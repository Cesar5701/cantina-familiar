"""
Módulo de Utilidades HTTP con Reintentos y Backoff Exponencial (H20).

Proporciona funciones seguras y resilientes para consultas HTTP a APIs y portales web,
manejando automáticamente interrupciones de red, rate limits (HTTP 429) y errores temporales de servidor (HTTP 5xx).
"""

import http.client
import json
import random
import socket
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

from src.logger import get_logger

try:
    from curl_cffi import requests as curl_requests
except (ImportError, OSError):
    curl_requests = None

logger = get_logger("http_utils")

USER_AGENT_CHROME = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
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


def _calcular_espera(intento: int, delay_inicial: float, factor_backoff: float, jitter: bool) -> float:
    """Calcula el backoff exponencial del intento, con jitter opcional."""
    delay = delay_inicial * (factor_backoff**intento)
    if jitter:
        delay += random.uniform(0.1, delay * 0.3)
    return delay


def _intentar_peticion(
    url: str,
    data: Optional[bytes],
    headers: Dict[str, str],
    metodo: str,
    timeout: float,
) -> tuple[Optional[str], Optional[BaseException], bool]:
    """
    Ejecuta un intento HTTP y clasifica el resultado.

    Retorna (contenido, error, reintentar):
    - Éxito: (texto, None, False)
    - Error transitorio: (None, excepción, True)
    - Error definitivo: (None, excepción, False)
    """
    try:
        req = urllib.request.Request(url, data=data, headers=headers, method=metodo)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore"), None, False
    except urllib.error.HTTPError as e:
        return None, e, e.code in CODIGOS_REINTENTO
    except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError, http.client.HTTPException) as e:
        return None, e, True
    except (OSError, UnicodeDecodeError) as e:
        return None, e, False


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

    for intento in range(max_intentos):
        contenido, error, reintentar = _intentar_peticion(url, data, encabezados, metodo, timeout)
        if contenido is not None:
            return contenido

        ultimo_error = error
        if not reintentar:
            if lanzar_error and error is not None:
                raise error
            return None

        # Si aún quedan reintentos, calcular el backoff exponencial
        if intento < max_intentos - 1:
            time.sleep(_calcular_espera(intento, delay_inicial, factor_backoff, jitter))

    if lanzar_error and ultimo_error:
        raise ultimo_error

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
    if curl_requests is None:
        logger.debug("curl_cffi no está disponible; se usa urllib como fallback para %s", url)
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
            if lanzar_error and resp.status_code >= 400:
                resp.raise_for_status()
            return resp.text
        except (OSError, RuntimeError, TimeoutError, ConnectionError, ValueError) as exc:
            if lanzar_error:
                raise
            logger.warning("curl_cffi falló para %s (%s); se reintenta con urllib", url, exc)
    return peticion_http_con_reintentos(url=url, headers=headers, timeout=timeout, lanzar_error=lanzar_error)
