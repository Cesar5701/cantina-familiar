"""
Detección y Clasificación Estricta bajo NOM-006 (Tequila), NOM-070 (Mezcal), Whisky y Vinos (H1).
"""

from typing import Any, Optional, Tuple, Union

from src.clasificacion.constantes import (
    KEYWORDS_BLENDED_WHISKY,
    KEYWORDS_SILVESTRES,
    MARCAS_REPOSADO_CRISTALINO_POR_NORMA,
)


def clasificar_agave_mezcal(nombre: str) -> str:
    """
    Identifica la especie de agave o ensamble para mezcales según la NOM-070.
    """
    nom_l = str(nombre).lower()
    if "cosecha salvaje" in nom_l:
        return "Ensamble Silvestre Tobalá-Mexicano (A. potatorum / A. rhodacantha)"
    if "mexicano" in nom_l and ("tobalá" in nom_l or "tobala" in nom_l):
        return "Ensamble Silvestre Tobalá-Mexicano (A. potatorum / A. rhodacantha)"
    if "espadín" in nom_l and ("tobalá" in nom_l or "tobala" in nom_l):
        return "Ensamble Espadín-Tobalá"
    if "mexicano" in nom_l:
        return "Mexicano silvestre (A. rhodacantha)"
    if "cuishe" in nom_l or "cuixe" in nom_l:
        return "Cuishe silvestre (A. karwinskii)"
    if "tobalá" in nom_l or "tobala" in nom_l:
        return "Tobalá silvestre (A. potatorum)"
    if "cupreata" in nom_l:
        return "Cupreata silvestre (A. cupreata)"
    if "tepeztate" in nom_l or "tepextate" in nom_l:
        return "Tepeztate silvestre (A. marmorata)"
    if "arroqueño" in nom_l or "arroqueno" in nom_l:
        return "Arroqueño silvestre (A. americana)"
    if "cenizo" in nom_l:
        return "Cenizo silvestre (A. durangensis)"
    if "salmiana" in nom_l:
        return "Salmiana silvestre"
    if "jabalí" in nom_l or "jabali" in nom_l:
        return "Jabalí silvestre (A. convallis)"
    if "barril" in nom_l:
        return "Barril silvestre (A. karwinskii)"
    if "madrecuishe" in nom_l or "madrecuixe" in nom_l:
        return "Madrecuishe silvestre (A. karwinskii)"
    if "papalometl" in nom_l:
        return "Papalometl silvestre (A. potatorum)"
    if "espadín" in nom_l or "espadin" in nom_l:
        return "Espadín (A. angustifolia)"
    return "Agave mezcalero (NOM-070)"


def detectar_categoria_base(nombre: str) -> str:
    """Infiere la macro-categoría de bebida a partir del nombre del producto."""
    nom_l = str(nombre).lower()
    if "tequila" in nom_l:
        return "Tequila"
    if "mezcal" in nom_l:
        return "Mezcal"
    # Licor Honey de marcas de whisky
    if (
        "jack daniel" in nom_l
        or "passport" in nom_l
        or "jim beam" in nom_l
        or "wild turkey" in nom_l
        or "william lawson" in nom_l
    ) and ("honey" in nom_l or "miel" in nom_l):
        return "Licor de Whisky"
    if "honey" in nom_l and ("whisky" in nom_l or "whiskey" in nom_l):
        return "Licor de Whisky"
    if "whisky" in nom_l or "whiskey" in nom_l or any(k in nom_l for k in KEYWORDS_BLENDED_WHISKY):
        return "Whisky"
    if (
        "vino" in nom_l
        or "carlo rossi" in nom_l
        or "lambrusco" in nom_l
        or "padre kino" in nom_l
        or "california" in nom_l
    ):
        return "Vino"
    return "Otros"


def clasificar_estricto(row_o_nombre: Union[dict, Any, str], categoria: Optional[str] = None) -> Tuple[str, str, str]:
    """
    Clasifica estrictamente un producto bajo las normas oficiales y el estándar del proyecto.

    Acepta:
    - Un dict o pd.Series con claves 'producto' y 'categoria'
    - Un nombre de producto (str) y una categoría opcional (str)

    Retorna:
    - (categoria_comparable, subcategoria, clase)
    """
    if isinstance(row_o_nombre, str):
        nom = row_o_nombre.strip()
        cat = categoria or detectar_categoria_base(nom)
    elif hasattr(row_o_nombre, "get"):
        nom = str(row_o_nombre.get("producto", "")).strip()
        cat = str(row_o_nombre.get("categoria", "") or categoria or detectar_categoria_base(nom)).strip()
    else:
        # pd.Series / objeto indexable
        nom = str(row_o_nombre["producto"]).strip()
        cat = str(row_o_nombre.get("categoria", categoria or detectar_categoria_base(nom))).strip()

    nom_l = nom.lower()

    # -----------------------------------------------------------------------
    # TEQUILA (NOM-006-SCFI)
    # -----------------------------------------------------------------------
    if cat == "Tequila" or "tequila" in nom_l:
        # 1. BLANCO / PLATA (0 meses barrica)
        if ("plata" in nom_l or "blanco" in nom_l or "silver" in nom_l) and not (
            "añejo" in nom_l or "anejo" in nom_l or "reposado" in nom_l
        ):
            return "Tequila - Blanco / Plata", "Blanco", "Blanco"
        if "don ramón plata" in nom_l or "don ramon plata" in nom_l:
            return "Tequila - Blanco / Plata", "Blanco", "Blanco"

        # 2. CASO DON JULIO 70 (Añejo Cristalino por NOM-006)
        if "don julio 70" in nom_l or "don julio 70 añejo" in nom_l:
            return "Tequila - Añejo Cristalino", "Añejo Cristalino", "Añejo Cristalino"

        # 3. CASO DON RAMÓN
        if "don ramón" in nom_l or "don ramon" in nom_l:
            if "añejo cristalino" in nom_l or ("añejo" in nom_l and ("platinium" in nom_l or "cristalino" in nom_l)):
                return "Tequila - Añejo Cristalino", "Añejo Cristalino", "Añejo Cristalino"
            elif "reposado cristalino" in nom_l or (
                "reposado" in nom_l and ("platinium" in nom_l or "cristalino" in nom_l)
            ):
                return "Tequila - Reposado Cristalino", "Reposado Cristalino", "Reposado Cristalino"
            elif "reposado" in nom_l:
                return "Tequila - Reposado Tradicional", "Reposado", "Reposado"
            elif "añejo" in nom_l or "dark" in nom_l:
                return "Tequila - Añejo Tradicional", "Añejo Tradicional", "Añejo"

        # 4. MARCAS REPOSADO CRISTALINO POR NORMA (cuando omiten la palabra 'Reposado')
        if any(m in nom_l for m in MARCAS_REPOSADO_CRISTALINO_POR_NORMA) and not (
            "añejo" in nom_l or "anejo" in nom_l or "ultra añejo" in nom_l
        ):
            return "Tequila - Reposado Cristalino", "Reposado Cristalino", "Reposado Cristalino"

        # 5. MAESTRO DOBEL DIAMANTE (Ensamble clarificado carbón activado -> Añejo Cristalino)
        if "dobel diamante" in nom_l or "maestro dobel diamante" in nom_l:
            return "Tequila - Añejo Cristalino", "Añejo Cristalino", "Añejo Cristalino"

        # 6. REGLAS GENERALES PARA OTROS TEQUILAS
        es_rep = "reposado" in nom_l or "rep." in nom_l or "rep " in nom_l
        es_crist = (
            "cristalino" in nom_l
            or "crist." in nom_l
            or "ultra" in nom_l
            or "platinium" in nom_l
            or "diamante" in nom_l
            or "cristal" in nom_l
        )
        es_anejo = "añejo" in nom_l or "anejo" in nom_l or "extra añejo" in nom_l or "milenio" in nom_l

        if es_rep and es_crist and not es_anejo:
            return "Tequila - Reposado Cristalino", "Reposado Cristalino", "Reposado Cristalino"
        elif es_rep and not es_crist and not es_anejo:
            return "Tequila - Reposado Tradicional", "Reposado", "Reposado"
        elif es_anejo and es_crist:
            return "Tequila - Añejo Cristalino", "Añejo Cristalino", "Añejo Cristalino"
        elif es_anejo and not es_crist:
            if "extra añejo" in nom_l or "milenio" in nom_l:
                return "Tequila - Añejo Tradicional", "Extra Añejo", "Extra Añejo"
            return "Tequila - Añejo Tradicional", "Añejo Tradicional", "Añejo"
        elif es_crist:
            return "Tequila - Añejo Cristalino", "Añejo Cristalino", "Añejo Cristalino"

        return "Tequila - Otros", "Otros", "Otros"

    # -----------------------------------------------------------------------
    # MEZCAL (NOM-070-SCFI)
    # -----------------------------------------------------------------------
    elif cat == "Mezcal" or "mezcal" in nom_l:
        es_silvestre = any(k in nom_l for k in KEYWORDS_SILVESTRES)
        es_rep = "reposado" in nom_l or "rep " in nom_l or "rep." in nom_l
        es_anejo = "añejo" in nom_l or "anejo" in nom_l
        es_crist = "cristalino" in nom_l or "crist " in nom_l or "crist." in nom_l

        if es_silvestre and not es_rep and not es_anejo:
            return "Mezcal - Silvestre", "Silvestre", "Joven Silvestre"
        elif es_crist and es_anejo:
            return "Mezcal - Añejo", "Añejo", "Añejo Cristalino"
        elif es_crist:
            return "Mezcal - Reposado Cristalino", "Reposado Cristalino", "Reposado Cristalino"
        elif es_anejo:
            return "Mezcal - Añejo", "Añejo", "Añejo"
        elif es_rep:
            return "Mezcal - Reposado", "Reposado", "Reposado"
        else:
            return "Mezcal - Espadín Joven", "Espadín Joven", "Joven"

    # -----------------------------------------------------------------------
    # OTROS DESTILADOS Y BEBIDAS
    # -----------------------------------------------------------------------
    elif (
        cat == "Licor de Whisky"
        or "honey" in nom_l
        or "miel" in nom_l
        or ("licor" in nom_l and ("whisky" in nom_l or "whiskey" in nom_l))
    ):
        return "Licor de Whisky - Honey", "Honey Liqueur", "Honey Liqueur"
    elif cat == "Whisky" or "whisky" in nom_l or "whiskey" in nom_l or any(k in nom_l for k in KEYWORDS_BLENDED_WHISKY):
        return "Whisky - Blended Scotch", "Blended Scotch", "Blended Scotch"
    elif cat == "Vino" or "vino" in nom_l:
        return "Vino - Tinto Clericot", "Tinto Clericot", "Tinto Clericot"

    return cat, "General", "General"


def clasificar_categoria(nombre: str) -> Tuple[str, str]:
    """
    Función de compatibilidad para scrapers simples.
    Retorna (categoria_principal, subcategoria).
    """
    cat_base = detectar_categoria_base(nombre)
    _, subcat, _ = clasificar_estricto(nombre, cat_base)
    return cat_base, subcat
