"""
Scraper para Soriana mediante catálogo HTML de Salesforce Commerce Cloud (.product-tile).
"""

import time
import urllib.error
import urllib.parse
from datetime import datetime

from bs4 import BeautifulSoup

import src.scraper_multitienda as _pkg
from src.clasificacion import limpiar_precio
from src.http_utils import HEADERS_DEFAULT
from src.io_utils import ResumenScraping
from src.logger import get_logger
from src.scraper_multitienda.normalizador import evaluar_y_normalizar_producto

logger = get_logger("scraper_multitienda")


def scrapear_soriana(terminos: list[str] | None = None) -> list[dict]:
    logger.info("=" * 60)
    logger.info("SCRAPEANDO SORIANA (soriana.com SFCC Catalog)")
    logger.info("=" * 60)
    if terminos is None:
        terminos = [
            "tequila cristalino",
            "tequila anejo",
            "tequila 1800",
            "tequila herradura",
            "tequila don julio",
            "tequila maestro dobel",
            "tequila centenario",
            "mezcal 400 conejos",
            "mezcal amaras",
            "mezcal montelobos",
            "mezcal reposado",
            "mezcal anejo",
            "whisky johnnie walker",
            "whisky buchanans",
            "whisky chivas",
            "whisky black & white",
            "whisky ballantines",
            "whisky william lawsons",
            "jack daniels honey",
            "vino tinto california",
            "vino tinto carlo rossi",
            "vino tinto reservado",
            "vino tinto cuatro soles",
            "vino tinto lambrusco",
        ]
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M")
    pids_vistos = set()
    resultados = []
    resumen = ResumenScraping("Soriana")

    for t in terminos:
        url = f"https://www.soriana.com/buscar?q={urllib.parse.quote(t)}"
        try:
            html = _pkg.descargar_html_con_reintentos(url, headers=HEADERS_DEFAULT, timeout=15)
            if not html:
                resumen.registrar_error_red(url, ConnectionError("Respuesta vacía"))
                continue
            soup = BeautifulSoup(html, "html.parser")
            tiles = soup.select(".product-tile")
            nuevos_q = 0
            for tile in tiles:
                link_el = tile.select_one("a.product-tile--link")
                if not link_el:
                    resumen.registrar_descarte("sin link")
                    continue
                nombre = link_el.get_text(strip=True)
                href = link_el.get("href", "")
                pid_btn = tile.select_one("[data-pid]")
                pid = pid_btn.get("data-pid") if pid_btn else href
                if not pid or pid in pids_vistos:
                    continue
                pids_vistos.add(pid)

                full_url = f"https://www.soriana.com{href}" if href.startswith("/") else (href or url)

                # Precio de lista
                inp_list = tile.select_one('input[name="clevertap-list-price"]')
                p_list = limpiar_precio(inp_list.get("value")) if inp_list else None

                # Precio de venta / promo
                sales_el = tile.select_one(".sales .cart-price") or tile.select_one(".price-plp")
                p_sale = limpiar_precio(sales_el.get_text(strip=True)) if sales_el else p_list

                p_promo = p_sale or p_list
                p_reg = p_list if (p_list and p_promo and p_list > p_promo) else p_promo

                # Promociones / Badges
                badges = [b.get("title", "").strip() for b in tile.select(".product-badge") if b.get("title")]
                badges_str = " | ".join(dict.fromkeys(b for b in badges if b))
                if p_reg and p_promo and p_reg > p_promo:
                    cond = f"Oferta en línea ({badges_str})" if badges_str else "Oferta en línea Soriana"
                elif badges_str:
                    cond = f"Precio regular ({badges_str})"
                else:
                    cond = "Precio regular Soriana"

                item_norm = evaluar_y_normalizar_producto(
                    tienda="Soriana",
                    nombre=nombre,
                    marca="",
                    precio_regular=p_reg,
                    precio_promo=p_promo,
                    disponible="disponible",
                    url=full_url,
                    condicion=cond,
                    fuente="Portal oficial soriana.com",
                    fecha_actual=fecha_actual,
                )
                if item_norm:
                    resultados.append(item_norm)
                    resumen.registrar_exito()
                    nuevos_q += 1
                else:
                    resumen.registrar_descarte("criterio exclusión o volumen")
            logger.info(f"  -> '{t}': +{nuevos_q} productos (Acumulado Soriana: {len(resultados)})")
            time.sleep(0.5)
        except (
            urllib.error.URLError,
            urllib.error.HTTPError,
            TimeoutError,
            ConnectionError,
            OSError,
            KeyError,
            ValueError,
        ) as e:
            resumen.registrar_error_red(url, e)
            logger.warning(f"[Soriana '{t}']: {e}")

    resumen.imprimir_resumen()
    logger.info(f"Total Soriana: {len(resultados)} productos validados.")
    return resultados
