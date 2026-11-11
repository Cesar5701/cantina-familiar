"""
Paquete Scraper exhaustivo para Bodegas Alianza por tipo de bebida (sin sesgo de marca).
"""

from src.scraper_catalogo_completo.clasificador_alianza import evaluar_item_alianza
from src.scraper_catalogo_completo.cliente_vtex import (
    consultar_endpoint_paginado,
    main,
    procesar_catalogo_completo,
)

__all__ = [
    "consultar_endpoint_paginado",
    "evaluar_item_alianza",
    "main",
    "procesar_catalogo_completo",
]
