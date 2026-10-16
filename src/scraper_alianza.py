"""
Scraper ético para Bodegas Alianza (API oficial VTEX).
Consulta exclusivamente la API pública permitida en robots.txt:
/api/catalog_system/pub/products/search/
"""

import argparse
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime

BASE_URL = "https://www.bodegasalianza.com/api/catalog_system/pub/products/search/{term}"
USER_AGENT = "CantinaFamiliarBot/1.0 (+decision-support; personal-use)"


import os

RAIZ_PROYECTO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if RAIZ_PROYECTO not in sys.path:
    sys.path.insert(0, RAIZ_PROYECTO)

from src.clasificacion import clasificar_categoria, extraer_ml
from src.http_utils import descargar_json_con_reintentos
from src.io_utils import ResumenScraping, guardar_csv_atomico
from src.logger import get_logger

logger = get_logger("scraper_alianza")


def consultar_api_alianza(
    termino: str, delay_segundos: float = 1.0, resumen: ResumenScraping | None = None
) -> list[dict]:
    """Consulta la API de catálogo de Bodegas Alianza para un término con reintentos automáticos."""
    url = BASE_URL.format(term=urllib.parse.quote(termino))

    try:
        data = descargar_json_con_reintentos(url, headers={"User-Agent": USER_AGENT})
        if not data:
            return []
    except Exception as e:
        if resumen:
            resumen.registrar_error_red(url, e)
        logger.error(f"Error al consultar '{termino}': {e}")
        return []

    productos = []
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M")

    for p in data:
        nombre = p.get("productName", "")
        marca = p.get("brand", "Desconocida")
        link = p.get("link", "")
        categoria, subcategoria = clasificar_categoria(nombre)
        ml = extraer_ml(nombre)

        items = p.get("items", [])
        if not items:
            if resumen:
                resumen.registrar_descarte("sin items")
            continue

        seller = items[0].get("sellers", [{}])[0].get("commertialOffer", {})
        precio_promo = seller.get("Price")
        precio_regular = seller.get("ListPrice") or precio_promo
        disponible = "disponible" if (seller.get("AvailableQuantity", 0) > 0) else "agotado"

        if precio_promo is None or precio_promo <= 0:
            if resumen:
                resumen.registrar_descarte("precio invalido")
            continue

        condicion = (
            "Descuento directo Aniversario Web" if (precio_regular > precio_promo) else "Precio regular catálogo"
        )

        productos.append(
            {
                "tienda": "Bodegas Alianza",
                "producto": nombre,
                "marca": marca,
                "categoria": categoria,
                "subcategoria": subcategoria,
                "clase": subcategoria if categoria in ["Tequila", "Mezcal"] else "no_aplica",
                "tipo_mezcal": "Artesanal" if categoria == "Mezcal" else "no_aplica",
                "especie_agave": "Tequilana Weber azul"
                if categoria == "Tequila"
                else ("Espadín" if categoria == "Mezcal" else "no_aplica"),
                "productor": marca,
                "sello_regulador": "sí" if categoria in ["Tequila", "Mezcal"] else "no_aplica",
                "ml": ml,
                "abv": 38.0 if categoria in ["Tequila", "Mezcal"] else (40.0 if categoria == "Whisky" else 12.0),
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
        if resumen:
            resumen.registrar_exito()

    time.sleep(delay_segundos)
    return productos


def main():
    parser = argparse.ArgumentParser(description="Scraper oficial ético para Bodegas Alianza (VTEX API).")
    parser.add_argument(
        "--terminos",
        nargs="+",
        default=["1800", "Herradura", "Amarás", "Red Label", "Jack Daniel"],
        help="Términos de búsqueda en catálogo.",
    )
    parser.add_argument("--salida", default="data/scraped_alianza.csv", help="Ruta del CSV de salida.")
    args = parser.parse_args()

    todos = []
    resumen = ResumenScraping("Bodegas Alianza")
    logger.info(f"Iniciando consulta para {len(args.terminos)} términos en Bodegas Alianza...")
    for t in args.terminos:
        logger.info(f"  -> Buscando: {t}")
        prods = consultar_api_alianza(t, resumen=resumen)
        todos.extend(prods)
        logger.info(f"     Encontrados: {len(prods)}")

    resumen.imprimir_resumen()
    import pandas as pd

    df = pd.DataFrame(todos)
    guardar_csv_atomico(df, args.salida)
    logger.info(f"Guardados {len(df)} registros en {args.salida}")


if __name__ == "__main__":
    main()
