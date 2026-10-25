"""
Evaluación y clasificación de ítems crudos de la API VTEX de Bodegas Alianza.
"""

from src.clasificacion import (
    KEYWORDS_BLENDED_WHISKY,
    KEYWORDS_SILVESTRES,
    clasificar_agave_mezcal,
    es_mercancia_o_no_bebible,
    extraer_ml,
    generar_etiqueta_condicion,
)
from src.io_utils import ResumenScraping


def evaluar_item_alianza(p: dict, fecha_actual: str, resumen: ResumenScraping) -> dict | None:
    """Evalúa un producto crudo de la API VTEX de Bodegas Alianza y retorna su registro normalizado o None."""
    nombre = p.get("productName", "").strip()
    marca = p.get("brand", "Desconocida").strip()
    link = p.get("link", "")
    nom_l = nombre.lower()

    ml = extraer_ml(nombre)

    # Descartar artículos no bebibles o mercancía (permitiendo botellas completas ml >= 650 con obsequios)
    if es_mercancia_o_no_bebible(nombre, ml):
        resumen.registrar_descarte("mercancia")
        return None

    items = p.get("items", [])
    if not items:
        resumen.registrar_descarte("sin items")
        return None

    seller = items[0].get("sellers", [{}])[0].get("commertialOffer", {})
    precio_promo = seller.get("Price")
    precio_regular = seller.get("ListPrice") or precio_promo
    avail_qty = seller.get("AvailableQuantity")
    stock_unidades = int(avail_qty) if avail_qty is not None else None
    disponible = "disponible" if (avail_qty and avail_qty > 0) else "agotado"

    if precio_promo is None or precio_promo <= 0:
        resumen.registrar_descarte("precio invalido")
        return None

    condicion = generar_etiqueta_condicion(nombre, float(precio_regular), float(precio_promo))

    # 1. TEQUILA: Solo Cristalino, Añejo, Añejo Cristalino
    if "tequila" in nom_l:
        es_cristalino = "cristalino" in nom_l or "diamante" in nom_l or "ultra" in nom_l or "punta diamante" in nom_l
        es_anejo = "añejo" in nom_l or "anejo" in nom_l or "extra añejo" in nom_l or "extra anejo" in nom_l

        if not es_cristalino and not es_anejo:
            resumen.registrar_descarte("tequila no cristalino/anejo")
            return None

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

        resumen.registrar_exito()
        return {
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
            "stock_unidades": stock_unidades,
            "url": link,
            "fecha_consulta": fecha_actual,
            "fuente": "API oficial Bodegas Alianza",
            "confianza": "Confirmado",
        }

    # 2. MEZCAL: Silvestres, Reposado, Añejo, Reposado Cristalino y Joven / Espadín Joven
    if "mezcal" in nom_l:
        if any(ign in nom_l for ign in ["crema de", "licor de mezcal", "gomitas", "mezcamaica", "mezcarindo"]):
            resumen.registrar_descarte("mezcal no apto")
            return None

        if float(precio_promo) < 250:
            resumen.registrar_descarte("mezcal precio < 250")
            return None

        es_rep = "reposado" in nom_l or "rep " in nom_l or "rep." in nom_l
        es_anejo = "añejo" in nom_l or "anejo" in nom_l
        es_cristalino = "cristalino" in nom_l
        es_silvestre = any(k in nom_l for k in KEYWORDS_SILVESTRES)

        if es_silvestre and not es_rep and not es_anejo:
            subcat = "Silvestre"
            clase = "Joven Silvestre"
        elif es_cristalino and es_anejo:
            subcat = "Añejo"
            clase = "Añejo Cristalino"
        elif es_cristalino:
            subcat = "Reposado Cristalino"
            clase = "Reposado Cristalino"
        elif es_anejo:
            subcat = "Añejo"
            clase = "Añejo"
        elif es_rep:
            subcat = "Reposado"
            clase = "Reposado"
        else:
            subcat = "Espadín Joven"
            clase = "Joven"

        agave = clasificar_agave_mezcal(nombre)
        resumen.registrar_exito()
        return {
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
            "abv": 38.0 if "400 conejos" in nom_l else 40.0,
            "precio_regular": float(precio_regular),
            "precio_promo": float(precio_promo),
            "unidades_promo": 1,
            "precio_total_promo": float(precio_promo),
            "condiciones": condicion,
            "disponibilidad": disponible,
            "stock_unidades": stock_unidades,
            "url": link,
            "fecha_consulta": fecha_actual,
            "fuente": "API oficial Bodegas Alianza",
            "confianza": "Confirmado",
        }

    # 3. LICOR DE WHISKY (HONEY)
    if "honey" in nom_l or "miel" in nom_l:
        resumen.registrar_exito()
        return {
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
            "stock_unidades": stock_unidades,
            "url": link,
            "fecha_consulta": fecha_actual,
            "fuente": "API oficial Bodegas Alianza",
            "confianza": "Confirmado",
        }

    # 4. WHISKY: Solo Blended Scotch y similares a Red Label
    if "whisky" in nom_l or "whiskey" in nom_l:
        if "single malt" in nom_l or "malt scotch" in nom_l or "bourbon" in nom_l:
            resumen.registrar_descarte("whisky no blended")
            return None

        es_blended = any(k in nom_l for k in KEYWORDS_BLENDED_WHISKY)
        if es_blended:
            resumen.registrar_exito()
            return {
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
                "stock_unidades": stock_unidades,
                "url": link,
                "fecha_consulta": fecha_actual,
                "fuente": "API oficial Bodegas Alianza",
                "confianza": "Confirmado",
            }
        resumen.registrar_descarte("whisky no categorizado")
        return None

    # 5. VINO TINTO (Para Clericot y Mesa)
    if "vino" in nom_l and "tinto" in nom_l:
        if float(precio_promo) <= 250:
            resumen.registrar_exito()
            return {
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
                "stock_unidades": stock_unidades,
                "url": link,
                "fecha_consulta": fecha_actual,
                "fuente": "API oficial Bodegas Alianza",
                "confianza": "Confirmado",
            }
        resumen.registrar_descarte("vino precio > 250")
        return None

    resumen.registrar_descarte("otra categoria")
    return None
