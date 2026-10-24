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
    calcular_grupos_cross_tienda,
    calcular_metricas,
    detectar_duplicados,
    enriquecer_registros_cross_tienda,
    filtrar_catalogo_dashboard,
    marcar_outliers_lujo,
    normalizar_texto_clave,
    validar_esquema_y_rangos,
)
from src.clasificacion import (
    LIMITES_PRESUPUESTO_DASHBOARD,
    corregir_ml_producto,
    normalizar_medidas_en_nombre,
    sincronizar_clasificacion_catalogo,
)
from src.io_utils import guardar_csv_atomico, guardar_json_atomico
from src.logger import get_logger

logger = get_logger("actualizador")


def actualizar_todo(archivos_fuente: list[str] | None = None, carpeta_salida: str = "data") -> list[dict]:
    if archivos_fuente is None:
        archivos_fuente = [
            "data/scraped_alianza_completo.csv",
            "data/scraped_sams.csv",
            "data/scraped_walmart.csv",
            "data/scraped_chedraui.csv",
            "data/scraped_soriana.csv",
            "data/scraped_costco.csv",
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

    # Clasificación estricta NOM y sincronización del catálogo familiar (H41)
    df = sincronizar_clasificacion_catalogo(df)

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

    # Filtrar para catálogo relevante de la cantina familiar según límites centralizados (H32, H37, H41)
    df_dash = filtrar_catalogo_dashboard(df, LIMITES_PRESUPUESTO_DASHBOARD)

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
        "es_paquete",
    ]
    for c in cols:
        if c not in df_dash.columns:
            df_dash[c] = ""

    # Precomputar métricas cross-tienda para el frontend (H8 / H35 / H40)
    grupos_cross = calcular_grupos_cross_tienda(df_dash)
    records = enriquecer_registros_cross_tienda(df_dash, grupos_cross=grupos_cross, cols=cols)

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


def main() -> None:
    """Entry point CLI para consolidar catálogos (H50)."""
    actualizar_todo()


if __name__ == "__main__":
    main()
