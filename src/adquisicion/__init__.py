"""
Paquete de Adquisición y Extracción Multitienda de Cantina Familiar.

Unifica conectores de API REST/VTEX, SSR Next.js, SFCC, navegación CDP nativa
(nodriver) e hidratación asistida de SPAs bajo un contrato homogéneo.
"""

from src.adquisicion.alianza_paginado import (
    consultar_endpoint_paginado,
    procesar_catalogo_completo,
)
from src.adquisicion.alianza_vtex import consultar_api_alianza
from src.adquisicion.chedraui import scrapear_chedraui
from src.adquisicion.clasificador_alianza import evaluar_item_alianza
from src.adquisicion.controlador_waf import (
    INDICADORES_CHALLENGE,
    detectar_desafio,
    inicializar_driver,
    pausa_humana,
    verificar_y_esperar_desafio,
)
from src.adquisicion.costco import scrapear_costco
from src.adquisicion.despachador_cli import main
from src.adquisicion.hidratacion_spa import consultar_urls_secuenciales
from src.adquisicion.navegador_cdp import (
    BloqueoWAF,
    consultar_pdps_con_nodriver,
    es_url_tienda_valida,
    obtener_binario_chrome_disponible,
)
from src.adquisicion.normalizador_tiendas import evaluar_y_normalizar_producto
from src.adquisicion.selectores_dom import (
    construir_registro_producto,
    es_item_fuera_de_stock,
    extraer_de_json_embebido,
    extraer_precios_item,
    parsear_html_con_bs4,
)
from src.adquisicion.soriana import scrapear_soriana
from src.adquisicion.walmart import (
    PASILLOS_WALMART_LICORES,
    descubrir_productos_pasillos_walmart,
    es_respuesta_prerender_falsa,
    extraer_item_nextjs,
    scrapear_nextjs_walmart_platform,
)

__all__ = [
    "BloqueoWAF",
    "INDICADORES_CHALLENGE",
    "PASILLOS_WALMART_LICORES",
    "construir_registro_producto",
    "consultar_api_alianza",
    "consultar_endpoint_paginado",
    "consultar_pdps_con_nodriver",
    "consultar_urls_secuenciales",
    "descubrir_productos_pasillos_walmart",
    "detectar_desafio",
    "es_item_fuera_de_stock",
    "es_respuesta_prerender_falsa",
    "es_url_tienda_valida",
    "evaluar_item_alianza",
    "evaluar_y_normalizar_producto",
    "extraer_de_json_embebido",
    "extraer_item_nextjs",
    "extraer_precios_item",
    "inicializar_driver",
    "main",
    "obtener_binario_chrome_disponible",
    "parsear_html_con_bs4",
    "pausa_humana",
    "procesar_catalogo_completo",
    "scrapear_chedraui",
    "scrapear_costco",
    "scrapear_nextjs_walmart_platform",
    "scrapear_soriana",
    "verificar_y_esperar_desafio",
]
