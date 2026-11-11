"""
Cliente paginado VTEX y orquestador de extracción exhaustiva para Bodegas Alianza.
"""

import json
import urllib.error
import urllib.parse
from datetime import datetime

import pandas as pd

from src.adquisicion.clasificador_alianza import evaluar_item_alianza
from src.infraestructura.almacenamiento_csv import ResumenScraping, guardar_csv_atomico
from src.infraestructura.cliente_http import HEADERS_BOT, descargar_json_con_reintentos, pausa_aleatoria
from src.infraestructura.registro_eventos import get_logger

logger = get_logger("alianza_paginado")


def consultar_endpoint_paginado(
    termino: str, max_paginas: int = 5, resumen: ResumenScraping | None = None
) -> list[dict]:
    """Consulta la API de VTEX con paginación de 50 en 50 elementos y reintentos automáticos."""
    items = []
    for pag in range(max_paginas):
        inicio = pag * 50
        fin = inicio + 49
        url = f"https://www.bodegasalianza.com/api/catalog_system/pub/products/search/{urllib.parse.quote(termino)}?_from={inicio}&_to={fin}"
        try:
            data = descargar_json_con_reintentos(url, headers=HEADERS_BOT)
            if not data:
                break
            items.extend(data)
            if len(data) < 50:
                break
        except (
            urllib.error.URLError,
            urllib.error.HTTPError,
            TimeoutError,
            ConnectionError,
            json.JSONDecodeError,
            OSError,
        ) as e:
            if resumen:
                resumen.registrar_error_red(url, e)
            logger.warning(f"Fin o error en '{termino}' pag {pag}: {e}")
            break
        pausa_aleatoria(0.25, 0.6)
    return items


def procesar_catalogo_completo(
    terminos_busqueda: list[str] | None = None,
    max_paginas: int = 5,
) -> list[dict]:
    """Descarga y clasifica todos los productos sin sesgo de marca."""
    if terminos_busqueda is None:
        terminos_busqueda = [
            "tequila",
            "tequila cristalino",
            "tequila anejo",
            "mezcal",
            "mezcal joven",
            "mezcal espadin",
            "mezcal reposado",
            "mezcal anejo",
            "mezcal tobala",
            "mezcal cupreata",
            "whisky",
            "whisky blended",
            "jack daniels",
            "jack daniels honey",
            "jack daniels apple",
            "vino tinto",
            "vino california",
            "vino reservado",
        ]

    productos_crudos = []
    ids_vistos = set()

    logger.info("Iniciando extracción exhaustiva del catálogo de Bodegas Alianza...")
    for t in terminos_busqueda:
        logger.info(f"  -> Consultando: '{t}'...")
        lote = consultar_endpoint_paginado(t, max_paginas=max_paginas)
        nuevos = 0
        for p in lote:
            pid = p.get("productId") or p.get("linkText")
            if pid and pid not in ids_vistos:
                ids_vistos.add(pid)
                productos_crudos.append(p)
                nuevos += 1
        logger.info(f"     Nuevos encontrados: {nuevos} (Total acumulado: {len(productos_crudos)})")

    logger.info("Filtrando y clasificando por tipos estrictos solicitados...")
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M")
    productos_filtrados = []
    resumen = ResumenScraping("Bodegas Alianza")

    for p in productos_crudos:
        item_norm = evaluar_item_alianza(p, fecha_actual, resumen)
        if item_norm:
            productos_filtrados.append(item_norm)

    resumen.imprimir_resumen()
    return productos_filtrados


def main():
    productos = procesar_catalogo_completo()
    df = pd.DataFrame(productos)
    salida = "data/scraped_alianza_completo.csv"
    guardar_csv_atomico(df, salida)
    logger.info(f"Se guardaron {len(df)} productos validados en: {salida}")
    logger.info("Desglose por categoría:")
    for cat, cnt in df["categoria"].value_counts().items():
        logger.info(f"  - {cat}: {cnt}")
