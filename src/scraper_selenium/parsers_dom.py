"""
Parsers híbridos de DOM (JSON-LD, __NEXT_DATA__, PDP y PLP con BeautifulSoup).
"""

import json
import re
from datetime import datetime

from bs4 import BeautifulSoup

from src.clasificacion import clasificar_categoria, extraer_ml, limpiar_precio


def _construir_registro_producto(
    tienda: str,
    nombre: str,
    precio_regular: float,
    precio_promo: float,
    condicion: str,
    url: str,
    fecha_consulta: str,
) -> dict:
    """Construye un diccionario estandarizado para un producto extraído vía DOM."""
    cat, subcat = clasificar_categoria(nombre)
    ml = extraer_ml(nombre)
    return {
        "tienda": tienda,
        "producto": nombre,
        "marca": nombre.split()[0],
        "categoria": cat,
        "subcategoria": subcat,
        "clase": subcat if cat in ["Tequila", "Mezcal"] else "no_aplica",
        "tipo_mezcal": "Artesanal" if cat == "Mezcal" else "no_aplica",
        "especie_agave": "Tequilana Weber azul"
        if cat == "Tequila"
        else ("Espadín" if cat == "Mezcal" else "no_aplica"),
        "productor": "no_verificado",
        "sello_regulador": "no_verificado",
        "ml": ml,
        "abv": 38.0 if cat in ["Tequila", "Mezcal"] else 40.0,
        "precio_regular": precio_regular,
        "precio_promo": precio_promo,
        "unidades_promo": 1,
        "precio_total_promo": precio_promo,
        "condiciones": condicion,
        "disponibilidad": "disponible",
        "url": url,
        "fecha_consulta": fecha_consulta,
        "fuente": f"Página oficial ({tienda})",
        "confianza": "Confirmado",
    }


def extraer_de_json_embebido(soup: BeautifulSoup, url: str, tienda: str, fecha_consulta: str) -> list[dict]:
    """Intenta extraer productos directamente de scripts JSON-LD o __NEXT_DATA__."""
    productos = []
    scripts = soup.find_all("script", attrs={"type": re.compile(r"json", re.I)})

    for s in scripts:
        if not s.string or len(s.string) < 60:
            continue
        try:
            data = json.loads(s.string)
        except (json.JSONDecodeError, ValueError, TypeError):
            continue

        # Caso 1: JSON-LD ItemList
        if isinstance(data, dict) and data.get("@type") == "ItemList":
            elementos = data.get("itemListElement", [])
            for elem in elementos:
                item = elem.get("item", elem)
                nombre = item.get("name")
                ofertas = item.get("offers", {})
                precio = ofertas.get("price") if isinstance(ofertas, dict) else None
                if nombre and precio:
                    p_val = limpiar_precio(str(precio))
                    if p_val and p_val > 50:
                        productos.append(
                            _construir_registro_producto(
                                tienda=tienda,
                                nombre=nombre,
                                precio_regular=p_val,
                                precio_promo=p_val,
                                condicion="Consulta web directa (JSON-LD)",
                                url=item.get("url") or url,
                                fecha_consulta=fecha_consulta,
                            )
                        )

        # Caso 2: __NEXT_DATA__ (Next.js / Electrode / Walmart platform)
        if s.get("id") == "__NEXT_DATA__" and isinstance(data, dict):

            def buscar_items_recursivo(obj):
                encontrados = []
                if isinstance(obj, dict):
                    nombre = obj.get("name") or obj.get("title") or obj.get("displayName")
                    precio_obj = obj.get("price") or obj.get("priceInfo") or obj.get("prices") or obj.get("itemPrice")
                    if nombre and isinstance(nombre, str) and len(nombre) > 5 and precio_obj:
                        p_val = None
                        if isinstance(precio_obj, (int, float)):
                            p_val = float(precio_obj)
                        elif isinstance(precio_obj, str):
                            p_val = limpiar_precio(precio_obj)
                        elif isinstance(precio_obj, dict):
                            for k in ["price", "itemPrice", "currentPrice", "finalPrice", "priceString"]:
                                if k in precio_obj and precio_obj[k] is not None:
                                    p_val = limpiar_precio(str(precio_obj[k]))
                                    if p_val:
                                        break
                        if p_val and p_val > 50:
                            prod_url = obj.get("productUrl") or obj.get("canonicalUrl") or url
                            encontrados.append((nombre, p_val, prod_url))

                    for v in obj.values():
                        encontrados.extend(buscar_items_recursivo(v))
                elif isinstance(obj, list):
                    for elem in obj:
                        encontrados.extend(buscar_items_recursivo(elem))
                return encontrados

            items_next = buscar_items_recursivo(data)
            nombres_vistos = set()
            for nombre, p_val, prod_url in items_next:
                if nombre in nombres_vistos:
                    continue
                nombres_vistos.add(nombre)
                full_url = f"https://www.sams.com.mx{prod_url}" if prod_url.startswith("/") else prod_url
                productos.append(
                    _construir_registro_producto(
                        tienda=tienda,
                        nombre=nombre,
                        precio_regular=p_val,
                        precio_promo=p_val,
                        condicion="Consulta web directa (__NEXT_DATA__)",
                        url=full_url,
                        fecha_consulta=fecha_consulta,
                    )
                )

    return productos


def parsear_html_con_bs4(html_source: str, url: str, tienda: str) -> list[dict]:
    """Parsea el HTML renderizado con BeautifulSoup y extrae productos estructurados."""
    soup = BeautifulSoup(html_source, "html.parser")
    fecha_consulta = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Estrategia 1: Intentar extracción de JSON estructurado embebido
    prods_json = extraer_de_json_embebido(soup, url, tienda, fecha_consulta)
    if prods_json:
        return prods_json

    productos = []

    # Estrategia 2: Página de producto individual (PDP)
    h1 = soup.find("h1")
    precios_pdp = soup.find_all(attrs={"class": re.compile(r"price|precio|val", re.I)})
    if h1 and precios_pdp:
        nombre = h1.get_text(strip=True)
        precio = limpiar_precio(precios_pdp[0].get_text(strip=True))
        if precio and len(nombre) > 5:
            return [
                _construir_registro_producto(
                    tienda=tienda,
                    nombre=nombre,
                    precio_regular=precio,
                    precio_promo=precio,
                    condicion="Consulta web directa en página de producto",
                    url=url,
                    fecha_consulta=fecha_consulta,
                )
            ]

    # Estrategia 3: Listado de búsqueda o catálogo (búsqueda amplia de contenedores)
    tarjetas = (
        soup.find_all(attrs={"data-testid": re.compile(r"product|item|card", re.I)})
        or soup.find_all(
            "div", class_=re.compile(r"sc-pc-|product-card|item-card|sc-product|product-item|ProductCard", re.I)
        )
        or soup.find_all("article")
    )

    # Si no hay tarjetas explícitas con esos selectores, buscar enlaces a productos
    if not tarjetas:
        enlaces_prod = soup.find_all("a", href=re.compile(r"/p/|/ip/|/producto/", re.I))
        vistos = set()
        for a in enlaces_prod:
            contenedor = a.find_parent("div", class_=True) or a.parent
            if contenedor and id(contenedor) not in vistos:
                vistos.add(id(contenedor))
                tarjetas.append(contenedor)

    nombres_procesados = set()
    for tarjeta in tarjetas:
        # Extraer nombre
        elem_nombre = (
            tarjeta.find(re.compile(r"h[1-4]|a|span|p"), attrs={"class": re.compile(r"title|name|desc", re.I)})
            or tarjeta.find("a", href=re.compile(r"/p/|/ip/", re.I))
            or tarjeta.find("a")
        )
        nombre = elem_nombre.get_text(strip=True) if elem_nombre else ""

        if not nombre or len(nombre) < 6 or nombre in nombres_procesados:
            continue

        # Extraer precios (buscar regular y promo si ambos aparecen)
        elems_precio = tarjeta.find_all(attrs={"class": re.compile(r"price|precio|val", re.I)}) or tarjeta.find_all(
            string=re.compile(r"\$\s*\d+")
        )

        valores_precio = []
        for ep in elems_precio:
            t = ep.get_text(strip=True) if hasattr(ep, "get_text") else str(ep)
            val = limpiar_precio(t)
            if val and val > 40:
                valores_precio.append(val)

        if not valores_precio:
            continue

        nombres_procesados.add(nombre)
        precio_regular = max(valores_precio)
        precio_promo = min(valores_precio)
        condicion = "Descuento en línea" if precio_regular > precio_promo else "Precio regular de catálogo"

        # Extraer link del producto si existe
        link_elem = tarjeta.find("a", href=re.compile(r"/p/|/ip/", re.I))
        item_url = url
        if link_elem and link_elem.get("href"):
            href = link_elem["href"]
            item_url = f"https://www.sams.com.mx{href}" if href.startswith("/") else href

        productos.append(
            _construir_registro_producto(
                tienda=tienda,
                nombre=nombre,
                precio_regular=precio_regular,
                precio_promo=precio_promo,
                condicion=condicion,
                url=item_url,
                fecha_consulta=fecha_consulta,
            )
        )

    return productos
