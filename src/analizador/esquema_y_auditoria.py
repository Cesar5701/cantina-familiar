"""
Validación de esquema, rangos de datos y auditoría de campos faltantes (H9).
"""

import numpy as np
import pandas as pd

COLUMNAS_OBLIGATORIAS = [
    "tienda",
    "producto",
    "marca",
    "categoria",
    "subcategoria",
    "clase",
    "tipo_mezcal",
    "especie_agave",
    "productor",
    "sello_regulador",
    "ml",
    "abv",
    "precio_regular",
    "precio_promo",
    "unidades_promo",
    "precio_total_promo",
    "condiciones",
    "disponibilidad",
    "url",
    "fecha_consulta",
    "fuente",
    "confianza",
]


def cargar_datos(ruta_csv: str, validar_rangos: bool = False) -> pd.DataFrame:
    """Carga el archivo CSV y valida la presencia de columnas mínimas."""
    df = pd.read_csv(ruta_csv)
    columnas_faltantes = [c for c in COLUMNAS_OBLIGATORIAS if c not in df.columns]
    if columnas_faltantes:
        raise ValueError(f"El archivo CSV no contiene las columnas requeridas: {columnas_faltantes}")
    if validar_rangos:
        df, _ = validar_esquema_y_rangos(df)
    return df


def validar_esquema_y_rangos(df: pd.DataFrame, lanzar_error: bool = False) -> tuple[pd.DataFrame, dict]:
    """
    Valida la coherencia de tipos y rangos de datos para evitar métricas sesgadas (H9):
    - Presencia de columnas obligatorias
    - Rango válido de volumen: 100 <= ml <= 10000
    - Rango válido de abv: 0 < abv <= 100 (si está presente)
    - Precios regulares o de promoción positivos (> 0)
    """
    errores = []
    faltantes = [c for c in COLUMNAS_OBLIGATORIAS if c not in df.columns]
    if faltantes:
        errores.append(f"Columnas faltantes: {faltantes}")
        if lanzar_error:
            raise ValueError(f"El dataset no contiene las columnas requeridas: {faltantes}")

    df_val = df.copy()
    ml_num = pd.to_numeric(df_val["ml"], errors="coerce")
    anomalias_ml = df_val[ml_num.isnull() | (ml_num < 100) | (ml_num > 10000)].index.tolist()

    abv_num = pd.to_numeric(df_val.get("abv", np.nan), errors="coerce")
    anomalias_abv = df_val[abv_num.notnull() & ((abv_num <= 0) | (abv_num > 100))].index.tolist()

    pr_num = pd.to_numeric(df_val["precio_regular"], errors="coerce")
    pp_num = pd.to_numeric(df_val.get("precio_promo", np.nan), errors="coerce")
    sin_precio = df_val[(pr_num.isnull() | (pr_num <= 0)) & (pp_num.isnull() | (pp_num <= 0))].index.tolist()

    reporte = {
        "total_registros": len(df_val),
        "registros_validos": len(df_val) - len(set(anomalias_ml + sin_precio)),
        "anomalias_volumen_ml": len(anomalias_ml),
        "anomalias_graduacion_abv": len(anomalias_abv),
        "registros_sin_precio": len(sin_precio),
        "errores": errores,
    }

    df_val["datos_validos"] = ~df_val.index.isin(set(anomalias_ml + sin_precio))
    return df_val, reporte


def auditar_datos_faltantes(df: pd.DataFrame) -> pd.DataFrame:
    """Identifica y marca filas que tienen campos clave vacíos o nulos."""
    columnas_criticas = ["tienda", "producto", "categoria", "ml", "precio_regular", "url", "confianza"]
    faltantes = df[columnas_criticas].isnull()
    df["tiene_datos_faltantes"] = faltantes.any(axis=1)
    df["campos_faltantes"] = faltantes.apply(lambda row: [col for col in columnas_criticas if row[col]], axis=1)
    return df
