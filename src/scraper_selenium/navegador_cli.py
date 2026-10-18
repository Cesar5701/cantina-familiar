"""
Orquestador de navegación secuencial con hidratación de DOM y CLI de Selenium.
"""

import argparse
import time

import pandas as pd
from selenium.common.exceptions import (
    JavascriptException,
    TimeoutException,
    WebDriverException,
)

import src.scraper_selenium as _pkg
from src.io_utils import ResumenScraping, guardar_csv_atomico
from src.logger import get_logger

logger = get_logger("scraper_selenium")


def consultar_urls_secuenciales(
    urls: list[str], tienda: str = "Sam's Club", headless: bool = False, navegador: str = "chrome"
) -> list[dict]:
    """
    Navega por una lista de URLs de forma secuencial y controlada, aplicando
    pausas humanas y esperando activamente la resolución de desafíos e hidratación del DOM.
    """
    driver = None
    resultados = []
    resumen = ResumenScraping(tienda)
    try:
        logger.info(f"Iniciando {navegador.upper()} con User-Agent de escritorio...")
        driver = _pkg.inicializar_driver(headless=headless, navegador=navegador)

        for i, url in enumerate(urls, 1):
            logger.info(f"({i}/{len(urls)}) Navegando a: {url}")
            driver.get(url)

            # Pausa de inicio
            _pkg.pausa_humana(2.5, 3.5)

            # Verificar si hay CAPTCHA o desafío WAF (30 segundos)
            if not _pkg.verificar_y_esperar_desafio(driver, timeout_humano=30):
                logger.warning(f"Saltando {url} debido a desafío no resuelto.")
                resumen.registrar_descarte("desafío de seguridad no resuelto")
                continue

            # Desplazamiento suave para gatillar lazy loading
            try:
                driver.execute_script("window.scrollTo(0, 500);")
                time.sleep(1.0)
                driver.execute_script("window.scrollTo(0, 0);")
            except (WebDriverException, JavascriptException) as e:
                logger.debug(f"Error en scroll de hidratación: {e}")

            # ESPERA ACTIVA DE HIDRATACIÓN TRAS DESAFÍO
            logger.info("Esperando que la página hidrate los componentes dinámicos...")
            html = ""
            for _intento in range(10):
                time.sleep(2)
                # Re-comprobar si tras la navegación se reactivó el desafío
                sigue_desafio, _ = _pkg.detectar_desafio(driver)
                if sigue_desafio:
                    logger.warning("  ... re-apareció desafío, pausando...")
                    _pkg.verificar_y_esperar_desafio(driver, timeout_humano=20)

                html = driver.page_source
                tamano = len(html)
                logger.debug(f"  ... cargando DOM: {tamano} bytes")
                # Si el DOM supera los 35 KB, la página ya cargó scripts y componentes de catálogo
                if tamano > 35000:
                    break

            # Breve pausa final para renderizado de precios
            time.sleep(1.5)
            html = driver.page_source

            logger.info(f"Analizando {len(html)} bytes de DOM con BeautifulSoup...")
            prods = _pkg.parsear_html_con_bs4(html, url, tienda)
            logger.info(f"  -> {len(prods)} productos extraídos.")

            if len(prods) == 0:
                debug_file = "data/debug_page.html"
                with open(debug_file, "w", encoding="utf-8") as f:
                    f.write(html)
                logger.info(f"Se guardó una copia del HTML en '{debug_file}' ({len(html)} bytes) para inspección.")
                resumen.registrar_error_parseo(url, ValueError("Sin productos extraídos del DOM"))
            else:
                for _ in prods:
                    resumen.registrar_exito()

            resultados.extend(prods)

            # Pausa entre páginas
            if i < len(urls):
                _pkg.pausa_humana(3.0, 5.0)

    except (WebDriverException, TimeoutException, OSError) as e:
        logger.error(f"Error durante la ejecución del navegador: {e}")
        resumen.registrar_error_red("navegador", e)
    finally:
        if driver:
            driver.quit()
            logger.info("Navegador cerrado limpiamente.")

    resumen.imprimir_resumen()
    return resultados


def main():
    parser = argparse.ArgumentParser(
        description="Scraper con Selenium + BeautifulSoup (Chrome, pausas humanas y espera de hidratación)."
    )
    parser.add_argument("--urls", nargs="+", required=True, help="Lista de URLs a consultar.")
    parser.add_argument("--tienda", default="Sam's Club", help="Tienda que se está consultando.")
    parser.add_argument("--navegador", default="chrome", choices=["chrome", "firefox"], help="Navegador a utilizar.")
    parser.add_argument("--headless", action="store_true", help="Ejecutar sin ventana gráfica.")
    parser.add_argument("--salida", default="data/scraped_selenium.csv", help="Archivo CSV donde guardar la prueba.")
    args = parser.parse_args()

    prods = consultar_urls_secuenciales(args.urls, tienda=args.tienda, headless=args.headless, navegador=args.navegador)
    if prods:
        df = pd.DataFrame(prods)
        guardar_csv_atomico(df, args.salida)
        logger.info(f"Se guardaron {len(df)} registros sin deduplicar en: {args.salida}")
    else:
        logger.warning("No se extrajeron productos. Revisa 'data/debug_page.html' para ver el estado de la página.")
