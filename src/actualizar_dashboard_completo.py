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

import argparse
import os

import pandas as pd

from src.analizador import (
    calcular_grupos_cross_tienda,
    calcular_metricas,
    detectar_campanas_por_tienda,
    detectar_duplicados,
    enriquecer_registros_cross_tienda,
    filtrar_catalogo_dashboard,
    guardar_campanas_json,
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
from src.historial import enriquecer_con_metricas_historicas, registrar_precios_historicos
from src.io_utils import guardar_csv_atomico, guardar_json_atomico
from src.logger import get_logger

logger = get_logger("actualizador")


def cargar_fuentes(archivos_fuente: list[str]) -> pd.DataFrame:
    """Carga y concatena los CSVs de tiendas disponibles."""
    dfs = []
    for ruta in archivos_fuente:
        if os.path.exists(ruta):
            df_part = pd.read_csv(ruta)
            logger.info(f"Cargado {ruta}: {len(df_part)} filas")
            dfs.append(df_part)

    if not dfs:
        logger.warning("No se encontraron archivos fuente para consolidar.")
        return pd.DataFrame()

    return pd.concat(dfs, ignore_index=True)


def depurar_y_clasificar_catalogo(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica normalización de medidas, filtros de formato/volumen y reglas NOM."""
    if df.empty:
        return df

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
    return calcular_metricas(df)


def auditar_y_filtrar_anomalias(df: pd.DataFrame) -> pd.DataFrame:
    """Valida esquema, tipos y rangos de precios/graduación y elimina anomalías."""
    if df.empty:
        return df

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
    return df[df["datos_validos"]].copy().reset_index(drop=True)


def persistir_rankings_e_historial(df: pd.DataFrame, carpeta_salida: str) -> pd.DataFrame:
    """Detecta outliers de lujo, registra snapshot histórico y persiste rankings generales en disco."""
    if df.empty:
        return df

    # Identificar y marcar outliers de ultra-lujo (H25)
    df = marcar_outliers_lujo(df)
    n_outliers = int(df["es_outlier_lujo"].sum())
    logger.info(f"Detección de ultra-lujo: {n_outliers} botellas marcadas como outliers fuera de alcance familiar")

    # Acumular snapshot en el registro histórico persistente de precios y enriquecer semáforo histórico
    df_historial = registrar_precios_historicos(df, os.path.join(carpeta_salida, "historial_precios.csv"))
    df = enriquecer_con_metricas_historicas(df, df_historial)

    # Guardar catálogo completo con trazabilidad de outliers y métricas históricas (H10 / H25)
    guardar_csv_atomico(df, os.path.join(carpeta_salida, "catalogo_completo_consolidado.csv"))

    # Guardar ranking general limpio de outliers para comparativas fiables (H25)
    df_ranking = df[~df["es_outlier_lujo"]].sort_values(by=["categoria", "precio_por_litro"]).reset_index(drop=True)
    guardar_csv_atomico(df_ranking, os.path.join(carpeta_salida, "ranking_completo_general.csv"))

    # Detección y persistencia de campañas y vigencias activas por tienda
    campanas = detectar_campanas_por_tienda(df)
    guardar_campanas_json(campanas, os.path.join(carpeta_salida, "campanas_activas.json"))

    return df


def enriquecer_y_exportar_dashboard(df: pd.DataFrame, carpeta_salida: str) -> list[dict]:
    """Filtra catálogo familiar, calcula comparativas cross-tienda y genera dashboard_data.json."""
    if df.empty:
        return []

    # Filtrar para catálogo relevante de la cantina familiar según límites centralizados (H32, H37, H41)
    df_dash = filtrar_catalogo_dashboard(df, LIMITES_PRESUPUESTO_DASHBOARD)

    cols = [
        "tienda",
        "producto",
        "marca",
        "categoria",
        "subcategoria",
        "clase",
        "tipo_mezcal",
        "productor",
        "categoria_comparable",
        "ml",
        "abv",
        "precio_promo",
        "precio_regular",
        "precio_por_litro",
        "ahorro_verificable",
        "porcentaje_ahorro",
        "semaforo_historico",
        "precio_min_historico",
        "precio_max_historico",
        "precio_reg_min_historico",
        "disponibilidad",
        "stock_unidades",
        "url",
        "fecha_consulta",
        "dias_desde_actualizacion",
        "es_stale",
        "ultima_captura_historica",
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


def actualizar_todo(archivos_fuente: list[str] | None = None, carpeta_salida: str = "data") -> list[dict]:
    """Pipeline orquestador en etapas modulares para consolidar datos, rankings y dashboard."""
    if archivos_fuente is None:
        archivos_fuente = [
            "data/scraped_alianza_completo.csv",
            "data/scraped_sams.csv",
            "data/scraped_walmart.csv",
            "data/scraped_chedraui.csv",
            "data/scraped_soriana.csv",
            "data/scraped_costco.csv",
        ]

    df_crudo = cargar_fuentes(archivos_fuente)
    if df_crudo.empty:
        return []

    df_clasificado = depurar_y_clasificar_catalogo(df_crudo)
    df_auditado = auditar_y_filtrar_anomalias(df_clasificado)
    df_enriquecido = persistir_rankings_e_historial(df_auditado, carpeta_salida)
    return enriquecer_y_exportar_dashboard(df_enriquecido, carpeta_salida)


def main() -> None:
    """Entry point CLI para consolidar catálogos (H50)."""
    parser = argparse.ArgumentParser(
        description="Consolida datasets de las 6 tiendas, aplica reglas NOM y genera dashboard_data.json."
    )
    parser.parse_args()
    actualizar_todo()


if __name__ == "__main__":
    main()
