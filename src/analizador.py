"""
Motor de procesamiento y análisis de precios de bebidas (Cantina Familiar).
Utiliza pandas para auditar datos, calcular métricas por litro, detectar duplicados
y generar rankings estrictamente separados por categorías comparables.
"""

import argparse
import re
import unicodedata
from typing import Any, Optional

import numpy as np
import pandas as pd

from src.clasificacion import TECHOS_LITRO_OUTLIERS
from src.logger import get_logger

logger = get_logger("analizador")


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


def normalizar_texto_clave(texto: str) -> str:
    """Normaliza un nombre de producto eliminando acentos, puntuación, especificaciones de volumen, stop-words y ordenando tokens para match cross-tienda."""
    if not texto or pd.isnull(texto):
        return ""

    s = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode("utf-8")
    # H35: Eliminar especificaciones de volumen en el título (ej. 700 ml, 750ml, 1.75 L, 1 L, 750 mililitros)
    s = re.sub(r"\b\d+(\.\d+)?\s*(ml|l|litros?|mililitros?)\b", " ", s, flags=re.IGNORECASE)
    s = re.sub(r"[^a-zA-Z0-9\s]", " ", s.lower())
    stop_words = {"de", "del", "el", "la", "los", "las", "en", "para"}
    tokens = [t for t in s.split() if t not in stop_words]
    tokens.sort()
    return " ".join(tokens)


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


def obtener_comparativa_cross_tienda(df: pd.DataFrame) -> pd.DataFrame:
    """
    Genera tabla de arbitraje de precios para botellas presentes en múltiples tiendas (H8 / H35).
    Calcula tienda más barata, más cara y el ahorro máximo por producto, priorizando
    precio por litro para formatos estándar unificados (700ml vs 750ml).
    """
    if "clave_comparativa" not in df.columns or "es_comparable_cross_tienda" not in df.columns:
        df = detectar_duplicados(df)
    if "precio_efectivo" not in df.columns:
        df = calcular_metricas(df)

    comparables = df[df["es_comparable_cross_tienda"] & (df["precio_efectivo"] > 0)].copy()
    if comparables.empty:
        return pd.DataFrame()

    resumen = []
    for clave, grupo in comparables.groupby("clave_comparativa"):
        if grupo["tienda"].nunique() < 2:
            continue

        # H35: Comparar por precio_por_litro para rankear con precisión ofertas con volúmenes ligeramente distintos
        col_ord = "precio_por_litro" if "precio_por_litro" in grupo.columns else "precio_efectivo"
        idx_min = grupo[col_ord].idxmin()
        idx_max = grupo[col_ord].idxmax()

        fila_min = grupo.loc[idx_min]
        fila_max = grupo.loc[idx_max]

        if fila_min["ml"] == fila_max["ml"]:
            ahorro = fila_max["precio_efectivo"] - fila_min["precio_efectivo"]
            pct_ahorro = (ahorro / fila_max["precio_efectivo"] * 100) if fila_max["precio_efectivo"] > 0 else 0.0
        else:
            # H35: Ahorro normalizado al formato de la botella comprada (fila_min)
            ahorro_por_litro = fila_max["precio_por_litro"] - fila_min["precio_por_litro"]
            ahorro = ahorro_por_litro * (fila_min["ml"] / 1000.0)
            pct_ahorro = (
                (ahorro_por_litro / fila_max["precio_por_litro"] * 100) if fila_max["precio_por_litro"] > 0 else 0.0
            )

        resumen.append(
            {
                "clave_comparativa": clave,
                "producto": fila_min["producto"],
                "categoria": fila_min["categoria"],
                "subcategoria": fila_min.get("subcategoria", ""),
                "ml": fila_min["ml"],
                "tiendas_disponibles": sorted(grupo["tienda"].unique().tolist()),
                "tienda_mas_barata": fila_min["tienda"],
                "precio_minimo": round(float(fila_min["precio_efectivo"]), 2),
                "tienda_mas_cara": fila_max["tienda"],
                "precio_maximo": round(float(fila_max["precio_efectivo"]), 2),
                "ahorro_maximo": round(float(ahorro), 2),
                "porcentaje_ahorro_maximo": round(float(pct_ahorro), 1),
            }
        )

    df_comp = pd.DataFrame(resumen)
    if not df_comp.empty:
        df_comp = df_comp.sort_values(by="ahorro_maximo", ascending=False).reset_index(drop=True)
    return df_comp


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


def es_producto_paquete(row_o_nombre: Any, condiciones: Optional[str] = None) -> bool:
    """
    Identifica si un producto es un paquete, combo promocional, kit o edición con obsequio.
    """
    if isinstance(row_o_nombre, str):
        nom = row_o_nombre.lower()
        cond = (condiciones or "").lower()
    elif hasattr(row_o_nombre, "get"):
        nom = str(row_o_nombre.get("producto", "")).lower()
        cond = str(row_o_nombre.get("condiciones", "")).lower()
    else:
        nom = str(row_o_nombre["producto"]).lower()
        cond = str(row_o_nombre.get("condiciones", "")).lower()

    if "🎁" in cond or "obsequio" in cond or "combo" in cond or "kit" in cond:
        return True

    # Palabras clave de paquetes y combos en el nombre
    patron = (
        r"\b(?:pack|paquete|combo|kit|caja|set)\b"
        r"|\b\d+\s*pzas?\b"
        r"|\bx\s*\d+\b"
        r"|\b\d+\s*botellas?\b"
        r"|\bcon\s+(?:vaso|copa|termo|shaker|tumbler|caballito|sal|kit)\b"
    )
    if re.search(patron, nom):
        return True

    # Detección de complementos en el nombre con '+' o 'c/'
    if " + " in nom or " c/" in nom or " con " in nom:
        if re.search(
            r"\+\s*(?:\d+|vaso|copa|termo|sal|bot|agua|refresco|chivas|jack|absolut|woodford|mason|shaker|tumbler)",
            nom,
        ):
            return True
        if re.search(
            r"c\/\s*(?:\d+|bot|vaso|copa|bal[oó]n|caballito|termo|porta|kit|escurridor|concentrado|tamborin|sangria|tinto|vino|ultra|reposado|joven|pechuga)",
            nom,
        ):
            return True

    return False


def calcular_metricas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula:
    - precio_efectivo (unitario real)
    - precio_por_litro: precio_efectivo / (ml / 1000)
    - ahorro_verificable: precio_regular - precio_efectivo
    - porcentaje_ahorro: (ahorro / precio_regular) * 100
    - es_paquete: si es paquete, combo, kit o edición con obsequio
    """
    df["precio_efectivo"] = df.apply(calcular_costo_efectivo, axis=1)

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


if __name__ == "__main__":
    main()
