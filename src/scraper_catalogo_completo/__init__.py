"""
Paquete Scraper exhaustivo para Bodegas Alianza por tipo de bebida (sin sesgo de marca).
"""

from src.http_utils import HEADERS_BOT, descargar_json_con_reintentos
from src.scraper_catalogo_completo.clasificador_alianza import evaluar_item_alianza
from src.scraper_catalogo_completo.cliente_vtex import (
    consultar_endpoint_paginado,
    main,
    procesar_catalogo_completo,
)

__all__ = [
    "HEADERS_BOT",
    "consultar_endpoint_paginado",
    "descargar_json_con_reintentos",
    "evaluar_item_alianza",
    "main",
    "procesar_catalogo_completo",
]
