"""
Evaluación y normalización estricta de productos multitienda bajo NOM-006 y NOM-070.
"""

from src.clasificacion import (
    KEYWORDS_BLENDED_WHISKY,
    PALABRAS_EXCLUIDAS,
    clasificar_agave_mezcal,
    clasificar_estricto,
    es_mercancia_o_no_bebible,
    extraer_ml,
)


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
