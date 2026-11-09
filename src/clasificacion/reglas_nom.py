"""
Detección y Clasificación Estricta bajo NOM-006 (Tequila), NOM-070 (Mezcal), Whisky y Vinos (H1).
"""

from typing import Any, Optional, Tuple, Union

from src.clasificacion.constantes import (
    KEYWORDS_BLENDED_WHISKY,
    KEYWORDS_SILVESTRES,
    MARCAS_REPOSADO_CRISTALINO_POR_NORMA,
)

REGLAS_AGAVE_MEZCAL: tuple[tuple[tuple[tuple[str, ...], ...], str], ...] = (
    # Cada regla contiene los grupos de sinónimos que deben aparecer (en cualquier orden)
    # y el resultado. El orden de la tabla define la precedencia.
    ((("cosecha salvaje",),), "Ensamble Silvestre Tobalá-Mexicano (A. potatorum / A. rhodacantha)"),
    (
        (("mexicano",), ("tobalá", "tobala")),
        "Ensamble Silvestre Tobalá-Mexicano (A. potatorum / A. rhodacantha)",
    ),
    ((("espadín", "espadin"), ("tobalá", "tobala")), "Ensamble Espadín-Tobalá"),
    ((("mexicano",),), "Mexicano silvestre (A. rhodacantha)"),
    ((("cuishe", "cuixe"),), "Cuishe silvestre (A. karwinskii)"),
    ((("tobalá", "tobala"),), "Tobalá silvestre (A. potatorum)"),
    ((("cupreata",),), "Cupreata silvestre (A. cupreata)"),
    ((("tepeztate", "tepextate"),), "Tepeztate silvestre (A. marmorata)"),
    ((("arroqueño", "arroqueno"),), "Arroqueño silvestre (A. americana)"),
    ((("cenizo",),), "Cenizo silvestre (A. durangensis)"),
    ((("salmiana",),), "Salmiana silvestre"),
    ((("jabalí", "jabali"),), "Jabalí silvestre (A. convallis)"),
    ((("barril",),), "Barril silvestre (A. karwinskii)"),
    ((("madrecuishe", "madrecuixe"),), "Madrecuishe silvestre (A. karwinskii)"),
    ((("papalometl",),), "Papalometl silvestre (A. potatorum)"),
    ((("espadín", "espadin"),), "Espadín (A. angustifolia)"),
)


def clasificar_agave_mezcal(nombre: str) -> str:
    """
    Identifica la especie de agave o ensamble para mezcales según la NOM-070.
    """
    nom_l = str(nombre).lower()
    for grupos_sinonimos, categoria in REGLAS_AGAVE_MEZCAL:
        if all(any(sinonimo in nom_l for sinonimo in grupo) for grupo in grupos_sinonimos):
            return categoria
    return "Agave mezcalero (NOM-070)"


def detectar_categoria_base(nombre: str) -> str:
    """Infiere la macro-categoría de bebida a partir del nombre del producto."""
    nom_l = str(nombre).lower()
    if "tequila" in nom_l:
        return "Tequila"
    if "mezcal" in nom_l:
        return "Mezcal"
    # Licor Honey o Apple de marcas de whisky
    if (
        "jack daniel" in nom_l
        or "passport" in nom_l
        or "jim beam" in nom_l
        or "wild turkey" in nom_l
        or "william lawson" in nom_l
    ) and ("honey" in nom_l or "miel" in nom_l or "apple" in nom_l or "manzana" in nom_l):
        return "Licor de Whisky"
    if ("honey" in nom_l or "apple" in nom_l) and ("whisky" in nom_l or "whiskey" in nom_l):
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


def _normalizar_entrada_clasificacion(row_o_nombre: Union[dict, Any, str], categoria: Optional[str]) -> tuple[str, str]:
    """Extrae (nombre, categoría) desde un str, un dict/pd.Series o una fila indexable."""
    if isinstance(row_o_nombre, str):
        nom = row_o_nombre.strip()
        return nom, categoria or detectar_categoria_base(nom)
    if hasattr(row_o_nombre, "get"):
        nom = str(row_o_nombre.get("producto", "")).strip()
        cat = str(row_o_nombre.get("categoria", "") or categoria or detectar_categoria_base(nom)).strip()
        return nom, cat
    nom = str(row_o_nombre["producto"]).strip()
    cat = str(row_o_nombre.get("categoria", categoria or detectar_categoria_base(nom))).strip()
    return nom, cat


def _indicadores_tequila(nom_l: str) -> tuple[bool, bool, bool]:
    """Devuelve (es_reposado, es_cristalino, es_añejo) para un nombre de tequila."""
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
    return es_rep, es_crist, es_anejo


def _es_tequila_blanco(nom_l: str, es_rep: bool, es_anejo: bool) -> bool:
    return ("plata" in nom_l or "blanco" in nom_l or "silver" in nom_l) and not (es_anejo or es_rep)


def _es_reposado_cristalino_por_norma(nom_l: str, es_crist: bool, es_anejo: bool) -> bool:
    return (
        es_crist
        and any(m in nom_l for m in MARCAS_REPOSADO_CRISTALINO_POR_NORMA)
        and not (es_anejo or "ultra añejo" in nom_l)
    )


def _clasificar_don_ramon(nom_l: str) -> Optional[Tuple[str, str, str]]:
    if "añejo cristalino" in nom_l or ("añejo" in nom_l and ("platinium" in nom_l or "cristalino" in nom_l)):
        return "Tequila - Añejo Cristalino", "Añejo Cristalino", "Añejo Cristalino"
    if "reposado cristalino" in nom_l or ("reposado" in nom_l and ("platinium" in nom_l or "cristalino" in nom_l)):
        return "Tequila - Reposado Cristalino", "Reposado Cristalino", "Reposado Cristalino"
    if "reposado" in nom_l:
        return "Tequila - Reposado Tradicional", "Reposado", "Reposado"
    if "añejo" in nom_l or "dark" in nom_l:
        return "Tequila - Añejo Tradicional", "Añejo Tradicional", "Añejo"
    return None


def _tequila_casos_especiales(nom_l: str) -> Optional[Tuple[str, str, str]]:
    """Casos con regla de marca/nombre propio, en el mismo orden de precedencia histórico."""
    es_rep, es_crist, es_anejo = _indicadores_tequila(nom_l)

    if _es_tequila_blanco(nom_l, es_rep, es_anejo):
        return "Tequila - Blanco / Plata", "Blanco", "Blanco"
    if "don ramón plata" in nom_l or "don ramon plata" in nom_l:
        return "Tequila - Blanco / Plata", "Blanco", "Blanco"
    if "don julio 70" in nom_l or "don julio 70 añejo" in nom_l:
        return "Tequila - Añejo Cristalino", "Añejo Cristalino", "Añejo Cristalino"
    if "don ramón" in nom_l or "don ramon" in nom_l:
        resultado = _clasificar_don_ramon(nom_l)
        if resultado is not None:
            return resultado
    if _es_reposado_cristalino_por_norma(nom_l, es_crist, es_anejo):
        return "Tequila - Reposado Cristalino", "Reposado Cristalino", "Reposado Cristalino"
    if "dobel diamante" in nom_l or "maestro dobel diamante" in nom_l:
        return "Tequila - Añejo Cristalino", "Añejo Cristalino", "Añejo Cristalino"
    return None


def _tequila_reglas_generales(nom_l: str) -> Tuple[str, str, str]:
    es_rep, es_crist, es_anejo = _indicadores_tequila(nom_l)

    if es_rep and es_crist and not es_anejo:
        return "Tequila - Reposado Cristalino", "Reposado Cristalino", "Reposado Cristalino"
    if es_rep and not es_crist and not es_anejo:
        return "Tequila - Reposado Tradicional", "Reposado", "Reposado"
    if es_anejo and es_crist:
        return "Tequila - Añejo Cristalino", "Añejo Cristalino", "Añejo Cristalino"
    if es_anejo:
        if "extra añejo" in nom_l or "milenio" in nom_l:
            return "Tequila - Añejo Tradicional", "Extra Añejo", "Extra Añejo"
        return "Tequila - Añejo Tradicional", "Añejo Tradicional", "Añejo"
    if es_crist:
        return "Tequila - Añejo Cristalino", "Añejo Cristalino", "Añejo Cristalino"
    return "Tequila - Otros", "Otros", "Otros"


def _clasificar_mezcal(nom_l: str) -> Tuple[str, str, str]:
    es_silvestre = any(k in nom_l for k in KEYWORDS_SILVESTRES)
    es_rep = "reposado" in nom_l or "rep " in nom_l or "rep." in nom_l
    es_anejo = "añejo" in nom_l or "anejo" in nom_l
    es_crist = "cristalino" in nom_l or "crist " in nom_l or "crist." in nom_l

    if es_silvestre and not es_rep and not es_anejo:
        return "Mezcal - Silvestre", "Silvestre", "Joven Silvestre"
    if es_crist and es_anejo:
        return "Mezcal - Añejo", "Añejo", "Añejo Cristalino"
    if es_crist:
        return "Mezcal - Reposado Cristalino", "Reposado Cristalino", "Reposado Cristalino"
    if es_anejo:
        return "Mezcal - Añejo", "Añejo", "Añejo"
    if es_rep:
        return "Mezcal - Reposado", "Reposado", "Reposado"
    return "Mezcal - Espadín Joven", "Espadín Joven", "Joven"


def _es_licor_whisky(nom_l: str, cat: str) -> bool:
    return (
        cat == "Licor de Whisky"
        or "honey" in nom_l
        or "miel" in nom_l
        or (("jack daniel" in nom_l or "jack daniel's" in nom_l) and ("apple" in nom_l or "manzana" in nom_l))
        or ("licor" in nom_l and ("whisky" in nom_l or "whiskey" in nom_l))
    )


def _es_whisky(nom_l: str, cat: str) -> bool:
    return (
        cat == "Whisky" or "whisky" in nom_l or "whiskey" in nom_l or any(k in nom_l for k in KEYWORDS_BLENDED_WHISKY)
    )


def _es_vino(nom_l: str, cat: str) -> bool:
    return cat == "Vino" or "vino" in nom_l


def clasificar_estricto(row_o_nombre: Union[dict, Any, str], categoria: Optional[str] = None) -> Tuple[str, str, str]:
    """
    Clasifica estrictamente un producto bajo las normas oficiales y el estándar del proyecto.

    Acepta:
    - Un dict o pd.Series con claves 'producto' y 'categoria'
    - Un nombre de producto (str) y una categoría opcional (str)

    Retorna:
    - (categoria_comparable, subcategoria, clase)
    """
    nom, cat = _normalizar_entrada_clasificacion(row_o_nombre, categoria)
    nom_l = nom.lower()

    if cat == "Tequila" or "tequila" in nom_l:
        caso_especial = _tequila_casos_especiales(nom_l)
        return caso_especial if caso_especial is not None else _tequila_reglas_generales(nom_l)

    if cat == "Mezcal" or "mezcal" in nom_l:
        return _clasificar_mezcal(nom_l)

    if _es_licor_whisky(nom_l, cat):
        return "Licor de Whisky - Honey", "Honey Liqueur", "Honey Liqueur"
    if _es_whisky(nom_l, cat):
        return "Whisky - Blended Scotch", "Blended Scotch", "Blended Scotch"
    if _es_vino(nom_l, cat):
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
