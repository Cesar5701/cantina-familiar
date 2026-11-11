"""
Scraper para Chedraui mediante API pública VTEX (/api/catalog_system/pub/products/search/).
"""

import json
import urllib.error
import urllib.parse
from datetime import datetime

from src.io_archivos import ResumenScraping
from src.logger import get_logger
from src.red_http import HEADERS_DEFAULT, descargar_json_con_reintentos, pausa_aleatoria
from src.scraper_multitienda.normalizador import evaluar_y_normalizar_producto

logger = get_logger("scraper_multitienda")


def scrapear_chedraui(terminos: list[str] | None = None) -> list[dict]:
    logger.info("=" * 60)
    logger.info("1. SCRAPEANDO CHEDRAUI (API VTEX chedraui.com.mx)")
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
            "tequila don ramon",
            "mezcal",
            "mezcal 400 conejos",
            "mezcal amaras",
            "mezcal montelobos",
            "whisky",
            "johnnie walker",
            "black & white",
            "ballantines",
            "william lawsons",
            "jack daniels",
            "jack daniels honey",
            "jack daniels apple",
            "vino tinto",
            "vino california",
            "carlo rossi",
            "concha y toro",
        ]
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M")
    ids_vistos = set()
    resultados = []
    resumen = ResumenScraping("Chedraui")

    for t in terminos:
        for pag in range(2):
            ini = pag * 50
            fin = ini + 49
            url = f"https://www.chedraui.com.mx/api/catalog_system/pub/products/search/{urllib.parse.quote(t)}?_from={ini}&_to={fin}"
            try:
                data = descargar_json_con_reintentos(url, headers=HEADERS_DEFAULT, timeout=12)
                if not data:
                    break
                for p in data:
                    pid = p.get("productId") or p.get("linkText")
                    if not pid or pid in ids_vistos:
                        continue
                    ids_vistos.add(pid)
                    nombre = p.get("productName", "").strip()
                    marca = p.get("brand", "").strip()
                    link = p.get("link", "")
                    items = p.get("items", [])
                    if not items:
                        resumen.registrar_descarte("sin items")
                        continue
                    offer = items[0].get("sellers", [{}])[0].get("commertialOffer", {})
                    p_promo = offer.get("Price")
                    p_reg = offer.get("ListPrice") or p_promo
                    avail_qty = offer.get("AvailableQuantity", 0)
                    disponible = "disponible" if avail_qty > 0 else "agotado"
                    if disponible == "agotado":
                        resumen.registrar_descarte("agotado")
                        continue
                    cond = (
                        "Oferta en línea Chedraui"
                        if (p_reg and p_promo and p_reg > p_promo)
                        else "Precio regular Chedraui"
                    )

                    item_norm = evaluar_y_normalizar_producto(
                        tienda="Chedraui",
                        nombre=nombre,
                        marca=marca,
                        precio_regular=p_reg,
                        precio_promo=p_promo,
                        disponible=disponible,
                        url=link,
                        condicion=cond,
                        fuente="API VTEX chedraui.com.mx",
                        fecha_actual=fecha_actual,
                        stock_unidades=int(avail_qty) if avail_qty is not None else None,
                    )
                    if item_norm:
                        resultados.append(item_norm)
                        resumen.registrar_exito()
                    else:
                        resumen.registrar_descarte("criterio exclusión o volumen")
                if len(data) < 50:
                    break
                pausa_aleatoria(0.3, 0.7)
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
                logger.warning(f"Aviso Chedraui '{t}': {e}")
                break
    resumen.imprimir_resumen()
    return resultados
