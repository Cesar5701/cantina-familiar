"""
Paquete Scraper Multitienda (Sam's Club, Walmart, Chedraui, Soriana).

Extrae precios verificados en tiempo real de:
1. Sam's Club (sams.com.mx) -> SSR __NEXT_DATA__ JSON
2. Walmart (walmart.com.mx) -> SSR __NEXT_DATA__ JSON
3. Chedraui (chedraui.com.mx) -> API pública VTEX (/api/catalog_system/pub/products/search/)
4. Soriana (soriana.com) -> HTML Salesforce Commerce Cloud (.product-tile)
"""

from src.scraper_multitienda.chedraui import scrapear_chedraui
from src.scraper_multitienda.cli import main
from src.scraper_multitienda.costco import scrapear_costco
from src.scraper_multitienda.normalizador import evaluar_y_normalizar_producto
from src.scraper_multitienda.soriana import scrapear_soriana
from src.scraper_multitienda.walmart_sams import (
    PASILLOS_WALMART_LICORES,
    descubrir_productos_pasillos_walmart,
    scrapear_nextjs_walmart_platform,
)

__all__ = [
    "PASILLOS_WALMART_LICORES",
    "descubrir_productos_pasillos_walmart",
    "evaluar_y_normalizar_producto",
    "main",
    "scrapear_chedraui",
    "scrapear_costco",
    "scrapear_nextjs_walmart_platform",
    "scrapear_soriana",
]
