"""
Orquestador maestro para la adquisición automática integral de todas las tiendas:
1. Bodegas Alianza (API VTEX pública)
2. Chedraui (API VTEX)
3. Sam's Club (SSR __NEXT_DATA__)
4. Walmart (SSR __NEXT_DATA__)
5. Soriana (API SFCC)
6. Costco México (API REST OCC v2)
Seguido de la consolidación ETL (NOM-006, NOM-070, precios $/L, stock)
y la sincronización automática del dashboard interactivo.
"""

import argparse
import time

from src.actualizar_dashboard_completo import actualizar_todo
from src.generar_dashboard_v4 import generar_dashboard
from src.logger import get_logger
from src.scraper_catalogo_completo.cliente_vtex import main as scrapear_alianza_main
from src.scraper_multitienda.cli import main as scrapear_multitienda_main

logger = get_logger("orquestador_scraping")


def ejecutar_pipeline_scraping_completo(
    saltar_alianza: bool = False,
    saltar_multitienda: bool = False,
    saltar_consolidacion: bool = False,
) -> bool:
    """
    Ejecuta el ciclo de vida completo de adquisición y despliegue local de datos.
    """
    inicio = time.time()
    logger.info("=" * 70)
    logger.info("🚀 INICIANDO EXTRACCIÓN AUTOMÁTICA COMPLETA DE TODAS LAS TIENDAS")
    logger.info("=" * 70)

    # 1. Bodegas Alianza
    if not saltar_alianza:
        logger.info("\n📦 [1/4] Extrayendo Bodegas Alianza (API VTEX oficial)...")
        try:
            scrapear_alianza_main()
        except (OSError, TimeoutError, ConnectionError, ValueError, RuntimeError, KeyError) as e:
            logger.error(f"Error extrayendo Bodegas Alianza: {e}")

    # 2. Multitienda (Chedraui, Sam's Club, Walmart, Soriana, Costco)
    if not saltar_multitienda:
        logger.info("\n🏪 [2/4] Extrayendo cadenas comerciales multitienda...")
        try:
            scrapear_multitienda_main()
        except (OSError, TimeoutError, ConnectionError, ValueError, RuntimeError, KeyError) as e:
            logger.error(f"Error extrayendo multitienda: {e}")

    # 3. Consolidación ETL y auditoría NOM
    if not saltar_consolidacion:
        logger.info("\n🔄 [3/4] Consolidando datasets, aplicando NOM-006/070 y arbitraje cross-tienda...")
        actualizar_todo()

        # 4. Generación reactiva del dashboard v6.0
        logger.info("\n🎨 [4/4] Ensamblando y sincronizando index.html...")
        generar_dashboard()

    duracion = time.time() - inicio
    logger.info("=" * 70)
    logger.info(f"✅ PIPELINE DE SCRAPING FINALIZADO EN {duracion:.1f} SEGUNDOS")
    logger.info("=" * 70)
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Orquestador automático completo: Scraping de 6 tiendas + Consolidación ETL + Dashboard."
    )
    parser.add_argument(
        "--saltar-alianza",
        action="store_true",
        help="Omitir extracción de Bodegas Alianza.",
    )
    parser.add_argument(
        "--saltar-multitienda",
        action="store_true",
        help="Omitir extracción multitienda (Chedraui, Sam's, Walmart, Soriana, Costco).",
    )
    parser.add_argument(
        "--solo-scraping",
        action="store_true",
        help="Solo extraer datos sin ejecutar consolidación ni regenerar dashboard.",
    )
    args = parser.parse_args()

    ejecutar_pipeline_scraping_completo(
        saltar_alianza=args.saltar_alianza,
        saltar_multitienda=args.saltar_multitienda,
        saltar_consolidacion=args.solo_scraping,
    )


if __name__ == "__main__":
    main()
