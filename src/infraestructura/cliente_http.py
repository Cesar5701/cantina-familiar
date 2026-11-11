"""
Módulo de Utilidades HTTP con Reintentos y Backoff Exponencial (H20).

Proporciona funciones seguras y resilientes para consultas HTTP a APIs y portales web,
manejando automáticamente interrupciones de red, rate limits (HTTP 429) y errores temporales de servidor (HTTP 5xx).
"""

import email.utils
import http.client
import json
import random
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Any, Dict, Optional

from src.infraestructura.registro_eventos import get_logger

try:
    from curl_cffi import requests as curl_requests
    from curl_cffi.requests.exceptions import RequestException as CurlRequestException
except (ImportError, OSError):
    curl_requests = None
    CurlRequestException = Exception  # type: ignore[misc, assignment]

logger = get_logger("cliente_http")

USER_AGENT_CHROME = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
USER_AGENT_BOT = (
    "Mozilla/5.0 (compatible; CantinaFamiliarBot/2.0; +https://github.com/cantina-familiar; personal/educativo)"
)

HEADERS_DEFAULT = {
    "User-Agent": USER_AGENT_CHROME,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json,*/*;q=0.8",
    "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
}

HEADERS_BOT = {
    "User-Agent": USER_AGENT_BOT,
    "Accept": "application/json",
}

HEADERS_SSR_NEXTJS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "es-MX,es;q=0.9,en-US;q=0.8,en;q=0.7",
    "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}

CODIGOS_REINTENTO = {429, 500, 502, 503, 504}

INDICADORES_DESAFIO_WAF: tuple[str, ...] = (
    "verify your identity",
    "verifica tu identidad",
    "px-captcha",
    "perimeterx",
    "mantén presionado",
    "press and hold",
    "just a moment",
    "challenge-running",
    "cf-challenge-running",
    "verificación de seguridad",
    "security check",
    "captcha",
    "unusual traffic",
    "bloqueo temporal",
    "robot",
    "attention required",
    "human verification",
)


def es_pagina_desafio_waf(html: str | None, max_bytes: int = 15000) -> bool:
    """Detecta si la respuesta HTML corresponde a un reto WAF/PerimeterX/Cloudflare en lugar de contenido legítimo."""
    if not html:
        return True
    if "__NEXT_DATA__" in html:
        return False
    muestra = html[:max_bytes].lower()
    return any(ind in muestra for ind in INDICADORES_DESAFIO_WAF)


def _preparar_encabezados(headers: Optional[Dict[str, str]]) -> Dict[str, str]:
    """Combina los encabezados del usuario con los defaults, respetando el UA de WhatsApp."""
    if headers is not None and "WhatsApp" in headers.get("User-Agent", ""):
        return headers.copy()
    encabezados = HEADERS_DEFAULT.copy()
    if headers:
        encabezados.update(headers)
    return encabezados


def sanitizar_url_para_logs(url: str) -> str:
    """Oculta tokens, api keys y secretos en parámetros URL para evitar fugas en logs de CI/CD."""
    if not url or "?" not in url:
        return url
    try:
        parsed = urllib.parse.urlsplit(url)
        query_dict = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
        campos_sensibles = {
            "token",
            "key",
            "api_key",
            "apikey",
            "secret",
            "password",
            "auth",
            "access_token",
            "signature",
        }
        sanitized_pairs = []
        for k, v_list in query_dict.items():
            if k.lower() in campos_sensibles:
                sanitized_pairs.append(f"{k}=***")
            else:
                for v in v_list:
                    sanitized_pairs.append(f"{k}={v}")
        new_query = "&".join(sanitized_pairs)
        return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, new_query, parsed.fragment))
    except (ValueError, TypeError, AttributeError):
        return url


def pausa_aleatoria(min_seg: float = 0.4, max_seg: float = 1.0) -> None:
    """Pausa con jitter aleatorio para mitigar la detección por cadencia fija en scrapers."""
    if max_seg < min_seg:
        max_seg = min_seg
    time.sleep(random.uniform(min_seg, max_seg))


def extraer_retry_after(cabeceras_o_error: Any, max_segundos: float = 60.0) -> Optional[float]:
    """Extrae y valida la cabecera Retry-After de un error o respuesta HTTP."""
    if cabeceras_o_error is None:
        return None
    headers = getattr(cabeceras_o_error, "headers", None)
    if headers is None and isinstance(cabeceras_o_error, dict):
        headers = cabeceras_o_error
    if headers is None:
        return None

    raw_val = None
    if hasattr(headers, "get"):
        raw_val = headers.get("Retry-After") or headers.get("retry-after")
    if not raw_val:
        return None

    try:
        val_seg = float(raw_val)
        return min(max(0.5, val_seg), max_segundos)
    except (ValueError, TypeError):
        try:
            parsed_time = email.utils.parsedate_to_datetime(str(raw_val))
            diff = (parsed_time - datetime.now(parsed_time.tzinfo)).total_seconds()
            if 0 < diff <= max_segundos:
                return diff
        except (ValueError, TypeError, AttributeError, IndexError):
            pass
    return None


def _calcular_espera(
    intento: int,
    delay_inicial: float,
    factor_backoff: float,
    jitter: bool,
    retry_after: Optional[float] = None,
) -> float:
    """Calcula el backoff exponencial del intento con jitter multiplicativo real o respeta Retry-After."""
    if retry_after is not None and retry_after > 0:
        return retry_after + (random.uniform(0.1, 0.5) if jitter else 0.0)

    delay_base = delay_inicial * (factor_backoff**intento)
    if jitter:
        # Full jitter multiplicativo: 70% a 130% del retraso base
        return delay_base * random.uniform(0.7, 1.3)
    return delay_base


def _intentar_peticion(
    url: str,
    data: Optional[bytes],
    headers: Dict[str, str],
    metodo: str,
    timeout: float,
) -> tuple[Optional[str], Optional[BaseException], bool, Optional[float]]:
    """
    Ejecuta un intento HTTP y clasifica el resultado.

    Retorna (contenido, error, reintentar, retry_after):
    - Éxito: (texto, None, False, None)
    - Error transitorio: (None, excepción, True, retry_after)
    - Error definitivo: (None, excepción, False, None)
    """
    try:
        req = urllib.request.Request(url, data=data, headers=headers, method=metodo)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore"), None, False, None
    except urllib.error.HTTPError as e:
        retry_after = extraer_retry_after(e)
        return None, e, e.code in CODIGOS_REINTENTO, retry_after
    except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError, http.client.HTTPException) as e:
        return None, e, True, None
    except (OSError, UnicodeDecodeError) as e:
        return None, e, False, None


def peticion_http_con_reintentos(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    data: Optional[bytes] = None,
    metodo: str = "GET",
    max_intentos: int = 3,
    delay_inicial: float = 1.0,
    factor_backoff: float = 2.0,
    timeout: float = 15.0,
    jitter: bool = True,
    lanzar_error: bool = True,
) -> str | None:
    """
    Ejecuta una petición HTTP con política de reintentos exponenciales y jitter.

    Args:
        url: URL de destino.
        headers: Encabezados HTTP (usa HEADERS_DEFAULT si no se especifica).
        data: Cuerpo de datos en bytes (para POST/PUT).
        metodo: Método HTTP ('GET', 'POST', etc.).
        max_intentos: Número máximo de intentos antes de fallar.
        delay_inicial: Segundos a esperar tras el primer fallo.
        factor_backoff: Multiplicador del retraso en cada reintento subsiguiente.
        timeout: Tiempo de espera en segundos para la conexión y lectura.
        jitter: Si es True, añade variación aleatoria para mitigar el efecto de rebaño (thundering herd).
        lanzar_error: Si es True, relanza la excepción si se agotan los reintentos. Si es False, retorna None.

    Returns:
        Cadena decodificada en UTF-8 con la respuesta del servidor, o None si falla y lanzar_error es False.
    """
    encabezados = _preparar_encabezados(headers)
    ultimo_error: Optional[BaseException] = None
    url_segura = sanitizar_url_para_logs(url)

    for intento in range(max_intentos):
        contenido, error, reintentar, retry_after = _intentar_peticion(url, data, encabezados, metodo, timeout)
        if contenido is not None:
            return contenido

        ultimo_error = error
        if not reintentar:
            if lanzar_error and error is not None:
                raise error
            logger.warning("Petición HTTP a %s falló definitivamente: %s", url_segura, error)
            return None

        # Si aún quedan reintentos, calcular el backoff exponencial
        if intento < max_intentos - 1:
            espera = _calcular_espera(intento, delay_inicial, factor_backoff, jitter, retry_after=retry_after)
            logger.debug("Reintentando petición a %s en %.2fs tras fallo transitorio (%s)", url_segura, espera, error)
            time.sleep(espera)

    if lanzar_error and ultimo_error:
        raise ultimo_error
    if ultimo_error:
        logger.warning("Petición HTTP a %s agotó los %s intentos: %s", url_segura, max_intentos, ultimo_error)

    return None


def descargar_json_con_reintentos(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    max_intentos: int = 3,
    delay_inicial: float = 1.0,
    timeout: float = 15.0,
) -> Any:
    """Descarga y parsea una respuesta JSON con reintentos automáticos."""
    texto = peticion_http_con_reintentos(
        url=url,
        headers=headers,
        max_intentos=max_intentos,
        delay_inicial=delay_inicial,
        timeout=timeout,
        lanzar_error=True,
    )
    if texto is None:
        return None
    return json.loads(texto)


def descargar_html_con_reintentos(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    max_intentos: int = 3,
    delay_inicial: float = 1.0,
    timeout: float = 15.0,
) -> str | None:
    """Descarga el contenido HTML de una página con reintentos automáticos."""
    return peticion_http_con_reintentos(
        url=url,
        headers=headers,
        max_intentos=max_intentos,
        delay_inicial=delay_inicial,
        timeout=timeout,
        lanzar_error=False,
    )


def peticion_curl_cffi(
    url: str,
    impersonate: str = "chrome124",
    headers: Optional[Dict[str, str]] = None,
    cookies: Optional[Dict[str, str]] = None,
    timeout: float = 15.0,
    lanzar_error: bool = False,
) -> str | None:
    """
    Ejecuta una petición HTTP utilizando curl_cffi para reproducir exactamente
    el handshake TLS/JA3/HTTP2 de un navegador real (ej. chrome124).
    Si curl_cffi no está disponible o falla, recurre de forma segura a peticion_http_con_reintentos.
    """
    url_segura = sanitizar_url_para_logs(url)
    if curl_requests is None:
        logger.debug("curl_cffi no está disponible; se usa urllib como fallback para %s", url_segura)
    else:
        try:
            hdrs = (HEADERS_SSR_NEXTJS if headers is None else headers).copy()
            resp = curl_requests.get(
                url,
                impersonate=impersonate,
                headers=hdrs,
                cookies=cookies,
                timeout=timeout,
            )
            if resp.status_code in {200, 304}:
                return resp.text

            logger.warning("curl_cffi recibió código HTTP %s al consultar %s", resp.status_code, url_segura)
            if resp.status_code in CODIGOS_REINTENTO:
                retry_after = extraer_retry_after(getattr(resp, "headers", {}))
                delay_ini = retry_after if retry_after else 1.0
                logger.info("Reintentando código transitorio HTTP %s con backoff adaptativo...", resp.status_code)
                return peticion_http_con_reintentos(
                    url=url,
                    headers=headers,
                    delay_inicial=delay_ini,
                    timeout=timeout,
                    lanzar_error=lanzar_error,
                )

            if resp.status_code >= 400:
                if lanzar_error:
                    resp.raise_for_status()
                return None

            return resp.text
        except (CurlRequestException, OSError, RuntimeError, TimeoutError, ConnectionError, ValueError) as exc:
            if lanzar_error:
                raise
            logger.warning("curl_cffi falló para %s (%s); se reintenta con urllib", url_segura, exc)
    return peticion_http_con_reintentos(url=url, headers=headers, timeout=timeout, lanzar_error=lanzar_error)
