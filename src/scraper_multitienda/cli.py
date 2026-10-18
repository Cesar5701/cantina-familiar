"""
Orquestador CLI para extracción multitienda bajo demanda.
"""

import os

import pandas as pd

import src.scraper_multitienda as _pkg
from src.io_utils import guardar_csv_atomico
from src.logger import get_logger

logger = get_logger("scraper_multitienda")


def main():
    os.makedirs("data", exist_ok=True)

    terminos_sams = ["tequila", "tequila cristalino", "tequila anejo", "mezcal", "whisky", "jack daniels", "vino tinto"]
    terminos_walmart = [
        "tequila cristalino",
        "tequila anejo",
        "tequila 1800",
        "tequila herradura",
        "tequila don julio",
        "tequila dobel",
        "mezcal 400 conejos",
        "mezcal amaras",
        "mezcal montelobos",
        "mezcal reposado",
        "mezcal anejo",
        "whisky johnnie walker",
        "whisky black & white",
        "whisky ballantines",
        "whisky william lawsons",
        "whisky chivas",
        "whisky buchanans",
        "jack daniels honey",
        "vino tinto california",
        "carlo rossi",
        "vino tinto reservado",
        "vino tinto cuatro soles",
    ]

    # 1. Chedraui
    prods_chedraui = _pkg.scrapear_chedraui()
    if prods_chedraui:
        guardar_csv_atomico(pd.DataFrame(prods_chedraui), "data/scraped_chedraui.csv")

    # 2. Sam's Club
    prods_sams = _pkg.scrapear_nextjs_walmart_platform("Sam's Club", "www.sams.com.mx", terminos_sams)
    if prods_sams:
        guardar_csv_atomico(pd.DataFrame(prods_sams), "data/scraped_sams.csv")

    # 3. Walmart
    prods_walmart = _pkg.scrapear_nextjs_walmart_platform("Walmart", "www.walmart.com.mx", terminos_walmart)
    if prods_walmart:
        guardar_csv_atomico(pd.DataFrame(prods_walmart), "data/scraped_walmart.csv")

    # 4. Soriana
    prods_soriana = _pkg.scrapear_soriana()
    if prods_soriana:
        guardar_csv_atomico(pd.DataFrame(prods_soriana), "data/scraped_soriana.csv")

    logger.info("=" * 70)
    logger.info("RESUMEN DE EXTRACCIÓN MULTITIENDA")
    logger.info("=" * 70)
    logger.info(f"  - Chedraui:   {len(prods_chedraui)} productos")
    logger.info(f"  - Sam's Club: {len(prods_sams)} productos")
    logger.info(f"  - Walmart:    {len(prods_walmart)} productos")
    logger.info(f"  - Soriana:    {len(prods_soriana)} productos")
