"""
Detección de duplicados, generación de claves canónicas y arbitraje cross-tienda (H8, H21, H35, H40).
"""

from typing import Optional

import pandas as pd

from src.analizador.metricas_y_outliers import calcular_metricas
from src.analizador.normalizacion import normalizar_texto_clave


def detectar_duplicados(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detecta duplicados intra-tienda y genera claves canónicas cross-tienda (H8).

    - 'es_duplicado': True si la misma tienda cotiza repetidamente el mismo producto y ml.
    - 'clave_comparativa': Clave unificada (producto_normalizado, ml) para comparar entre tiendas.
    - 'es_comparable_cross_tienda': True si el producto existe en 2 o más tiendas distintas.
    - 'num_tiendas_disponibles': Cantidad de tiendas donde se cotiza la misma botella.
    """
    df = df.copy()
    # 1. Duplicados intra-tienda (compatibilidad total)
    df["es_duplicado"] = df.duplicated(subset=["tienda", "producto", "ml"], keep="first")

    # 2. Clave comparativa cross-tienda (H8 / H21 / H35)
    claves = []
    for _, row in df.iterrows():
        prod_norm = normalizar_texto_clave(row.get("producto", ""))
        val_ml = row.get("ml")
        ml_val = 750
        if pd.notnull(val_ml):
            try:
                ml_num = float(val_ml)
                if not pd.isna(ml_num) and ml_num > 0:
                    ml_val = round(ml_num)
            except (ValueError, TypeError):
                ml_val = 750

        # H35: Formato estándar 700ml vs 750ml (650 <= ml <= 800) unificado a 'std'
        vol_tag = "std" if 650 <= ml_val <= 800 else str(ml_val)
        claves.append(f"{prod_norm}_{vol_tag}")
    df["clave_comparativa"] = claves

    conteo_tiendas = df.groupby("clave_comparativa")["tienda"].nunique()
    df["num_tiendas_disponibles"] = df["clave_comparativa"].map(conteo_tiendas)
    df["es_comparable_cross_tienda"] = df["num_tiendas_disponibles"] > 1

    return df


def calcular_grupos_cross_tienda(df: pd.DataFrame) -> dict[str, dict]:
    """
    Precomputa métricas de arbitraje cross-tienda para botellas presentes en 2 o más tiendas (H8 / H35 / H40).
    Devuelve un diccionario clave_comparativa -> datos agregados de arbitraje (tienda_min, tienda_max, ahorro_max, ofertas).
    """
    if "clave_comparativa" not in df.columns or "es_comparable_cross_tienda" not in df.columns:
        df = detectar_duplicados(df)
    if "precio_por_litro" not in df.columns or "precio_efectivo" not in df.columns:
        df = calcular_metricas(df)

    comparables = df[df["es_comparable_cross_tienda"]].copy()
    if comparables.empty:
        return {}

    grupos_cross = {}
    for clave, grp in comparables.groupby("clave_comparativa"):
        tiendas_unicas = grp["tienda"].unique()
        if len(tiendas_unicas) < 2:
            continue

        col_ord = "precio_por_litro" if "precio_por_litro" in grp.columns else "precio_efectivo"
        grp_valid = grp[grp[col_ord] > 0]
        if grp_valid["tienda"].nunique() < 2:
            continue

        if "disponibilidad" in grp_valid.columns:
            grp_disp = grp_valid[grp_valid["disponibilidad"].astype(str).str.lower() != "agotado"]
            idx_min = grp_disp[col_ord].idxmin() if not grp_disp.empty else grp_valid[col_ord].idxmin()
        else:
            idx_min = grp_valid[col_ord].idxmin()
        idx_max = grp_valid[col_ord].idxmax()
        row_min = grp_valid.loc[idx_min]
        row_max = grp_valid.loc[idx_max]

        # Determinar columna de precio base (precio_promo para consolidador o precio_efectivo para analizador)
        col_precio = (
            "precio_promo" if ("precio_promo" in row_min and pd.notnull(row_min["precio_promo"])) else "precio_efectivo"
        )

        p_min = float(row_min[col_precio])
        p_max = float(row_max[col_precio])
        ppl_min = float(row_min["precio_por_litro"]) if "precio_por_litro" in row_min else p_min
        ppl_max = float(row_max["precio_por_litro"]) if "precio_por_litro" in row_max else p_max

        if row_min["ml"] == row_max["ml"]:
            ahorro_max = round(p_max - p_min, 2)
            pct_ahorro = round((ahorro_max / p_max * 100) if p_max > 0 else 0.0, 1)
        else:
            ahorro_por_litro = ppl_max - ppl_min
            ahorro_max = round(ahorro_por_litro * (float(row_min["ml"]) / 1000.0), 2)
            pct_ahorro = round((ahorro_por_litro / ppl_max * 100) if ppl_max > 0 else 0.0, 1)

        ofertas = [
            {
                "tienda": r["tienda"],
                "producto": r["producto"],
                "ml": r["ml"],
                "precio_promo": round(float(r[col_precio]), 2),
                "precio_por_litro": (
                    round(float(r["precio_por_litro"]), 2)
                    if "precio_por_litro" in r
                    else round(float(r[col_precio]), 2)
                ),
                "disponibilidad": r.get("disponibilidad", "disponible"),
                "stock_unidades": (
                    int(r["stock_unidades"])
                    if ("stock_unidades" in r and pd.notnull(r["stock_unidades"]) and str(r["stock_unidades"]).isdigit())
                    else None
                ),
                "url": r.get("url", ""),
            }
            for _, r in grp_valid.iterrows()
        ]

        grupos_cross[clave] = {
            "num_tiendas": len(tiendas_unicas),
            "tiendas_disponibles": sorted(tiendas_unicas.tolist()),
            "producto": row_min["producto"],
            "categoria": row_min.get("categoria", ""),
            "subcategoria": row_min.get("subcategoria", ""),
            "tienda_min": row_min["tienda"],
            "precio_min": round(p_min, 2),
            "precio_por_litro_min": round(ppl_min, 2),
            "ml_min": row_min["ml"],
            "disponibilidad_min": row_min.get("disponibilidad", "disponible"),
            "tienda_max": row_max["tienda"],
            "precio_max": round(p_max, 2),
            "precio_por_litro_max": round(ppl_max, 2),
            "ahorro_max": ahorro_max,
            "porcentaje_ahorro_max": pct_ahorro,
            "ofertas": ofertas,
        }

    return grupos_cross


def obtener_comparativa_cross_tienda(df: pd.DataFrame) -> pd.DataFrame:
    """
    Genera tabla de arbitraje de precios para botellas presentes en múltiples tiendas (H8 / H35 / H40).
    Calcula tienda más barata, más cara y el ahorro máximo por producto, priorizando
    precio por litro para formatos estándar unificados (700ml vs 750ml).
    Unifica la lógica de cálculo cross-tienda consumiendo calcular_grupos_cross_tienda().
    """
    grupos_cross = calcular_grupos_cross_tienda(df)
    if not grupos_cross:
        return pd.DataFrame()

    resumen = [
        {
            "clave_comparativa": clave,
            "producto": info["producto"],
            "categoria": info["categoria"],
            "subcategoria": info.get("subcategoria", ""),
            "ml": info["ml_min"],
            "tiendas_disponibles": info["tiendas_disponibles"],
            "tienda_mas_barata": info["tienda_min"],
            "precio_minimo": info["precio_min"],
            "tienda_mas_cara": info["tienda_max"],
            "precio_maximo": info["precio_max"],
            "ahorro_maximo": info["ahorro_max"],
            "porcentaje_ahorro_maximo": info["porcentaje_ahorro_max"],
        }
        for clave, info in grupos_cross.items()
    ]

    df_comp = pd.DataFrame(resumen)
    if not df_comp.empty:
        df_comp = df_comp.sort_values(by="ahorro_maximo", ascending=False).reset_index(drop=True)
    return df_comp


def enriquecer_registros_cross_tienda(
    df: pd.DataFrame,
    grupos_cross: Optional[dict[str, dict]] = None,
    cols: Optional[list[str]] = None,
) -> list[dict]:
    """
    Enriquece cada registro de un DataFrame con las métricas cross-tienda (H8 / H35 / H40)
    para el dashboard interactivo y la exportación JSON.
    """
    if "clave_comparativa" not in df.columns or "es_comparable_cross_tienda" not in df.columns:
        df = detectar_duplicados(df)
    if "precio_por_litro" not in df.columns or "precio_efectivo" not in df.columns:
        df = calcular_metricas(df)

    if grupos_cross is None:
        grupos_cross = calcular_grupos_cross_tienda(df)

    records = []
    for _, row in df.iterrows():
        rec = {}
        if cols:
            for c in cols:
                val = row.get(c, "")
                rec[c] = "" if pd.isna(val) else val
        else:
            rec = {k: ("" if pd.isna(v) else v) for k, v in row.items()}

        rec["es_paquete"] = bool(row.get("es_paquete", False))
        clave = row.get("clave_comparativa", "")
        rec["clave_comparativa"] = clave

        col_p = "precio_promo" if ("precio_promo" in row and pd.notnull(row["precio_promo"])) else "precio_efectivo"
        p_actual = round(float(row.get(col_p, 0.0)), 2)
        p_litro_actual = round(float(row.get("precio_por_litro", 0.0)), 2)

        if clave in grupos_cross:
            info = grupos_cross[clave]
            rec["es_comparable_cross_tienda"] = True
            rec["num_tiendas_cross"] = info["num_tiendas"]
            rec["tienda_mas_barata"] = info["tienda_min"]
            rec["precio_minimo_cross"] = info["precio_min"]
            rec["precio_por_litro_minimo_cross"] = info["precio_por_litro_min"]
            rec["tienda_mas_cara"] = info["tienda_max"]
            rec["precio_maximo_cross"] = info["precio_max"]
            rec["ahorro_maximo_cross"] = info["ahorro_max"]

            p_litro_min = info["precio_por_litro_min"]

            # H35: El mejor precio se determina por precio por litro (+ margen de 5 centavos para empates)
            # Descartando precios fantasma si el producto actual está agotado y hay alternativa en existencia
            disp_actual = str(row.get("disponibilidad", "disponible")).lower()
            if disp_actual == "agotado" and info.get("disponibilidad_min", "disponible") != "agotado":
                rec["es_precio_mas_bajo"] = False
            else:
                rec["es_precio_mas_bajo"] = bool(p_litro_actual <= p_litro_min + 0.05)

            if rec["es_precio_mas_bajo"]:
                rec["diferencia_vs_minimo"] = 0.0
            else:
                if row["ml"] == info.get("ml_min", row["ml"]):
                    dif = p_actual - info["precio_min"]
                    rec["diferencia_vs_minimo"] = round(
                        dif if dif > 0 else (p_litro_actual - p_litro_min) * (float(row["ml"]) / 1000.0), 2
                    )
                else:
                    rec["diferencia_vs_minimo"] = round((p_litro_actual - p_litro_min) * (float(row["ml"]) / 1000.0), 2)

            rec["ofertas_cross_tienda"] = [
                {
                    "tienda": of["tienda"],
                    "producto": of["producto"],
                    "ml": of["ml"],
                    "precio_promo": of["precio_promo"],
                    "precio_por_litro": of["precio_por_litro"],
                    "disponibilidad": of.get("disponibilidad", "disponible"),
                    "stock_unidades": of.get("stock_unidades"),
                    "url": of["url"],
                    "diferencia": round(
                        (p_actual - of["precio_promo"])
                        if row["ml"] == of["ml"]
                        else (p_litro_actual - of["precio_por_litro"]) * (float(row["ml"]) / 1000.0),
                        2,
                    ),
                    "es_mejor_precio": bool(
                        of["precio_por_litro"] < p_litro_actual - 0.05
                        and str(of.get("disponibilidad", "disponible")).lower() != "agotado"
                    ),
                }
                for of in info["ofertas"]
                if of["tienda"] != row["tienda"]
            ]
        else:
            rec["es_comparable_cross_tienda"] = False
            rec["num_tiendas_cross"] = 1
            rec["tienda_mas_barata"] = row["tienda"]
            rec["precio_minimo_cross"] = p_actual
            rec["precio_por_litro_minimo_cross"] = p_litro_actual
            rec["tienda_mas_cara"] = row["tienda"]
            rec["precio_maximo_cross"] = p_actual
            rec["ahorro_maximo_cross"] = 0.0
            rec["es_precio_mas_bajo"] = bool(str(row.get("disponibilidad", "disponible")).lower() != "agotado")
            rec["diferencia_vs_minimo"] = 0.0
            rec["ofertas_cross_tienda"] = []

        records.append(rec)

    return records
