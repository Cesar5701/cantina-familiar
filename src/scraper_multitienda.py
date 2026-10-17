"""
Scraper Multitienda (Sam's Club, Walmart, Chedraui, Soriana) + Consolidación con Bodegas Alianza.

Extrae precios verificados en tiempo real de:
1. Sam's Club (sams.com.mx) -> SSR __NEXT_DATA__ JSON
2. Walmart (walmart.com.mx) -> SSR __NEXT_DATA__ JSON
3. Chedraui (chedraui.com.mx) -> API pública VTEX (/api/catalog_system/pub/products/search/)
4. Soriana (soriana.com) -> HTML Salesforce Commerce Cloud (.product-tile)

Aplica filtrado estricto por tipo de bebida (Tequila, Mezcal, Whisky Blended, Licor Honey, Vino Tinto)
y descarta mercancía, alimentos, mezcladores, latas RTD y miniaturas (< 650 ml).
"""

import json
import os
import time
import urllib.error
import urllib.parse
from datetime import datetime

import pandas as pd
from bs4 import BeautifulSoup

from src.clasificacion import (
    KEYWORDS_BLENDED_WHISKY,
    PALABRAS_EXCLUIDAS,
    clasificar_agave_mezcal,
    clasificar_estricto,
    es_mercancia_o_no_bebible,
    extraer_ml,
    limpiar_precio,
)
from src.http_utils import HEADERS_DEFAULT, descargar_html_con_reintentos, descargar_json_con_reintentos
from src.io_utils import ResumenScraping, guardar_csv_atomico
from src.logger import get_logger

logger = get_logger("scraper_multitienda")


def evaluar_y_normalizar_producto(
    tienda: str,
    nombre: str,
    marca: str,
    precio_regular: float,
    precio_promo: float,
    disponible: str,
    url: str,
    condicion: str,
    fuente: str,
    fecha_actual: str,
) -> dict | None:
    """
    Evalúa si un producto cumple con los criterios del proyecto y le asigna
    su categoría y subcategoría estrictas bajo la NOM-006 / NOM-070.
    """
    if not nombre or len(nombre) < 6:
        return None
    nom_l = nombre.lower()

    ml = extraer_ml(nombre)
    # Solo botellas de tamaño estándar o familiar (>= 650 ml)
    if ml < 650:
        return None

    # 1. Descartar artículos no deseados (mercancía física, no bebibles, latas RTD, mezcladores)
    if es_mercancia_o_no_bebible(nombre, ml):
        return None
    if any(excl in nom_l for excl in PALABRAS_EXCLUIDAS):
        return None

    if precio_promo is None or precio_promo <= 50:
        return None
    if precio_regular is None or precio_regular < precio_promo:
        precio_regular = precio_promo

    if not marca or marca.lower() in ["desconocida", "sin marca", "null", "none"]:
        palabras = [
            w
            for w in nombre.split()
            if w.lower()
            not in [
                "tequila",
                "mezcal",
                "whisky",
                "whiskey",
                "vino",
                "tinto",
                "licor",
                "de",
                "100%",
                "agave",
                "artesanal",
                "joven",
                "reposado",
                "añejo",
                "anejo",
                "cristalino",
                "blanco",
            ]
        ]
        marca = palabras[0] if palabras else nombre.split()[0]

    # -------------------------------------------------------------
    # A. TEQUILA
    # -------------------------------------------------------------
    if "tequila" in nom_l:
        if precio_promo < 200:
            return None

        # Clasificación estricta NOM-006 unificada
        cat_comp, subcat, clase = clasificar_estricto(nombre, "Tequila")
        if cat_comp in ["Tequila - Blanco / Plata", "Tequila - Reposado Tradicional", "Tequila - Otros"]:
            return None

        return {
            "tienda": tienda,
            "producto": nombre,
            "marca": marca,
            "categoria": "Tequila",
            "subcategoria": subcat,
            "clase": clase,
            "tipo_mezcal": "no_aplica",
            "especie_agave": "Tequilana Weber azul",
            "productor": marca,
            "sello_regulador": "sí",
            "ml": ml,
            "abv": 35.0 if "cristalino" in subcat.lower() else 38.0,
            "precio_regular": round(float(precio_regular), 2),
            "precio_promo": round(float(precio_promo), 2),
            "unidades_promo": 1,
            "precio_total_promo": round(float(precio_promo), 2),
            "condiciones": condicion,
            "disponibilidad": disponible,
            "url": url,
            "fecha_consulta": fecha_actual,
            "fuente": fuente,
            "confianza": "Confirmado",
        }

    # -------------------------------------------------------------
    # B. MEZCAL (Reposado, Añejo, Silvestres, y 400 Conejos / Amarás / Montelobos de referencia)
    # -------------------------------------------------------------
    if "mezcal" in nom_l:
        if precio_promo < 250:
            return None

        es_referencia = any(m in nom_l for m in ["400 conejos", "amarás", "amaras", "montelobos"])
        cat_comp, subcat, clase = clasificar_estricto(nombre, "Mezcal")

        # Descartar espadines jóvenes que no pertenezcan a marcas de referencia para mantener rigor
        if subcat == "Espadín Joven" and not es_referencia:
            return None

        return {
            "tienda": tienda,
            "producto": nombre,
            "marca": marca,
            "categoria": "Mezcal",
            "subcategoria": subcat,
            "clase": clase,
            "tipo_mezcal": "Artesanal",
            "especie_agave": clasificar_agave_mezcal(nombre),
            "productor": marca,
            "sello_regulador": "sí",
            "ml": ml,
            "abv": 38.0 if "400 conejos" in nom_l else 40.0,
            "precio_regular": round(float(precio_regular), 2),
            "precio_promo": round(float(precio_promo), 2),
            "unidades_promo": 1,
            "precio_total_promo": round(float(precio_promo), 2),
            "condiciones": condicion,
            "disponibilidad": disponible,
            "url": url,
            "fecha_consulta": fecha_actual,
            "fuente": fuente,
            "confianza": "Confirmado",
        }

    # -------------------------------------------------------------
    # C. LICOR DE WHISKY HONEY
    # -------------------------------------------------------------
    if (
        "jack daniel" in nom_l
        or "passport" in nom_l
        or "jim beam" in nom_l
        or "wild turkey" in nom_l
        or "william lawson" in nom_l
    ) and ("honey" in nom_l or "miel" in nom_l):
        if precio_promo < 150:
            return None
        return {
            "tienda": tienda,
            "producto": nombre,
            "marca": marca,
            "categoria": "Licor de Whisky",
            "subcategoria": "Honey Liqueur",
            "clase": "no_aplica",
            "tipo_mezcal": "no_aplica",
            "especie_agave": "no_aplica",
            "productor": marca,
            "sello_regulador": "no_aplica",
            "ml": ml,
            "abv": 35.0,
            "precio_regular": round(float(precio_regular), 2),
            "precio_promo": round(float(precio_promo), 2),
            "unidades_promo": 1,
            "precio_total_promo": round(float(precio_promo), 2),
            "condiciones": condicion,
            "disponibilidad": disponible,
            "url": url,
            "fecha_consulta": fecha_actual,
            "fuente": fuente,
            "confianza": "Confirmado",
        }

    # -------------------------------------------------------------
    # D. WHISKY BLENDED SCOTCH
    # -------------------------------------------------------------
    if (
        "whisky" in nom_l
        or "whiskey" in nom_l
        or "johnnie walker" in nom_l
        or "buchanan" in nom_l
        or "chivas regal" in nom_l
        or "black & white" in nom_l
        or "ballantine" in nom_l
        or "william lawson" in nom_l
    ):
        if any(
            ign in nom_l
            for ign in ["single malt", "malt scotch", "bourbon", "tennessee", "apple", "fire", "peach", "blackberry"]
        ):
            return None
        if precio_promo < 160:
            return None
        if any(k in nom_l for k in KEYWORDS_BLENDED_WHISKY):
            return {
                "tienda": tienda,
                "producto": nombre,
                "marca": marca,
                "categoria": "Whisky",
                "subcategoria": "Blended Scotch",
                "clase": "no_aplica",
                "tipo_mezcal": "no_aplica",
                "especie_agave": "no_aplica",
                "productor": marca,
                "sello_regulador": "no_aplica",
                "ml": ml,
                "abv": 40.0,
                "precio_regular": round(float(precio_regular), 2),
                "precio_promo": round(float(precio_promo), 2),
                "unidades_promo": 1,
                "precio_total_promo": round(float(precio_promo), 2),
                "condiciones": condicion,
                "disponibilidad": disponible,
                "url": url,
                "fecha_consulta": fecha_actual,
                "fuente": fuente,
                "confianza": "Confirmado",
            }

    # -------------------------------------------------------------
    # E. VINO TINTO PARA CLERICOT Y MESA
    # -------------------------------------------------------------
    if (
        "vino tinto" in nom_l
        or "carlo rossi" in nom_l
        or "vino lambrusco" in nom_l
        or "tinto california" in nom_l
        or "padre kino" in nom_l
    ):
        if any(ign in nom_l for ign in ["blanco", "rosado", "espumoso", "champagne", "prosecco"]):
            return None
        # Permitir botellas individuales económicas (<= $280) o garrafas familiares de 1.5L a 4L (<= $550)
        limite_precio = 550.0 if ml >= 1500 else 260.0
        if 65.0 <= precio_promo <= limite_precio:
            return {
                "tienda": tienda,
                "producto": nombre,
                "marca": marca,
                "categoria": "Vino",
                "subcategoria": "Tinto Clericot",
                "clase": "no_aplica",
                "tipo_mezcal": "no_aplica",
                "especie_agave": "no_aplica",
                "productor": marca,
                "sello_regulador": "no_aplica",
                "ml": ml,
                "abv": 12.0,
                "precio_regular": round(float(precio_regular), 2),
                "precio_promo": round(float(precio_promo), 2),
                "unidades_promo": 1,
                "precio_total_promo": round(float(precio_promo), 2),
                "condiciones": condicion,
                "disponibilidad": disponible,
                "url": url,
                "fecha_consulta": fecha_actual,
                "fuente": fuente,
                "confianza": "Confirmado",
            }

    return None


# ==============================================================================
# 1. SCRAPER CHEDRAUI (API VTEX OFICIAL)
# ==============================================================================
def scrapear_chedraui() -> list[dict]:
    logger.info("=" * 60)
    logger.info("1. SCRAPEANDO CHEDRAUI (API VTEX chedraui.com.mx)")
    logger.info("=" * 60)
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
        "jack daniels honey",
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
                    )
                    if item_norm:
                        resultados.append(item_norm)
                        resumen.registrar_exito()
                    else:
                        resumen.registrar_descarte("criterio exclusión o volumen")
                if len(data) < 50:
                    break
                time.sleep(0.3)
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


# ==============================================================================
# 2. SCRAPER SAM'S CLUB & WALMART (SSR __NEXT_DATA__)
# ==============================================================================
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
            html = descargar_html_con_reintentos(url, headers=HEADERS_DEFAULT, timeout=15)
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


# ==============================================================================
# 3. SCRAPER SORIANA (HTML SALESFORCE COMMERCE CLOUD)
# ==============================================================================
def scrapear_soriana() -> list[dict]:
    logger.info("=" * 60)
    logger.info("SCRAPEANDO SORIANA (soriana.com SFCC Catalog)")
    logger.info("=" * 60)
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
            html = descargar_html_con_reintentos(url, headers=HEADERS_DEFAULT, timeout=15)
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
    prods_chedraui = scrapear_chedraui()
    if prods_chedraui:
        guardar_csv_atomico(pd.DataFrame(prods_chedraui), "data/scraped_chedraui.csv")

    # 2. Sam's Club
    prods_sams = scrapear_nextjs_walmart_platform("Sam's Club", "www.sams.com.mx", terminos_sams)
    if prods_sams:
        guardar_csv_atomico(pd.DataFrame(prods_sams), "data/scraped_sams.csv")

    # 3. Walmart
    prods_walmart = scrapear_nextjs_walmart_platform("Walmart", "www.walmart.com.mx", terminos_walmart)
    if prods_walmart:
        guardar_csv_atomico(pd.DataFrame(prods_walmart), "data/scraped_walmart.csv")

    # 4. Soriana
    prods_soriana = scrapear_soriana()
    if prods_soriana:
        guardar_csv_atomico(pd.DataFrame(prods_soriana), "data/scraped_soriana.csv")

    logger.info("=" * 70)
    logger.info("RESUMEN DE EXTRACCIÓN MULTITIENDA")
    logger.info("=" * 70)
    logger.info(f"  - Chedraui:   {len(prods_chedraui)} productos")
    logger.info(f"  - Sam's Club: {len(prods_sams)} productos")
    logger.info(f"  - Walmart:    {len(prods_walmart)} productos")
    logger.info(f"  - Soriana:    {len(prods_soriana)} productos")


if __name__ == "__main__":
    main()
