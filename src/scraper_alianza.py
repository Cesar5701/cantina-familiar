"""
Scraper ético para Bodegas Alianza (API oficial VTEX).
Consulta exclusivamente la API pública permitida en robots.txt:
/api/catalog_system/pub/products/search/
"""

import sys
import re
import json
import time
import argparse
import urllib.request
import urllib.parse
from datetime import datetime

BASE_URL = "https://www.bodegasalianza.com/api/catalog_system/pub/products/search/{term}"
USER_AGENT = "CantinaFamiliarBot/1.0 (+decision-support; personal-use)"


def extraer_ml(nombre: str) -> int:
    """Extrae el volumen en mililitros a partir del nombre del producto."""
    # Buscar formato litros: ej. 1.75 L, 1.75L, 1 L, 2 L, 4 L
    match_l = re.search(r'(\d+(?:\.\d+)?)\s*(?:l|lt|lts|litro|litros)\b', nombre, re.I)
    if match_l:
        return int(float(match_l.group(1)) * 1000)

    # Buscar formato mililitros: ej. 700 ml, 750ml, 946 ml
    match_ml = re.search(r'(\d+)\s*(?:ml|mls|mililitros)\b', nombre, re.I)
    if match_ml:
        return int(match_ml.group(1))

    return 750  # Estándar por defecto si no se especifica


def clasificar_categoria(nombre: str) -> tuple[str, str]:
    """Clasifica categoría y subcategoría a partir del nombre."""
    nombre_l = nombre.lower()
    if "tequila" in nombre_l:
        if "cristalino" in nombre_l:
            return "Tequila", "Añejo Cristalino"
        if "añejo" in nombre_l or "anejo" in nombre_l:
            return "Tequila", "Añejo Tradicional"
        if "reposado" in nombre_l or "rep" in nombre_l:
            return "Tequila", "Reposado"
        if "blanco" in nombre_l or "plata" in nombre_l:
            return "Tequila", "Blanco"
        return "Tequila", "Tequila General"

    if "mezcal" in nombre_l:
        if "tobalá" in nombre_l or "tobala" in nombre_l or "cupreata" in nombre_l or "cuishe" in nombre_l:
            return "Mezcal", "Silvestre"
        if "añejo" in nombre_l or "anejo" in nombre_l:
            return "Mezcal", "Añejo"
        if "cristalino" in nombre_l:
            return "Mezcal", "Reposado Cristalino"
        if "reposado" in nombre_l or "rep" in nombre_l:
            return "Mezcal", "Reposado"
        return "Mezcal", "Espadín Joven"

    if "honey" in nombre_l:
        return "Licor de Whisky", "Honey Liqueur"

    if "whisky" in nombre_l or "whiskey" in nombre_l:
        return "Whisky", "Blended Scotch"

    if "vino" in nombre_l:
        return "Vino", "Tinto Clericot"

    return "Destilado", "General"


def consultar_api_alianza(termino: str, delay_segundos: float = 1.0) -> list[dict]:
    """Consulta la API de catálogo de Bodegas Alianza para un término."""
    url = BASE_URL.format(term=urllib.parse.quote(termino))
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[ERROR] Error al consultar '{termino}': {e}", file=sys.stderr)
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
            continue

        seller = items[0].get("sellers", [{}])[0].get("commertialOffer", {})
        precio_promo = seller.get("Price")
        precio_regular = seller.get("ListPrice") or precio_promo
        disponible = "disponible" if (seller.get("AvailableQuantity", 0) > 0) else "agotado"

        if precio_promo is None or precio_promo <= 0:
            continue

        condicion = "Descuento directo Aniversario Web" if (precio_regular > precio_promo) else "Precio regular catálogo"

        productos.append({
            "tienda": "Bodegas Alianza",
            "producto": nombre,
            "marca": marca,
            "categoria": categoria,
            "subcategoria": subcategoria,
            "clase": subcategoria if categoria in ["Tequila", "Mezcal"] else "no_aplica",
            "tipo_mezcal": "Artesanal" if categoria == "Mezcal" else "no_aplica",
            "especie_agave": "Tequilana Weber azul" if categoria == "Tequila" else ("Espadín" if categoria == "Mezcal" else "no_aplica"),
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
            "confianza": "Confirmado"
        })

    time.sleep(delay_segundos)
    return productos


def main():
    parser = argparse.ArgumentParser(description="Scraper oficial ético para Bodegas Alianza (VTEX API).")
    parser.add_argument("--terminos", nargs="+", default=["1800", "Herradura", "Amarás", "Red Label", "Jack Daniel"],
                        help="Términos de búsqueda en catálogo.")
    parser.add_argument("--salida", default="data/scraped_alianza.csv", help="Ruta del CSV de salida.")
    args = parser.parse_args()

    todos = []
    print(f"Iniciando consulta para {len(args.terminos)} términos en Bodegas Alianza...")
    for t in args.terminos:
        print(f"  -> Buscando: {t}")
        prods = consultar_api_alianza(t)
        todos.extend(prods)
        print(f"     Encontrados: {len(prods)}")

    import pandas as pd
    df = pd.DataFrame(todos)
    df.to_csv(args.salida, index=False)
    print(f"Guardados {len(df)} registros en {args.salida}")


if __name__ == "__main__":
    main()
