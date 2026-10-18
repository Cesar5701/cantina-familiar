"""
Filtrado de mercancía no bebible, etiquetado de promociones y sincronización de catálogos (H41).
"""

import re
from typing import Optional

import pandas as pd

from src.clasificacion.constantes import (
    CATEGORIAS_COMPARABLES_VALIDAS,
    KEYWORDS_BLENDED_WHISKY,
)
from src.clasificacion.reglas_nom import clasificar_agave_mezcal, clasificar_estricto
from src.clasificacion.volumen_y_precios import extraer_ml


def es_mercancia_o_no_bebible(nombre: str, ml: Optional[int] = None) -> bool:
    """
    Identifica si un producto es mercancía física (vasos, copas, playeras, hieleras),
    alimentos ajenos (sal sola, chocolates, vinagres) o presentaciones no bebibles.

    Distingue y permite combos con botellas completas de licor (ml >= 650) que incluyan
    artículos de obsequio (ej. '+ 2 Vasos + Sal', 'C/Vaso Balón', 'kit con vasos').
    """
    if not nombre:
        return True
    nom_l = str(nombre).lower().strip()

    # 1. Artículos que son inherentemente mercancía pura o comida ajena
    mercancia_pura = [
        "playera",
        "gorra",
        "hielera",
        "estuche vacío",
        "sacacorchos",
        "destapador",
        "decantador",
        "licorera",
        "lata 180",
        "chocolate",
        "bombón",
        "bombon",
        "pastel",
        "galleta",
        "gomita",
        "dulce de ",
        "dulces ",
        "carne",
        "queso",
        "jamon",
        "jamón",
        "chorizo",
        "salchicha",
        "aderezo",
        "aceite",
        "mostaza",
        "mermelada",
        "vinagre",
        "salsa tabasco",
        "salsa inglesa",
    ]
    if any(m in nom_l for m in mercancia_pura):
        return True

    # 2. Artículos que inician directamente como cristalería o botanas/sales sueltas
    prefijos_cristaleria = (
        "vaso ",
        "vasos ",
        "copa ",
        "copas ",
        "caballito ",
        "caballitos ",
        "tarro ",
        "tarros ",
        "set de ",
        "juego de ",
        "sal de ",
        "sal con ",
        "papas ",
    )
    if nom_l.startswith(prefijos_cristaleria):
        return True

    # 3. Detectar si contiene palabras de cristalería o accesorios en el cuerpo del nombre
    es_cristaleria_o_combo = any(
        w in nom_l for w in ["vaso", "copa", "caballito", "sal de ", "sal con ", "termo", "porta vaso"]
    )
    if es_cristaleria_o_combo:
        vol = ml if ml is not None else extraer_ml(nombre)
        tiene_categoria_licor = any(cat in nom_l for cat in ["tequila", "mezcal", "whisky", "whiskey", "vino"]) or any(
            k in nom_l for k in KEYWORDS_BLENDED_WHISKY
        )
        if vol >= 650 and tiene_categoria_licor:
            return False
        return True

    return False


def generar_etiqueta_condicion(nombre: str, precio_regular: float, precio_promo: float) -> str:
    """
    Genera la descripción de condiciones comerciales detectando si el producto
    incluye accesorios u obsequios (vasos, copas, sal, kits promocionales).
    """
    nom_l = str(nombre).lower()
    es_promo_precio = precio_regular > precio_promo

    # Detectar obsequios en el empaque
    detalles = []
    if "vaso" in nom_l:
        m_v = re.search(r"(\d+)\s*vasos?", nom_l)
        detalles.append(f"{m_v.group(1)} Vasos" if m_v else ("Vasos" if "vasos" in nom_l else "Vaso"))
    if "copa" in nom_l:
        m_c = re.search(r"(\d+)\s*copas?", nom_l)
        detalles.append(f"{m_c.group(1)} Copas" if m_c else ("Copas" if "copas" in nom_l else "Copa"))
    if "sal" in nom_l and any(k in nom_l for k in ["+ sal", "c/sal", "con sal", "y sal"]):
        detalles.append("Sal")
    if "kit" in nom_l:
        detalles.append("Kit mezcalero" if "mezcal" in nom_l else "Kit coctelería")
    if "termo" in nom_l:
        detalles.append("Termo")
    if "porta vaso" in nom_l or "portavaso" in nom_l:
        detalles.append("Portavasos")

    if detalles:
        obs_str = " + ".join(detalles)
        if es_promo_precio:
            return f"Descuento Web + 🎁 Obsequio ({obs_str})"
        return f"🎁 Edición con obsequio ({obs_str})"

    if es_promo_precio:
        return "Descuento directo Aniversario Web"
    return "Precio regular catálogo"


def sincronizar_clasificacion_catalogo(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica clasificación estricta NOM, sincroniza categorías con categorías comparables,
    clasifica especies de agave en mezcal, restringe a categorías permitidas del alcance
    familiar, depura falsos Honey en licores y enriquece condiciones de obsequio (H41).
    """
    if df is None or getattr(df, "empty", True):
        return df.copy() if hasattr(df, "copy") else df

    df = df.copy()

    # Clasificación estricta NOM
    resultados = df.apply(clasificar_estricto, axis=1)
    df["categoria_comparable"] = [r[0] for r in resultados]
    df["subcategoria"] = [r[1] for r in resultados]
    df["clase"] = [r[2] for r in resultados]

    # Sincronizar columna categoria consistente con categoria_comparable
    df.loc[df["categoria_comparable"] == "Licor de Whisky - Honey", "categoria"] = "Licor de Whisky"
    df.loc[df["categoria_comparable"] == "Whisky - Blended Scotch", "categoria"] = "Whisky"
    df.loc[df["categoria_comparable"] == "Vino - Tinto Clericot", "categoria"] = "Vino"
    df.loc[df["categoria_comparable"].str.startswith("Tequila"), "categoria"] = "Tequila"
    df.loc[df["categoria_comparable"].str.startswith("Mezcal"), "categoria"] = "Mezcal"

    # Sincronizar especie_agave para Mezcales usando clasificar_agave_mezcal
    mask_mezcal = df["categoria"] == "Mezcal"
    if mask_mezcal.any():
        df.loc[mask_mezcal, "especie_agave"] = df.loc[mask_mezcal, "producto"].apply(clasificar_agave_mezcal)

    # Eliminar Tequilas que sean Reposado Tradicional, Blanco/Plata u Otros (solo conservar categorías válidas del alcance familiar)
    categorias_excluidas = {"Tequila - Reposado Tradicional", "Tequila - Blanco / Plata", "Tequila - Otros"}
    categorias_permitidas = set(CATEGORIAS_COMPARABLES_VALIDAS) - categorias_excluidas
    df = df[df["categoria_comparable"].isin(categorias_permitidas)].copy()

    # En Licor de Whisky - Honey, asegurar que sea realmente Honey
    mask_honey_invalido = (df["categoria_comparable"] == "Licor de Whisky - Honey") & (
        ~df["producto"].str.lower().str.contains("honey|miel", regex=True, na=False)
    )
    df = df[~mask_honey_invalido].copy()

    # Enriquecer condiciones con etiqueta de obsequio si incluye regalos o cristalería
    for idx, row in df.iterrows():
        nom_l = str(row["producto"]).lower()
        if any(k in nom_l for k in ["vaso", "copa", "sal", "termo", "kit"]):
            cond_actual = str(row.get("condiciones", ""))
            if "🎁" not in cond_actual:
                nueva_cond = generar_etiqueta_condicion(
                    str(row["producto"]), float(row["precio_regular"]), float(row["precio_promo"])
                )
                if "🎁" in nueva_cond:
                    df.at[idx, "condiciones"] = nueva_cond

    return df
