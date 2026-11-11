"""
Paquete de Infraestructura transversal de Cantina Familiar.

Contiene utilidades desacopladas de transporte HTTP resiliente,
persistencia atómica de archivos CSV/JSON y registro centralizado de eventos.
"""

from src.infraestructura.almacenamiento_csv import (
    ResumenScraping,
    guardar_csv_atomico,
    guardar_json_atomico,
)
from src.infraestructura.cliente_http import (
    HEADERS_BOT,
    HEADERS_DEFAULT,
    HEADERS_SSR_NEXTJS,
    INDICADORES_DESAFIO_WAF,
    USER_AGENT_BOT,
    USER_AGENT_CHROME,
    descargar_html_con_reintentos,
    descargar_json_con_reintentos,
    es_pagina_desafio_waf,
    extraer_retry_after,
    pausa_aleatoria,
    peticion_curl_cffi,
    peticion_http_con_reintentos,
    sanitizar_url_para_logs,
)
from src.infraestructura.registro_eventos import configurar_logging, get_logger

__all__ = [
    "HEADERS_BOT",
    "HEADERS_DEFAULT",
    "HEADERS_SSR_NEXTJS",
    "INDICADORES_DESAFIO_WAF",
    "ResumenScraping",
    "USER_AGENT_BOT",
    "USER_AGENT_CHROME",
    "configurar_logging",
    "descargar_html_con_reintentos",
    "descargar_json_con_reintentos",
    "es_pagina_desafio_waf",
    "extraer_retry_after",
    "get_logger",
    "guardar_csv_atomico",
    "guardar_json_atomico",
    "pausa_aleatoria",
    "peticion_curl_cffi",
    "peticion_http_con_reintentos",
    "sanitizar_url_para_logs",
]
