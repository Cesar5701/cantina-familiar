"""
Motor de procesamiento y análisis de precios de bebidas (Cantina Familiar).
Utiliza pandas para auditar datos, calcular métricas por litro, detectar duplicados
y generar rankings estrictamente separados por categorías comparables.
"""

import sys
import argparse
import pandas as pd
import numpy as np


COLUMNAS_OBLIGATORIAS = [
    "tienda", "producto", "marca", "categoria", "subcategoria",
    "clase", "tipo_mezcal", "especie_agave", "productor", "sello_regulador",
    "ml", "abv", "precio_regular", "precio_promo", "unidades_promo",
    "precio_total_promo", "condiciones", "disponibilidad", "url",
    "fecha_consulta", "fuente", "confianza"
]


def cargar_datos(ruta_csv: str) -> pd.DataFrame:
    """Carga el archivo CSV y valida la presencia de columnas mínimas."""
    df = pd.read_csv(ruta_csv)
    columnas_faltantes = [c for c in COLUMNAS_OBLIGATORIAS if c not in df.columns]
    if columnas_faltantes:
        raise ValueError(f"El archivo CSV no contiene las columnas requeridas: {columnas_faltantes}")
    return df


def auditar_datos_faltantes(df: pd.DataFrame) -> pd.DataFrame:
    """Identifica y marca filas que tienen campos clave vacíos o nulos."""
    columnas_criticas = ["tienda", "producto", "categoria", "ml", "precio_regular", "url", "confianza"]
    faltantes = df[columnas_criticas].isnull()
    df["tiene_datos_faltantes"] = faltantes.any(axis=1)
    df["campos_faltantes"] = faltantes.apply(lambda row: [col for col in columnas_criticas if row[col]], axis=1)
    return df


def detectar_duplicados(df: pd.DataFrame) -> pd.DataFrame:
    """Detecta filas duplicadas por combinación (tienda, producto, ml)."""
    df["es_duplicado"] = df.duplicated(subset=["tienda", "producto", "ml"], keep="first")
    return df


def calcular_costo_efectivo(row: pd.Series) -> float:
    """
    Calcula el costo efectivo unitario distinguiendo:
    - Promoción multiunidad (ej. 3x2 o paquete N piezas).
    - Descuento directo unitario.
    - Precio regular.
    """
    unidades = row.get("unidades_promo", 1)
    precio_total = row.get("precio_total_promo", np.nan)
    precio_promo = row.get("precio_promo", np.nan)
    precio_regular = row.get("precio_regular", np.nan)

    # Caso multiunidad: unidades > 1 y precio_total válido
    if pd.notnull(unidades) and unidades > 1 and pd.notnull(precio_total) and precio_total > 0:
        return float(precio_total) / float(unidades)

    # Caso unitario promocional
    if pd.notnull(precio_promo) and precio_promo > 0:
        return float(precio_promo)

    # Caso regular
    if pd.notnull(precio_regular) and precio_regular > 0:
        return float(precio_regular)

    return np.nan


def calcular_metricas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula:
    - precio_efectivo (unitario real)
    - precio_por_litro: precio_efectivo / (ml / 1000)
    - ahorro_verificable: precio_regular - precio_efectivo
    - porcentaje_ahorro: (ahorro / precio_regular) * 100
    """
    df["precio_efectivo"] = df.apply(calcular_costo_efectivo, axis=1)

    # Validación de ml > 0 para evitar división por cero
    df["ml"] = pd.to_numeric(df["ml"], errors="coerce").fillna(750)
    df["litros"] = df["ml"] / 1000.0
    df["precio_por_litro"] = np.where(
        (df["litros"] > 0) & pd.notnull(df["precio_efectivo"]) & (df["precio_efectivo"] > 0),
        (df["precio_efectivo"] / df["litros"]).round(2),
        np.nan
    )

    # Ahorro verificable
    df["precio_regular"] = pd.to_numeric(df["precio_regular"], errors="coerce").fillna(df["precio_efectivo"])
    df["ahorro_verificable"] = (df["precio_regular"] - df["precio_efectivo"]).apply(
        lambda x: max(0.0, round(x, 2)) if pd.notnull(x) else 0.0
    )
    df["porcentaje_ahorro"] = np.where(
        (pd.notnull(df["precio_regular"])) & (df["precio_regular"] > 0),
        ((df["ahorro_verificable"] / df["precio_regular"]) * 100.0).round(1),
        0.0
    )

    return df


def generar_rankings_por_categoria(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """
    Genera rankings ordenados por precio_por_litro dentro de cada subcategoría comparable
    respetando estrictamente la Regla de Rigor 6 (no mezclar categorías no equivalentes).
    """
    # Filtrar solo registros no duplicados y con precio por litro válido y positivo
    no_duplicados = (~df["es_duplicado"]) if "es_duplicado" in df.columns else True
    validos = df[
        no_duplicados & 
        (pd.notnull(df["precio_por_litro"])) & 
        (df["precio_por_litro"] > 0)
    ].copy()

    # Definición de grupos comparables estrictos
    grupos = {
        "Tequila - Añejo Tradicional": validos[(validos["categoria"] == "Tequila") & (validos["subcategoria"] == "Añejo Tradicional")],
        "Tequila - Añejo Cristalino": validos[(validos["categoria"] == "Tequila") & (validos["subcategoria"] == "Añejo Cristalino")],
        "Tequila - Reposado": validos[(validos["categoria"] == "Tequila") & (validos["subcategoria"].str.contains("Reposado", case=False, na=False))],
        "Mezcal - Reposado": validos[(validos["categoria"] == "Mezcal") & (validos["subcategoria"] == "Reposado")],
        "Mezcal - Añejo": validos[(validos["categoria"] == "Mezcal") & (validos["subcategoria"] == "Añejo")],
        "Mezcal - Silvestre": validos[(validos["categoria"] == "Mezcal") & (validos["subcategoria"] == "Silvestre")],
        "Mezcal - Silvestres (Tobalá/Cupreata/Cuishe)": validos[(validos["categoria"] == "Mezcal") & (validos["subcategoria"] == "Silvestre")],
        "Mezcal - Espadín Joven": validos[(validos["categoria"] == "Mezcal") & (validos["subcategoria"] == "Espadín Joven")],
        "Whisky - Blended Scotch": validos[(validos["categoria"] == "Whisky") & (validos["subcategoria"] == "Blended Scotch")],
        "Licor de Whisky - Honey": validos[(validos["categoria"] == "Licor de Whisky") & (validos["subcategoria"] == "Honey Liqueur")],
        "Vino - Tinto Clericot": validos[(validos["categoria"] == "Vino") & (validos["subcategoria"] == "Tinto Clericot")]
    }

    rankings = {}
    for nombre_grupo, sub_df in grupos.items():
        if not sub_df.empty:
            rankings[nombre_grupo] = sub_df.sort_values(by="precio_por_litro", ascending=True).reset_index(drop=True)

    return rankings


def imprimir_resumen_rankings(rankings: dict[str, pd.DataFrame]):
    """Imprime en terminal el ranking formateado por categoría."""
    print("=" * 90)
    print("RANKINGS POR CATEGORÍA COMPARABLE (ORDENADO POR PRECIO POR LITRO)")
    print("=" * 90)

    for nombre_grupo, df_cat in rankings.items():
        print(f"\n>>> {nombre_grupo.upper()} ({len(df_cat)} productos)")
        print("-" * 90)
        cols = ["producto", "tienda", "ml", "precio_efectivo", "precio_por_litro", "porcentaje_ahorro", "confianza"]
        sub = df_cat[cols].copy()
        sub.columns = ["Producto", "Tienda", "ml", "Precio ($)", "$/Litro", "% Ahorro", "Confianza"]
        print(sub.to_string(index=True))


def procesar_archivo(ruta_entrada: str, ruta_salida: str = None) -> pd.DataFrame:
    """Ejecuta el flujo completo de validación, auditoría, cálculo y reporte."""
    df = cargar_datos(ruta_entrada)
    df = auditar_datos_faltantes(df)
    df = detectar_duplicados(df)
    df = calcular_metricas(df)

    if ruta_salida:
        df.to_csv(ruta_salida, index=False)
        print(f"[OK] Archivo procesado guardado en: {ruta_salida}")

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
    print(f"\nAuditoría inicial:")
    print(f"  • Registros totales: {len(df)}")
    print(f"  • Filas con datos críticos faltantes: {faltantes_count}")
    print(f"  • Filas duplicadas detectadas: {duplicados_count}")

    rankings = generar_rankings_por_categoria(df)
    imprimir_resumen_rankings(rankings)


if __name__ == "__main__":
    main()
