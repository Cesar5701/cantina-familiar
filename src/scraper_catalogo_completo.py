"""
Scraper exhaustivo para Bodegas Alianza por tipo de bebida (sin sesgo de marca).

Filtros aplicados según solicitud:
1. Tequila: Exclusivamente Cristalino, Añejo y Añejo Cristalino.
   (Descarta Blancos y Reposados tradicionales no cristalinos).
2. Mezcal: Desde Reposado hasta Añejo, y Silvestres (Tobalá, Cupreata, Cuishe, etc.).
   (Descarta Espadín Joven básico).
3. Whisky: Exclusivamente Blended Scotch y similares a Red Label.
   (Descarta Single Malts).
4. Honey: Licores de whisky con miel (Jack Daniel's Honey).
5. Vino: Tintos para clericot y mesa familiar.
"""

import time
import urllib.parse
import urllib.request
from datetime import datetime

import pandas as pd

from src.clasificacion import KEYWORDS_BLENDED_WHISKY, KEYWORDS_SILVESTRES, clasificar_agave_mezcal, extraer_ml
from src.http_utils import USER_AGENT_BOT, descargar_json_con_reintentos
from src.io_utils import ResumenScraping, guardar_csv_atomico
from src.logger import get_logger

USER_AGENT = USER_AGENT_BOT

logger = get_logger("scraper_catalogo_completo")


def consultar_endpoint_paginado(
    termino: str, max_paginas: int = 5, resumen: ResumenScraping | None = None
) -> list[dict]:
    """Consulta la API de VTEX con paginación de 50 en 50 elementos y reintentos automáticos."""
    items = []
    headers = {"User-Agent": USER_AGENT}
    for pag in range(max_paginas):
        inicio = pag * 50
        fin = inicio + 49
        url = f"https://www.bodegasalianza.com/api/catalog_system/pub/products/search/{urllib.parse.quote(termino)}?_from={inicio}&_to={fin}"
        try:
            data = descargar_json_con_reintentos(url, headers=headers)
            if not data:
                break
            items.extend(data)
            if len(data) < 50:
                break
        except Exception as e:
            if resumen:
                resumen.registrar_error_red(url, e)
            logger.warning(f"Fin o error en '{termino}' pag {pag}: {e}")
            break
        time.sleep(0.25)
    return items


def procesar_catalogo_completo() -> list[dict]:
    """Descarga y clasifica todos los productos sin sesgo de marca."""
    terminos_busqueda = [
        "tequila",
        "tequila cristalino",
        "tequila anejo",
        "mezcal",
        "mezcal reposado",
        "mezcal anejo",
        "mezcal tobala",
        "mezcal cupreata",
        "whisky",
        "whisky blended",
        "jack daniels honey",
        "vino tinto",
        "vino california",
        "vino reservado",
    ]

    productos_crudos = []
    ids_vistos = set()

    logger.info("Iniciando extracción exhaustiva del catálogo de Bodegas Alianza...")
    for t in terminos_busqueda:
        logger.info(f"  -> Consultando: '{t}'...")
        lote = consultar_endpoint_paginado(t, max_paginas=5)
        nuevos = 0
        for p in lote:
            pid = p.get("productId") or p.get("linkText")
            if pid and pid not in ids_vistos:
                ids_vistos.add(pid)
                productos_crudos.append(p)
                nuevos += 1
        logger.info(f"     Nuevos encontrados: {nuevos} (Total acumulado: {len(productos_crudos)})")

    # Filtrar y clasificar
    logger.info("Filtrando y clasificando por tipos estrictos solicitados...")
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M")
    productos_filtrados = []
    resumen = ResumenScraping("Bodegas Alianza")

    for p in productos_crudos:
        nombre = p.get("productName", "").strip()
        marca = p.get("brand", "Desconocida").strip()
        link = p.get("link", "")
        nom_l = nombre.lower()

        # Descartar artículos no bebibles o mercancía
        if any(
            ign in nom_l
            for ign in ["chocolate", "lata 180", "vaso", "termo", "estuche vacío", "hielera", "playera", "gorra"]
        ):
            resumen.registrar_descarte("mercancia")
            continue

        items = p.get("items", [])
        if not items:
            resumen.registrar_descarte("sin items")
            continue

        seller = items[0].get("sellers", [{}])[0].get("commertialOffer", {})
        precio_promo = seller.get("Price")
        precio_regular = seller.get("ListPrice") or precio_promo
        disponible = "disponible" if (seller.get("AvailableQuantity", 0) > 0) else "agotado"

        if precio_promo is None or precio_promo <= 0:
            resumen.registrar_descarte("precio invalido")
            continue

        ml = extraer_ml(nombre)
        condicion = (
            "Descuento directo Aniversario Web" if (precio_regular > precio_promo) else "Precio regular catálogo"
        )

        # -------------------------------------------------------------
        # 1. TEQUILA: Solo Cristalino, Añejo, Añejo Cristalino
        # -------------------------------------------------------------
        if "tequila" in nom_l:
            es_cristalino = (
                "cristalino" in nom_l or "diamante" in nom_l or "ultra" in nom_l or "punta diamante" in nom_l
            )
            es_anejo = "añejo" in nom_l or "anejo" in nom_l or "extra añejo" in nom_l or "extra anejo" in nom_l

            # Descartar blancos puros y reposados tradicionales que no sean cristalinos
            if not es_cristalino and not es_anejo:
                resumen.registrar_descarte("tequila no cristalino/anejo")
                continue

            # Determinación de subcategoría y clase
            if es_cristalino and es_anejo:
                subcat = "Añejo Cristalino"
                clase = "Añejo Cristalino"
            elif es_cristalino:
                subcat = "Añejo Cristalino" if ("añejo" in nom_l or "ultra" in nom_l) else "Reposado Cristalino"
                clase = subcat
            elif "extra" in nom_l:
                subcat = "Añejo Tradicional"
                clase = "Extra Añejo"
            else:
                subcat = "Añejo Tradicional"
                clase = "Añejo"

            productos_filtrados.append(
                {
                    "tienda": "Bodegas Alianza",
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
                    "abv": 38.0,
                    "precio_regular": float(precio_regular),
                    "precio_promo": float(precio_promo),
                    "unidades_promo": 1,
                    "precio_total_promo": float(precio_promo),
                    "condiciones": condicion,
                    "disponibilidad": disponible,
                    "url": link,
                    "fecha_consulta": fecha_actual,
                    "fuente": "API oficial Bodegas Alianza",
                    "confianza": "Confirmado",
                }
            )
            resumen.registrar_exito()
            continue

        # -------------------------------------------------------------
        # 2. MEZCAL: Reposado hasta Añejo, y Silvestres
        # -------------------------------------------------------------
        if "mezcal" in nom_l:
            if any(ign in nom_l for ign in ["crema de", "licor de mezcal", "gomitas"]):
                resumen.registrar_descarte("mezcal no apto")
                continue

            es_rep = "reposado" in nom_l or "rep " in nom_l or "rep." in nom_l
            es_anejo = "añejo" in nom_l or "anejo" in nom_l
            es_cristalino = "cristalino" in nom_l
            es_silvestre = any(k in nom_l for k in KEYWORDS_SILVESTRES)

            # Descartar Espadín joven común que no sea silvestre ni reposado/añejo
            if not es_rep and not es_anejo and not es_cristalino and not es_silvestre:
                resumen.registrar_descarte("espadin joven no silvestre")
                continue

            if es_silvestre and not es_rep and not es_anejo:
                subcat = "Silvestre"
                clase = "Joven Silvestre"
            elif es_anejo:
                subcat = "Añejo"
                clase = "Añejo"
            elif es_cristalino:
                subcat = "Reposado Cristalino"
                clase = "Reposado Cristalino"
            else:
                subcat = "Reposado"
                clase = "Reposado"

            agave = clasificar_agave_mezcal(nombre)

            productos_filtrados.append(
                {
                    "tienda": "Bodegas Alianza",
                    "producto": nombre,
                    "marca": marca,
                    "categoria": "Mezcal",
                    "subcategoria": subcat,
                    "clase": clase,
                    "tipo_mezcal": "Artesanal",
                    "especie_agave": agave,
                    "productor": marca,
                    "sello_regulador": "sí",
                    "ml": ml,
                    "abv": 40.0,
                    "precio_regular": float(precio_regular),
                    "precio_promo": float(precio_promo),
                    "unidades_promo": 1,
                    "precio_total_promo": float(precio_promo),
                    "condiciones": condicion,
                    "disponibilidad": disponible,
                    "url": link,
                    "fecha_consulta": fecha_actual,
                    "fuente": "API oficial Bodegas Alianza",
                    "confianza": "Confirmado",
                }
            )
            resumen.registrar_exito()
            continue

        # -------------------------------------------------------------
        # 3. LICOR DE WHISKY (HONEY)
        # -------------------------------------------------------------
        if "honey" in nom_l or "miel" in nom_l:
            productos_filtrados.append(
                {
                    "tienda": "Bodegas Alianza",
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
                    "precio_regular": float(precio_regular),
                    "precio_promo": float(precio_promo),
                    "unidades_promo": 1,
                    "precio_total_promo": float(precio_promo),
                    "condiciones": condicion,
                    "disponibilidad": disponible,
                    "url": link,
                    "fecha_consulta": fecha_actual,
                    "fuente": "API oficial Bodegas Alianza",
                    "confianza": "Confirmado",
                }
            )
            resumen.registrar_exito()
            continue

        # -------------------------------------------------------------
        # 4. WHISKY: Solo Blended Scotch y similares a Red Label
        # -------------------------------------------------------------
        if "whisky" in nom_l or "whiskey" in nom_l:
            if "single malt" in nom_l or "malt scotch" in nom_l or "bourbon" in nom_l:
                resumen.registrar_descarte("whisky no blended")
                continue

            es_blended = any(k in nom_l for k in KEYWORDS_BLENDED_WHISKY)
            if es_blended:
                productos_filtrados.append(
                    {
                        "tienda": "Bodegas Alianza",
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
                        "precio_regular": float(precio_regular),
                        "precio_promo": float(precio_promo),
                        "unidades_promo": 1,
                        "precio_total_promo": float(precio_promo),
                        "condiciones": condicion,
                        "disponibilidad": disponible,
                        "url": link,
                        "fecha_consulta": fecha_actual,
                        "fuente": "API oficial Bodegas Alianza",
                        "confianza": "Confirmado",
                    }
                )
                resumen.registrar_exito()
                continue
            else:
                resumen.registrar_descarte("whisky no categorizado")
                continue

        # -------------------------------------------------------------
        # 5. VINO TINTO (Para Clericot y Mesa)
        # -------------------------------------------------------------
        if "vino" in nom_l and "tinto" in nom_l:
            # Vinos tintos de consumo accesible
            if float(precio_promo) <= 250:
                productos_filtrados.append(
                    {
                        "tienda": "Bodegas Alianza",
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
                        "precio_regular": float(precio_regular),
                        "precio_promo": float(precio_promo),
                        "unidades_promo": 1,
                        "precio_total_promo": float(precio_promo),
                        "condiciones": condicion,
                        "disponibilidad": disponible,
                        "url": link,
                        "fecha_consulta": fecha_actual,
                        "fuente": "API oficial Bodegas Alianza",
                        "confianza": "Confirmado",
                    }
                )
                resumen.registrar_exito()
                continue
            else:
                resumen.registrar_descarte("vino precio > 250")
                continue

        resumen.registrar_descarte("otra categoria")

    resumen.imprimir_resumen()
    return productos_filtrados


def main():
    productos = procesar_catalogo_completo()
    df = pd.DataFrame(productos)
    salida = "data/scraped_alianza_completo.csv"
    guardar_csv_atomico(df, salida)
    logger.info(f"Se guardaron {len(df)} productos validados en: {salida}")
    logger.info("Desglose por categoría:")
    for cat, cnt in df["categoria"].value_counts().items():
        logger.info(f"  - {cat}: {cnt}")


if __name__ == "__main__":
    main()
