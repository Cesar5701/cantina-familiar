"""
Script maestro para:
1. Consolidar los catálogos scrapeados de las 5 tiendas:
   - Bodegas Alianza (data/scraped_alianza_completo.csv)
   - Sam's Club (data/scraped_sams.csv)
   - Walmart (data/scraped_walmart.csv)
   - Chedraui (data/scraped_chedraui.csv)
   - Soriana (data/scraped_soriana.csv)
2. Auditar y corregir clasificaciones NOM de Tequila, Mezcal, Whisky, Licor Honey y Vino.
3. Calcular métricas normalizadas por litro (src/analizador.py) y actualizar:
   - data/catalogo_completo_consolidado.csv
   - data/ranking_completo_general.csv
   - data/dashboard_data.json
"""

import os
import sys

import pandas as pd

RAIZ_PROYECTO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if RAIZ_PROYECTO not in sys.path:
    sys.path.insert(0, RAIZ_PROYECTO)

from src.analizador import (
    calcular_metricas,
    detectar_duplicados,
    marcar_outliers_lujo,
    normalizar_texto_clave,
    validar_esquema_y_rangos,
)
from src.io_utils import guardar_csv_atomico, guardar_json_atomico
from src.logger import get_logger

logger = get_logger("actualizador")


from src.clasificacion import (
    clasificar_estricto,
    corregir_ml_producto,
    normalizar_medidas_en_nombre,
)


def actualizar_todo(archivos_fuente: list[str] | None = None, carpeta_salida: str = "data") -> list[dict]:
    if archivos_fuente is None:
        archivos_fuente = [
            "data/scraped_alianza_completo.csv",
            "data/scraped_sams.csv",
            "data/scraped_walmart.csv",
            "data/scraped_chedraui.csv",
            "data/scraped_soriana.csv",
        ]

    dfs = []
    for ruta in archivos_fuente:
        if os.path.exists(ruta):
            df_part = pd.read_csv(ruta)
            logger.info(f"Cargado {ruta}: {len(df_part)} filas")
            dfs.append(df_part)

    if not dfs:
        logger.warning("No se encontraron archivos fuente para consolidar.")
        return []

    df = pd.concat(dfs, ignore_index=True)

    # Normalizar medidas en los nombres de producto (Fase 1)
    df["producto"] = df["producto"].map(normalizar_medidas_en_nombre)

    # Limpiar artículos que sean latas RTD, cajas mayoristas o miniaturas (< 650 ml)
    df["ml"] = [corregir_ml_producto(row["producto"], row["ml"]) for _, row in df.iterrows()]
    df = df[df["ml"] >= 650].copy()

    mask_excluir = (
        df["producto"]
        .str.lower()
        .str.contains(
            "lemonade|6 latas|4 pachitas|6 pzas|paquete de 3|caja de 3|caja de 6|caja de 12|estuche vacío|crema de|aguamiel|bacanora",
            regex=True,
            na=False,
        )
    )
    df = df[~mask_excluir].copy()

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

    # Eliminar Tequilas que sean Reposado Tradicional, Blanco/Plata u Otros (solo conservar Añejo Cristalino, Reposado Cristalino y Añejo Tradicional)
    categorias_excluidas = ["Tequila - Reposado Tradicional", "Tequila - Blanco / Plata", "Tequila - Otros"]
    df = df[~df["categoria_comparable"].isin(categorias_excluidas)].copy()

    # En Licor de Whisky - Honey, asegurar que sea realmente Honey
    mask_honey_invalido = (df["categoria_comparable"] == "Licor de Whisky - Honey") & (
        ~df["producto"].str.lower().str.contains("honey|miel", regex=True, na=False)
    )
    df = df[~mask_honey_invalido].copy()

    # Deduplicar por (tienda, producto normalizado, ml) usando normalizar_texto_clave (H23)
    df["prod_key"] = df["producto"].apply(normalizar_texto_clave)
    df = (
        df.drop_duplicates(subset=["tienda", "prod_key", "ml"], keep="first")
        .drop(columns=["prod_key"])
        .reset_index(drop=True)
    )

    # Calcular métricas con src/analizador.py
    df = detectar_duplicados(df)
    df = calcular_metricas(df)

    # Validación de esquema y rangos (H9 / H22)
    df, reporte_val = validar_esquema_y_rangos(df)
    anomalias = (
        reporte_val.get("anomalias_volumen_ml", 0)
        + reporte_val.get("anomalias_graduacion_abv", 0)
        + reporte_val.get("registros_sin_precio", 0)
    )
    logger.info(
        f"Auditoría de datos: {reporte_val['registros_validos']}/{reporte_val['total_registros']} registros válidos "
        f"({anomalias} anomalías detectadas y filtradas)"
    )
    # Filtrar activamente registros inválidos para que no contaminen rankings ni dashboard
    df = df[df["datos_validos"]].copy().reset_index(drop=True)

    # Identificar y marcar outliers de ultra-lujo (H25)
    df = marcar_outliers_lujo(df)
    n_outliers = int(df["es_outlier_lujo"].sum())
    logger.info(f"Detección de ultra-lujo: {n_outliers} botellas marcadas como outliers fuera de alcance familiar")

    # Guardar catálogo completo con trazabilidad de outliers (H10 / H25)
    guardar_csv_atomico(df, os.path.join(carpeta_salida, "catalogo_completo_consolidado.csv"))

    # Guardar ranking general limpio de outliers para comparativas fiables (H25)
    df_ranking = df[~df["es_outlier_lujo"]].sort_values(by=["categoria", "precio_por_litro"]).reset_index(drop=True)
    guardar_csv_atomico(df_ranking, os.path.join(carpeta_salida, "ranking_completo_general.csv"))

    # Filtrar para catálogo relevante de la cantina familiar (descartar botellas ultra-lujo > $2,000)
    cond = (
        ((df["categoria"] == "Tequila") & (df["precio_promo"] <= 1950))
        | ((df["categoria"] == "Mezcal") & (df["precio_promo"] <= 1500))
        | ((df["categoria"] == "Whisky") & (df["precio_promo"] <= 1750))
        | ((df["categoria"] == "Licor de Whisky") & (df["precio_promo"] <= 950))
        | ((df["categoria"] == "Vino") & ((df["precio_por_litro"] <= 350) | (df["precio_promo"] <= 260)))
    )
    df_dash = df[cond].copy()
    df_dash = df_dash.sort_values(by=["categoria_comparable", "precio_por_litro"]).reset_index(drop=True)

    cols = [
        "tienda",
        "producto",
        "marca",
        "categoria",
        "subcategoria",
        "clase",
        "categoria_comparable",
        "ml",
        "precio_promo",
        "precio_regular",
        "precio_por_litro",
        "ahorro_verificable",
        "porcentaje_ahorro",
        "disponibilidad",
        "url",
        "especie_agave",
        "condiciones",
    ]
    for c in cols:
        if c not in df_dash.columns:
            df_dash[c] = ""

    # Precomputar métricas cross-tienda para el frontend (H8)
    grupos_cross = {}
    for clave, grp in df_dash.groupby("clave_comparativa"):
        tiendas_unicas = grp["tienda"].unique()
        if len(tiendas_unicas) >= 2:
            idx_min = grp["precio_promo"].idxmin()
            idx_max = grp["precio_promo"].idxmax()
            row_min = grp.loc[idx_min]
            row_max = grp.loc[idx_max]
            grupos_cross[clave] = {
                "num_tiendas": len(tiendas_unicas),
                "tienda_min": row_min["tienda"],
                "precio_min": round(float(row_min["precio_promo"]), 2),
                "tienda_max": row_max["tienda"],
                "precio_max": round(float(row_max["precio_promo"]), 2),
                "ahorro_max": round(float(row_max["precio_promo"] - row_min["precio_promo"]), 2),
                "ofertas": [
                    {
                        "tienda": r["tienda"],
                        "producto": r["producto"],
                        "precio_promo": round(float(r["precio_promo"]), 2),
                        "precio_por_litro": round(float(r["precio_por_litro"]), 2),
                        "url": r["url"],
                    }
                    for _, r in grp.iterrows()
                ],
            }

    records = []
    for _, row in df_dash.iterrows():
        rec = {}
        for c in cols:
            val = row.get(c, "")
            rec[c] = "" if pd.isna(val) else val

        clave = row.get("clave_comparativa", "")
        rec["clave_comparativa"] = clave

        if clave in grupos_cross:
            info = grupos_cross[clave]
            rec["es_comparable_cross_tienda"] = True
            rec["num_tiendas_cross"] = info["num_tiendas"]
            rec["tienda_mas_barata"] = info["tienda_min"]
            rec["precio_minimo_cross"] = info["precio_min"]
            rec["tienda_mas_cara"] = info["tienda_max"]
            rec["precio_maximo_cross"] = info["precio_max"]
            rec["ahorro_maximo_cross"] = info["ahorro_max"]
            p_actual = round(float(row["precio_promo"]), 2)
            rec["es_precio_mas_bajo"] = bool(p_actual <= info["precio_min"] + 0.01)
            rec["diferencia_vs_minimo"] = round(p_actual - info["precio_min"], 2)
            rec["ofertas_cross_tienda"] = [
                {
                    "tienda": of["tienda"],
                    "producto": of["producto"],
                    "precio_promo": of["precio_promo"],
                    "precio_por_litro": of["precio_por_litro"],
                    "url": of["url"],
                    "diferencia": round(p_actual - of["precio_promo"], 2),
                    "es_mejor_precio": bool(of["precio_promo"] < p_actual - 0.01),
                }
                for of in info["ofertas"]
                if of["tienda"] != row["tienda"]
            ]
        else:
            rec["es_comparable_cross_tienda"] = False
            rec["num_tiendas_cross"] = 1
            rec["tienda_mas_barata"] = row["tienda"]
            p_actual = round(float(row["precio_promo"]), 2)
            rec["precio_minimo_cross"] = p_actual
            rec["tienda_mas_cara"] = row["tienda"]
            rec["precio_maximo_cross"] = p_actual
            rec["ahorro_maximo_cross"] = 0.0
            rec["es_precio_mas_bajo"] = True
            rec["diferencia_vs_minimo"] = 0.0
            rec["ofertas_cross_tienda"] = []

        records.append(rec)

    guardar_json_atomico(records, os.path.join(carpeta_salida, "dashboard_data.json"))

    logger.info(f"Total registros guardados en dashboard_data.json: {len(records)}")
    logger.info(f"Productos comparables entre 2 o más tiendas: {len(grupos_cross)} etiquetas")
    logger.info("Distribución por Tienda:")
    for t, cnt in df_dash["tienda"].value_counts().items():
        logger.info(f"  - {t}: {cnt}")
    logger.info("Distribución por Categoría Comparable:")
    for cat, cnt in df_dash["categoria_comparable"].value_counts().items():
        logger.info(f"  - {cat}: {cnt}")

    return records


if __name__ == "__main__":
    actualizar_todo()
