"""
Scraper para Costco México mediante API REST nativa OCC v2 de SAP Commerce Cloud (/rest/v2/mexico/products/search).
"""

import json
import time
import urllib.error
import urllib.parse
from datetime import datetime

import src.scraper_multitienda as _pkg
from src.http_utils import HEADERS_DEFAULT
from src.io_utils import ResumenScraping
from src.logger import get_logger
from src.scraper_multitienda.normalizador import evaluar_y_normalizar_producto

logger = get_logger("scraper_multitienda")


def scrapear_costco(terminos: list[str] | None = None) -> list[dict]:
    logger.info("=" * 60)
    logger.info("SCRAPEANDO COSTCO MÉXICO (API OCC v2 costco.com.mx)")
    logger.info("=" * 60)
    if terminos is None:
        terminos = [
            "tequila",
            "tequila cristalino",
            "tequila anejo",
            "tequila reposado",
            "mezcal",
            "whisky",
            "scotch",
            "whiskey",
            "vino tinto",
            "vino",
        ]

    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M")
    ids_vistos = set()
    resultados = []
    resumen = ResumenScraping("Costco")

    for t in terminos:
        pagina = 0
        max_paginas = 3
        while pagina < max_paginas:
            q_enc = urllib.parse.quote(t)
            url = f"https://www.costco.com.mx/rest/v2/mexico/products/search?query={q_enc}&pageSize=100&currentPage={pagina}"
            try:
                data = _pkg.descargar_json_con_reintentos(url, headers=HEADERS_DEFAULT, timeout=15)
                if not data or not isinstance(data, dict):
                    break

                products = data.get("products", [])
                if not products:
                    break

                nuevos_q = 0
                for p in products:
                    code = str(p.get("code") or "").strip()
                    if not code or code in ids_vistos:
                        continue
                    ids_vistos.add(code)

                    # Si el precio está oculto tras login de socio o no existe
                    if p.get("hidePriceValue"):
                        resumen.registrar_descarte("precio oculto socio")
                        continue

                    price_info = p.get("price") or {}
                    p_promo = price_info.get("value")
                    if p_promo is None or p_promo <= 0:
                        resumen.registrar_descarte("sin precio")
                        continue

                    base_info = p.get("basePrice") or {}
                    p_base = base_info.get("value")
                    p_reg = p_base if (p_base and p_base > p_promo) else p_promo

                    nombre = (p.get("name") or "").strip()
                    stock_info = p.get("stock") or {}
                    disp_val = stock_info.get("stockLevelStatus")
                    stock_lvl = stock_info.get("stockLevel")
                    stock_unidades = int(stock_lvl) if stock_lvl is not None else None
                    disponible = "disponible" if disp_val == "inStock" else "agotado"

                    if disponible == "agotado":
                        resumen.registrar_descarte("agotado")
                        continue

                    coupon = p.get("couponDiscount") or {}
                    desc_val = coupon.get("discountValue")
                    if desc_val and desc_val > 0 and p_reg > p_promo:
                        cond = f"Oferta Costco (Ahorra ${desc_val:.2f})"
                    elif p_reg > p_promo:
                        ahorro = p_reg - p_promo
                        cond = f"Oferta Costco (Ahorra ${ahorro:.2f})"
                    else:
                        cond = "Precio socio Costco"

                    path_url = p.get("url") or ""
                    full_url = f"https://www.costco.com.mx{path_url}" if path_url.startswith("/") else path_url

                    item_norm = evaluar_y_normalizar_producto(
                        tienda="Costco",
                        nombre=nombre,
                        marca="",
                        precio_regular=p_reg,
                        precio_promo=p_promo,
                        disponible=disponible,
                        url=full_url,
                        condicion=cond,
                        fuente="API OCC v2 costco.com.mx",
                        fecha_actual=fecha_actual,
                        stock_unidades=stock_unidades,
                    )
                    if item_norm:
                        resultados.append(item_norm)
                        resumen.registrar_exito()
                        nuevos_q += 1
                    else:
                        resumen.registrar_descarte("filtro categoría o volumen")

                logger.info(f"  -> '{t}' (pág {pagina + 1}): +{nuevos_q} válidos (Acumulado Costco: {len(resultados)})")

                pag_info = data.get("pagination") or {}
                total_pags = pag_info.get("totalPages", 1)
                pagina += 1
                if pagina >= total_pags:
                    break

                time.sleep(0.4)

            except (
                urllib.error.URLError,
                urllib.error.HTTPError,
                TimeoutError,
                ConnectionError,
                json.JSONDecodeError,
                OSError,
                KeyError,
                ValueError,
            ) as e:
                resumen.registrar_error_red(url, e)
                logger.warning(f"[Costco '{t}' pág {pagina}]: {e}")
                break

    resumen.imprimir_resumen()
    return resultados
