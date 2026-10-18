"""
Cálculo vectorial de métricas financieras por litro, detección de outliers de lujo y filtrado de presupuesto (H25, H32, H37, H41).
"""

import numpy as np
import pandas as pd

from src.analizador.normalizacion import es_producto_paquete
from src.clasificacion import LIMITES_PRESUPUESTO_DASHBOARD, TECHOS_LITRO_OUTLIERS


def calcular_metricas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula:
    - precio_efectivo (unitario real)
    - precio_por_litro: precio_efectivo / (ml / 1000)
    - ahorro_verificable: precio_regular - precio_efectivo
    - porcentaje_ahorro: (ahorro / precio_regular) * 100
    - es_paquete: si es paquete, combo, kit o edición con obsequio
    """
    p_promo = (
        pd.to_numeric(df["precio_promo"], errors="coerce")
        if "precio_promo" in df.columns
        else pd.Series(np.nan, index=df.index)
    )
    p_reg = (
        pd.to_numeric(df["precio_regular"], errors="coerce")
        if "precio_regular" in df.columns
        else pd.Series(np.nan, index=df.index)
    )
    u_promo = (
        pd.to_numeric(df["unidades_promo"], errors="coerce").fillna(1)
        if "unidades_promo" in df.columns
        else pd.Series(1, index=df.index)
    )
    p_tot = (
        pd.to_numeric(df["precio_total_promo"], errors="coerce")
        if "precio_total_promo" in df.columns
        else pd.Series(np.nan, index=df.index)
    )

    cond_multi = (u_promo > 1) & (p_tot > 0)
    cond_promo = p_promo > 0
    cond_reg = p_reg > 0

    df["precio_efectivo"] = np.select(
        [cond_multi, cond_promo, cond_reg],
        [p_tot / u_promo, p_promo, p_reg],
        default=np.nan,
    )

    # Validación de ml > 0 para evitar división por cero
    df["ml"] = pd.to_numeric(df["ml"], errors="coerce").fillna(750)
    df["litros"] = df["ml"] / 1000.0
    df["precio_por_litro"] = np.where(
        (df["litros"] > 0) & pd.notnull(df["precio_efectivo"]) & (df["precio_efectivo"] > 0),
        (df["precio_efectivo"] / df["litros"]).round(2),
        np.nan,
    )

    # Ahorro verificable
    df["precio_regular"] = pd.to_numeric(df["precio_regular"], errors="coerce").fillna(df["precio_efectivo"])
    df["ahorro_verificable"] = (df["precio_regular"] - df["precio_efectivo"]).apply(
        lambda x: max(0.0, round(x, 2)) if pd.notnull(x) else 0.0
    )
    df["porcentaje_ahorro"] = np.where(
        (pd.notnull(df["precio_regular"])) & (df["precio_regular"] > 0),
        ((df["ahorro_verificable"] / df["precio_regular"]) * 100.0).round(1),
        0.0,
    )

    df["es_paquete"] = df.apply(es_producto_paquete, axis=1)

    return df


def marcar_outliers_lujo(df: pd.DataFrame, umbral_multiplicador_mediana: float = 5.0) -> pd.DataFrame:
    """
    Identifica botellas de colección o ultra-lujo que distorsionan análisis estadísticos (H25).
    Marca la columna booleana 'es_outlier_lujo'.
    Un producto se clasifica como outlier de ultra-lujo si:
    1. Su precio por litro supera `umbral_multiplicador_mediana` veces la mediana de su categoría.
    2. Su precio por litro supera techos de consumo familiar (ej. > 3,500 MXN/L en Tequila/Whisky,
       > 3,000 MXN/L en Mezcal, > 1,000 MXN/L en Vino de mesa).
    3. Su precio unitario es exorbitante (> 5,000 MXN) y su precio por litro supera 2,500 MXN/L.
    """
    df = df.copy()
    if "precio_por_litro" not in df.columns or "precio_promo" not in df.columns:
        df["es_outlier_lujo"] = False
        return df

    outlier_mask = pd.Series(False, index=df.index)

    limites_ppl = TECHOS_LITRO_OUTLIERS
    for cat, max_ppl in limites_ppl.items():
        c_mask = (df["categoria"] == cat) & (df["precio_por_litro"] > max_ppl)
        outlier_mask = outlier_mask | c_mask

    if "categoria" in df.columns:
        for cat, sub in df.groupby("categoria"):
            med = sub["precio_por_litro"].median()
            if pd.notnull(med) and med > 0:
                mask_med = (df["categoria"] == cat) & (df["precio_por_litro"] > (med * umbral_multiplicador_mediana))
                outlier_mask = outlier_mask | mask_med

    outlier_mask = outlier_mask | ((df["precio_promo"] > 5000.0) & (df["precio_por_litro"] > 2500.0))
    df["es_outlier_lujo"] = outlier_mask
    return df


def filtrar_catalogo_dashboard(
    df: pd.DataFrame, limites_presupuesto: dict[str, dict[str, float]] | None = None
) -> pd.DataFrame:
    """
    Filtra el catálogo consolidado aplicando los límites de presupuesto por categoría
    y excluyendo explícitamente cualquier outlier de lujo (H32, H37, H41).
    Ordena el resultado por categoría comparable y precio por litro.
    """
    if df.empty:
        return df.copy()

    limites = limites_presupuesto if limites_presupuesto is not None else LIMITES_PRESUPUESTO_DASHBOARD

    cond_list = []
    for cat, limits in limites.items():
        sub_cond = df["categoria"] == cat
        if "max_precio_promo" in limits and "max_precio_por_litro" in limits:
            sub_cond = sub_cond & (
                (df["precio_promo"] <= limits["max_precio_promo"])
                | (df["precio_por_litro"] <= limits["max_precio_por_litro"])
            )
        elif "max_precio_promo" in limits:
            sub_cond = sub_cond & (df["precio_promo"] <= limits["max_precio_promo"])
        elif "max_precio_por_litro" in limits:
            sub_cond = sub_cond & (df["precio_por_litro"] <= limits["max_precio_por_litro"])
        cond_list.append(sub_cond)

    cond_presupuesto = pd.Series(False, index=df.index)
    for c in cond_list:
        cond_presupuesto = cond_presupuesto | c

    mask_outlier = df["es_outlier_lujo"] if "es_outlier_lujo" in df.columns else pd.Series(False, index=df.index)

    df_dash = df[cond_presupuesto & ~mask_outlier].copy()
    if "categoria_comparable" in df_dash.columns and "precio_por_litro" in df_dash.columns:
        df_dash = df_dash.sort_values(by=["categoria_comparable", "precio_por_litro"]).reset_index(drop=True)
    return df_dash
