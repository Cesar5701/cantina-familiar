"""
Scraper para Sam's Club y Walmart México mediante SSR __NEXT_DATA__ JSON.
"""

import json
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


def scrapear_nextjs_walmart_platform(tienda: str, base_domain: str, terminos: list[str]) -> list[dict]:
    logger.info("=" * 60)
    logger.info(f"SCRAPEANDO {tienda.upper()} ({base_domain} SSR __NEXT_DATA__)")
    logger.info("=" * 60)
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M")
    ids_vistos = set()
    resultados = []
    resumen = ResumenScraping(tienda)

    for t in terminos:
        url = f"https://{base_domain}/search?q={urllib.parse.quote(t)}"
        try:
            html = _pkg.descargar_html_con_reintentos(url, headers=HEADERS_DEFAULT, timeout=15)
            if not html:
                resumen.registrar_error_red(url, ConnectionError("Respuesta vacía"))
                continue
            soup = BeautifulSoup(html, "html.parser")
            script = soup.find("script", id="__NEXT_DATA__")
            if not script or not script.string:
                resumen.registrar_error_parseo(t, ValueError("Sin __NEXT_DATA__"))
                logger.warning(f"[{tienda}] Sin __NEXT_DATA__ en '{t}' ({len(html)} bytes)")
                time.sleep(1.0)
                continue

            data = json.loads(script.string)
            stacks = (
                data.get("props", {})
                .get("pageProps", {})
                .get("initialData", {})
                .get("searchResult", {})
                .get("itemStacks", [])
            )
            nuevos_q = 0
            for st in stacks:
                for it in st.get("items", []):
                    us_id = it.get("usItemId") or it.get("id") or it.get("canonicalUrl")
                    if not us_id or us_id in ids_vistos:
                        continue
                    ids_vistos.add(us_id)

                    nombre = (it.get("name") or it.get("title") or "").strip()
                    marca = (it.get("brand") or "").strip()
                    canon = it.get("canonicalUrl") or ""
                    full_url = f"https://{base_domain}{canon}" if canon.startswith("/") else (canon or url)

                    avail_obj = it.get("availabilityStatusV2") or {}
                    avail_val = avail_obj.get("value", "IN_STOCK") if isinstance(avail_obj, dict) else "IN_STOCK"
                    if avail_val == "OUT_OF_STOCK":
                        resumen.registrar_descarte("agotado")
                        continue

                    p_info = it.get("priceInfo") or {}
                    p_promo = limpiar_precio(it.get("price")) or limpiar_precio(p_info.get("linePrice"))
                    p_was = limpiar_precio(p_info.get("wasPrice")) or limpiar_precio(p_info.get("itemPrice"))
                    p_reg = p_was if (p_was and p_promo and p_was > p_promo) else p_promo

                    savings = p_info.get("savings") or ""
                    if p_reg and p_promo and p_reg > p_promo:
                        cond = f"Rebaja en línea ({savings})" if savings else f"Oferta {tienda}"
                    else:
                        cond = f"Precio socio {tienda}" if "Sam" in tienda else f"Precio regular {tienda}"

                    item_norm = evaluar_y_normalizar_producto(
                        tienda=tienda,
                        nombre=nombre,
                        marca=marca,
                        precio_regular=p_reg,
                        precio_promo=p_promo,
                        disponible="disponible",
                        url=full_url,
                        condicion=cond,
                        fuente=f"Portal oficial {base_domain}",
                        fecha_actual=fecha_actual,
                    )
                    if item_norm:
                        resultados.append(item_norm)
                        resumen.registrar_exito()
                        nuevos_q += 1
                    else:
                        resumen.registrar_descarte("filtro categoría o volumen")
            logger.info(f"  -> '{t}': +{nuevos_q} productos (Acumulado {tienda}: {len(resultados)})")
            time.sleep(0.8)
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
            logger.warning(f"[{tienda} '{t}']: {e}")
            time.sleep(1.0)

    resumen.imprimir_resumen()
    return resultados
