"""
Paquete Scraper automatizado con nodriver (Chrome DevTools Protocol - CDP) y fallback WebDriver/Selenium (H34/Ruta C).
"""

from src.scraper_selenium.driver_y_waf import (
    INDICADORES_CHALLENGE,
    detectar_desafio,
    inicializar_driver,
    pausa_humana,
    verificar_y_esperar_desafio,
)
from src.scraper_selenium.navegador_cli import consultar_urls_secuenciales, main
from src.scraper_selenium.nodriver_cdp import (
    consultar_pdps_con_nodriver,
    obtener_binario_chrome_disponible,
)
from src.scraper_selenium.parsers_dom import (
    construir_registro_producto,
    es_item_fuera_de_stock,
    extraer_de_json_embebido,
    extraer_precios_item,
    parsear_html_con_bs4,
)

__all__ = [
    "INDICADORES_CHALLENGE",
    "construir_registro_producto",
    "consultar_pdps_con_nodriver",
    "consultar_urls_secuenciales",
    "detectar_desafio",
    "es_item_fuera_de_stock",
    "extraer_de_json_embebido",
    "extraer_precios_item",
    "inicializar_driver",
    "main",
    "obtener_binario_chrome_disponible",
    "parsear_html_con_bs4",
    "pausa_humana",
    "verificar_y_esperar_desafio",
]
