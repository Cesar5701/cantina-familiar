"""
Orquestador CLI para extracción multitienda bajo demanda.
"""

import os

import pandas as pd

import src.scraper_multitienda as _pkg
from src.io_utils import guardar_csv_atomico
from src.logger import get_logger

logger = get_logger("scraper_multitienda")


def main(
    usar_fallback_selenium: bool | None = None,
    forzar_selenium: bool = False,
    headless_selenium: bool = False,
    walmart_cdp: bool = False,
):
    os.makedirs("data", exist_ok=True)

    terminos_sams = [
        "tequila",
        "tequila cristalino",
        "mezcal",
        "whisky",
        "vino tinto",
    ]
    terminos_walmart = [
        "tequila",
        "tequila cristalino",
        "mezcal",
        "whisky",
        "jack daniels",
        "vino tinto",
    ]

    # 1. Chedraui
    prods_chedraui = _pkg.scrapear_chedraui()
    if prods_chedraui:
        guardar_csv_atomico(pd.DataFrame(prods_chedraui), "data/scraped_chedraui.csv")

    # 2. Sam's Club
    prods_sams = _pkg.scrapear_nextjs_walmart_platform(
        "Sam's Club",
        "www.sams.com.mx",
        terminos_sams,
        ruta_respaldo="data/scraped_sams.csv",
        usar_fallback_selenium=usar_fallback_selenium,
        forzar_selenium=forzar_selenium,
        headless_selenium=headless_selenium,
    )
    if prods_sams:
        guardar_csv_atomico(pd.DataFrame(prods_sams), "data/scraped_sams.csv")

    # 3. Walmart (Ruta C directa con nodriver CDP si forzar_selenium o walmart_cdp está activo)
    forzar_walmart = forzar_selenium or walmart_cdp
    prods_walmart = _pkg.scrapear_nextjs_walmart_platform(
        "Walmart",
        "www.walmart.com.mx",
        terminos_walmart,
        ruta_respaldo="data/scraped_walmart.csv",
        usar_fallback_selenium=usar_fallback_selenium,
        forzar_selenium=forzar_walmart,
        headless_selenium=headless_selenium,
    )
    if prods_walmart:
        guardar_csv_atomico(pd.DataFrame(prods_walmart), "data/scraped_walmart.csv")

    # 4. Soriana
    prods_soriana = _pkg.scrapear_soriana()
    if prods_soriana:
        guardar_csv_atomico(pd.DataFrame(prods_soriana), "data/scraped_soriana.csv")

    # 5. Costco
    prods_costco = _pkg.scrapear_costco()
    if prods_costco:
        guardar_csv_atomico(pd.DataFrame(prods_costco), "data/scraped_costco.csv")

    logger.info("=" * 70)
    logger.info("RESUMEN DE EXTRACCIÓN MULTITIENDA")
    logger.info("=" * 70)
    logger.info(f"  - Chedraui:   {len(prods_chedraui)} productos")
    logger.info(f"  - Sam's Club: {len(prods_sams)} productos")
    logger.info(f"  - Walmart:    {len(prods_walmart)} productos")
    logger.info(f"  - Soriana:    {len(prods_soriana)} productos")
    logger.info(f"  - Costco:     {len(prods_costco)} productos")
