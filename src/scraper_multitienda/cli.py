"""
Orquestador CLI para extracción multitienda bajo demanda.
"""

import argparse
import os
import sys

import pandas as pd

from src.io_archivos import guardar_csv_atomico
from src.logger import get_logger
from src.scraper_multitienda.chedraui import scrapear_chedraui
from src.scraper_multitienda.costco import scrapear_costco
from src.scraper_multitienda.soriana import scrapear_soriana
from src.scraper_multitienda.walmart_sams import scrapear_nextjs_walmart_platform

logger = get_logger("scraper_multitienda")


def main(
    tiendas: list[str] | None = None,
    usar_fallback_selenium: bool | None = None,
    forzar_selenium: bool = False,
    headless_selenium: bool = False,
    walmart_cdp: bool = False,
    args: list[str] | None = None,
):
    if args is not None or (len(sys.argv) > 1 and tiendas is None):
        parser = argparse.ArgumentParser(description="Orquestador CLI para extracción multitienda.")
        parser.add_argument(
            "--tiendas",
            nargs="+",
            default=["todas"],
            help="Tiendas a scrapear: chedraui, sams, walmart, soriana, costco, o 'todas'.",
        )
        parser.add_argument("--forzar-selenium", action="store_true", help="Forzar scraping con navegador.")
        parser.add_argument("--headless", action="store_true", help="Ejecutar navegador en modo headless.")
        parser.add_argument("--walmart-cdp", action="store_true", help="Usar nodriver CDP para Walmart.")
        parser.add_argument("--sin-fallback-selenium", action="store_true", help="Desactivar fallback de Selenium.")
        parsed_args = parser.parse_args(args)
        tiendas = parsed_args.tiendas
        forzar_selenium = parsed_args.forzar_selenium or forzar_selenium
        headless_selenium = parsed_args.headless or headless_selenium
        walmart_cdp = parsed_args.walmart_cdp or walmart_cdp
        if parsed_args.sin_fallback_selenium:
            usar_fallback_selenium = False

    tiendas_norm = {t.strip().lower() for t in (tiendas or ["todas"])}
    scrapear_todas = "todas" in tiendas_norm or "all" in tiendas_norm

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

    totales = {}

    # 1. Chedraui
    if scrapear_todas or "chedraui" in tiendas_norm:
        prods_chedraui = scrapear_chedraui()
        if prods_chedraui:
            guardar_csv_atomico(pd.DataFrame(prods_chedraui), "data/scraped_chedraui.csv")
        totales["Chedraui"] = len(prods_chedraui)

    # 2. Sam's Club
    if scrapear_todas or "sams" in tiendas_norm or "sam" in tiendas_norm or "sam's club" in tiendas_norm:
        prods_sams = scrapear_nextjs_walmart_platform(
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
        totales["Sam's Club"] = len(prods_sams)

    # 3. Walmart (Ruta C directa con nodriver CDP si forzar_selenium o walmart_cdp está activo)
    if scrapear_todas or "walmart" in tiendas_norm:
        forzar_walmart = forzar_selenium or walmart_cdp
        prods_walmart = scrapear_nextjs_walmart_platform(
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
        totales["Walmart"] = len(prods_walmart)

    # 4. Soriana
    if scrapear_todas or "soriana" in tiendas_norm:
        prods_soriana = scrapear_soriana()
        if prods_soriana:
            guardar_csv_atomico(pd.DataFrame(prods_soriana), "data/scraped_soriana.csv")
        totales["Soriana"] = len(prods_soriana)

    # 5. Costco
    if scrapear_todas or "costco" in tiendas_norm:
        prods_costco = scrapear_costco()
        if prods_costco:
            guardar_csv_atomico(pd.DataFrame(prods_costco), "data/scraped_costco.csv")
        totales["Costco"] = len(prods_costco)

    logger.info("=" * 70)
    logger.info("RESUMEN DE EXTRACCIÓN MULTITIENDA")
    logger.info("=" * 70)
    for tienda_nom, cnt in totales.items():
        logger.info(f"  - {tienda_nom}: {cnt} productos")

    return totales


if __name__ == "__main__":
    main()
