"""
Generación de rankings por categoría comparable y herramienta CLI de auditoría ad-hoc.
"""

import argparse

import pandas as pd

from src.analizador.cross_tienda import detectar_duplicados
from src.analizador.esquema_y_auditoria import auditar_datos_faltantes, cargar_datos
from src.analizador.metricas_y_outliers import calcular_metricas
from src.logger import get_logger

logger = get_logger("analizador")


def generar_rankings_por_categoria(df: pd.DataFrame, excluir_outliers: bool = True) -> dict[str, pd.DataFrame]:
    """
    Genera rankings ordenados por precio_por_litro dentro de cada subcategoría comparable
    respetando estrictamente la Regla de Rigor 6 (no mezclar categorías no equivalentes).
    """
    # Filtrar solo registros no duplicados y con precio por litro válido y positivo
    no_duplicados = (~df["es_duplicado"]) if "es_duplicado" in df.columns else True
    sin_outliers = (
        (~df["es_outlier_lujo"])
        if (excluir_outliers and "es_outlier_lujo" in df.columns)
        else pd.Series(True, index=df.index)
    )
    validos = df[
        no_duplicados & sin_outliers & (pd.notnull(df["precio_por_litro"])) & (df["precio_por_litro"] > 0)
    ].copy()

    # Definición de grupos comparables estrictos
    grupos = {
        "Tequila - Añejo Tradicional": validos[
            (validos["categoria"] == "Tequila") & (validos["subcategoria"] == "Añejo Tradicional")
        ],
        "Tequila - Añejo Cristalino": validos[
            (validos["categoria"] == "Tequila") & (validos["subcategoria"] == "Añejo Cristalino")
        ],
        "Tequila - Reposado": validos[
            (validos["categoria"] == "Tequila")
            & (validos["subcategoria"].str.contains("Reposado", case=False, na=False))
        ],
        "Mezcal - Reposado": validos[(validos["categoria"] == "Mezcal") & (validos["subcategoria"] == "Reposado")],
        "Mezcal - Añejo": validos[(validos["categoria"] == "Mezcal") & (validos["subcategoria"] == "Añejo")],
        "Mezcal - Silvestre": validos[(validos["categoria"] == "Mezcal") & (validos["subcategoria"] == "Silvestre")],
        "Mezcal - Espadín Joven": validos[
            (validos["categoria"] == "Mezcal") & (validos["subcategoria"] == "Espadín Joven")
        ],
        "Whisky - Blended Scotch": validos[
            (validos["categoria"] == "Whisky") & (validos["subcategoria"] == "Blended Scotch")
        ],
        "Licor de Whisky - Honey": validos[
            (validos["categoria"] == "Licor de Whisky") & (validos["subcategoria"] == "Honey Liqueur")
        ],
        "Vino - Tinto Clericot": validos[
            (validos["categoria"] == "Vino") & (validos["subcategoria"] == "Tinto Clericot")
        ],
    }

    rankings = {}
    for nombre_grupo, sub_df in grupos.items():
        if not sub_df.empty:
            rankings[nombre_grupo] = sub_df.sort_values(by="precio_por_litro", ascending=True).reset_index(drop=True)

    return rankings


def imprimir_resumen_rankings(rankings: dict[str, pd.DataFrame]):
    """Imprime en terminal el ranking formateado por categoría."""
    logger.info("=" * 80)
    logger.info("RANKINGS POR CATEGORÍA COMPARABLE (ORDENADO POR PRECIO POR LITRO)")
    logger.info("=" * 80)

    for nombre_grupo, df_cat in rankings.items():
        logger.info(f">>> {nombre_grupo.upper()} ({len(df_cat)} productos)")
        cols = ["producto", "tienda", "ml", "precio_efectivo", "precio_por_litro", "porcentaje_ahorro", "confianza"]
        sub = df_cat[cols].copy()
        sub.columns = ["Producto", "Tienda", "ml", "Precio ($)", "$/Litro", "% Ahorro", "Confianza"]
        logger.info("\n" + sub.to_string(index=True))


def procesar_archivo(ruta_entrada: str, ruta_salida: str | None = None) -> pd.DataFrame:
    """Ejecuta el flujo completo de validación, auditoría, cálculo y reporte."""
    df = cargar_datos(ruta_entrada)
    df = auditar_datos_faltantes(df)
    df = detectar_duplicados(df)
    df = calcular_metricas(df)

    if ruta_salida:
        df.to_csv(ruta_salida, index=False)
        logger.info(f"Archivo procesado guardado en: {ruta_salida}")

    return df


def main():
    parser = argparse.ArgumentParser(description="Procesador y analizador de precios de bebidas.")
    parser.add_argument("--entrada", default="data/bebidas_verificadas.csv", help="Ruta al CSV de entrada.")
    parser.add_argument("--salida", default="data/reporte_ranking.csv", help="Ruta al CSV de salida con cálculos.")
    args = parser.parse_args()

    df = procesar_archivo(args.entrada, args.salida)

    # Reportar datos faltantes y duplicados
    faltantes_count = df["tiene_datos_faltantes"].sum()
    duplicados_count = df["es_duplicado"].sum()
    logger.info(
        f"Auditoría inicial: {len(df)} registros totales, {faltantes_count} con datos faltantes, {duplicados_count} duplicados."
    )

    rankings = generar_rankings_por_categoria(df)
    imprimir_resumen_rankings(rankings)
