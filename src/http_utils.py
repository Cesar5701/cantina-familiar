"""
Módulo de Utilidades HTTP con Reintentos y Backoff Exponencial (H20).

Proporciona funciones seguras y resilientes para consultas HTTP a APIs y portales web,
manejando automáticamente interrupciones de red, rate limits (HTTP 429) y errores temporales de servidor (HTTP 5xx).
"""

import sys
import time
import json
import random
import urllib.request
import urllib.error
import socket
from typing import Any, Dict, Optional

HEADERS_DEFAULT = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json,*/*;q=0.8",
    "Accept-Language": "es-MX,es;q=0.9,en;q=0.8"
}

CODIGOS_REINTENTO = {429, 500, 502, 503, 504}


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
    lanzar_error: bool = True
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
    encabezados = HEADERS_DEFAULT.copy()
    if headers:
        encabezados.update(headers)

    ultimo_error = None

    for intento in range(max_intentos):
        try:
            req = urllib.request.Request(url, data=data, headers=encabezados, method=metodo)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                contenido = resp.read().decode("utf-8", errors="ignore")
                return contenido

        except urllib.error.HTTPError as e:
            ultimo_error = e
            # Solo reintentar en errores transitorios (rate limits y fallos de servidor)
            if e.code not in CODIGOS_REINTENTO:
                if lanzar_error:
                    raise
                return None

        except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError) as e:
            ultimo_error = e

        except Exception as e:
            ultimo_error = e
            if lanzar_error:
                raise
            return None

        # Si aún quedan reintentos, calcular el backoff exponencial
        if intento < max_intentos - 1:
            delay = delay_inicial * (factor_backoff ** intento)
            if jitter:
                delay += random.uniform(0.1, delay * 0.3)
            time.sleep(delay)

    if lanzar_error and ultimo_error:
        raise ultimo_error

    return None


def descargar_json_con_reintentos(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    max_intentos: int = 3,
    delay_inicial: float = 1.0,
    timeout: float = 15.0
) -> Any:
    """Descarga y parsea una respuesta JSON con reintentos automáticos."""
    texto = peticion_http_con_reintentos(
        url=url,
        headers=headers,
        max_intentos=max_intentos,
        delay_inicial=delay_inicial,
        timeout=timeout,
        lanzar_error=True
    )
    if texto is None:
        return None
    return json.loads(texto)


def descargar_html_con_reintentos(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    max_intentos: int = 3,
    delay_inicial: float = 1.0,
    timeout: float = 15.0
) -> str | None:
    """Descarga el contenido HTML de una página con reintentos automáticos."""
    return peticion_http_con_reintentos(
        url=url,
        headers=headers,
        max_intentos=max_intentos,
        delay_inicial=delay_inicial,
        timeout=timeout,
        lanzar_error=False
    )
