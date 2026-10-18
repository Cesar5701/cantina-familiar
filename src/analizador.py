"""
Motor de procesamiento y análisis de precios de bebidas (Cantina Familiar).
Utiliza pandas para auditar datos, calcular métricas por litro, detectar duplicados
y generar rankings estrictamente separados por categorías comparables.
"""

import argparse
import re
import unicodedata
from typing import Any, NamedTuple, Optional

import numpy as np
import pandas as pd

from src.clasificacion import LIMITES_PRESUPUESTO_DASHBOARD, TECHOS_LITRO_OUTLIERS, extraer_ml
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


class ReglaNormalizacion(NamedTuple):
    """Estructura declarativa para reglas de normalización textual (H38)."""

    patron: re.Pattern
    reemplazo: str
    nombre: str


# =====================================================================
# TABLA DECLARATIVA DE NORMALIZACIÓN DE PRODUCTOS Y ETIQUETAS (H38)
# =====================================================================
REGLAS_NORMALIZACION_CLAVE: tuple[ReglaNormalizacion, ...] = (
    # 1. Unificar posesivos ingleses eliminando apóstrofes (Daniel's / Daniel’s -> Daniels, Buchanan's -> Buchanans)
    ReglaNormalizacion(re.compile(r"['’`]"), "", "unificar_posesivos"),
    # 2. Eliminar especificaciones de volumen en el título (ej. 700 ml, 750ml, 1.75 L, 1 L, 750 mililitros)
    ReglaNormalizacion(
        re.compile(r"\b\d+(\.\d+)?\s*(ml|l|litros?|mililitros?)\b", re.IGNORECASE),
        " ",
        "eliminar_volumen",
    ),
    # 3. Unificar variantes ortográficas de bebidas (whiskey/wisky -> whisky, licor de whisky -> whisky)
    ReglaNormalizacion(re.compile(r"\b(whiskey|wisky)\b", re.IGNORECASE), "whisky", "variantes_whisky"),
    ReglaNormalizacion(re.compile(r"\blicor\s+de\s+whisky\b", re.IGNORECASE), "whisky", "licor_de_whisky"),
    ReglaNormalizacion(re.compile(r"\blicor\s+de\b", re.IGNORECASE), " ", "prefijo_licor"),
    # 4. Omitir descriptores regionales/opcionales en marcas reconocidas (ej. Tennessee en Jack Daniel's)
    ReglaNormalizacion(re.compile(r"\btennessee\b", re.IGNORECASE), " ", "descriptor_regional"),
    # 5. Abreviaturas de reposado frecuentes en retail (Rep -> reposado)
    ReglaNormalizacion(re.compile(r"\brep\.?(?!\w)", re.IGNORECASE), "reposado", "abreviatura_reposado"),
    # 6. Descriptores de pureza de agave / artesanales / envase genérico en Tequila y Mezcal
    ReglaNormalizacion(
        re.compile(r"\b100%?\s*(puro\s+de\s+|de\s+)?(agave(\s+azul)?)?\b", re.IGNORECASE),
        " ",
        "pureza_agave",
    ),
    ReglaNormalizacion(re.compile(r"\b(artesanal|botella)\b", re.IGNORECASE), " ", "descriptores_envase"),
    # 7. Descriptores genéricos de Scotch en Whisky
    ReglaNormalizacion(re.compile(r"\bblended\s+scotch\b", re.IGNORECASE), " ", "blended_scotch"),
    ReglaNormalizacion(re.compile(r"\bscotch\b", re.IGNORECASE), " ", "descriptor_scotch"),
    # 8. Espaciado en marcas conocidas (Mc Harrison -> Mcharrison)
    ReglaNormalizacion(re.compile(r"\bmc\s+harrison\b", re.IGNORECASE), "mcharrison", "marca_mcharrison"),
    # 9. Normalización de Cristalinos de clase única en Tequila y Mezcal
    ReglaNormalizacion(
        re.compile(r"\bpatron\s+cristalino\b", re.IGNORECASE),
        "patron anejo cristalino",
        "patron_cristalino",
    ),
    ReglaNormalizacion(
        re.compile(r"\bdobel\s+diamante\s+cristalino\b", re.IGNORECASE),
        "dobel diamante",
        "dobel_diamante",
    ),
    ReglaNormalizacion(
        re.compile(r"\b(mayorazgo|ollitas|viuda\s+de\s+romero|contraluz)\s+cristalino\b", re.IGNORECASE),
        r"\1 reposado cristalino",
        "marcas_reposado_cristalino",
    ),
)

STOP_WORDS_CLAVE: frozenset[str] = frozenset({"de", "del", "el", "la", "los", "las", "en", "para", "licor", "100"})


def normalizar_texto_clave(texto: str) -> str:
    """Normaliza un nombre de producto aplicando la tabla declarativa REGLAS_NORMALIZACION_CLAVE (H38), eliminando acentos, stop-words y unificando el volumen estándar (650-800 ml) para match cross-tienda (H8 / H35). Preserva el tamaño canónico para formatos no estándar (<650 o >800 ml)."""
    if not texto or pd.isnull(texto):
        return ""

    s_orig = str(texto)
    # H35: Extraer volumen previo a la limpieza para preservar formatos no estándar
    ml = extraer_ml(s_orig, ml_defecto=750)

    s = unicodedata.normalize("NFKD", s_orig).encode("ascii", "ignore").decode("utf-8")

    # Aplicar tabla declarativa de transformaciones por regex compiladas (H38)
    for regla in REGLAS_NORMALIZACION_CLAVE:
        s = regla.patron.sub(regla.reemplazo, s)

    s = re.sub(r"[^a-zA-Z0-9\s]", " ", s.lower())
    tokens = [t for t in s.split() if t not in STOP_WORDS_CLAVE]

    # Blindaje H35: botellas no estándar (<650 ml o >800 ml) conservan su tamaño canónico
    if ml and (ml < 650 or ml > 800):
        tokens.append(f"{ml}ml")

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
                    "url": of["url"],
                    "diferencia": round(
                        (p_actual - of["precio_promo"])
                        if row["ml"] == of["ml"]
                        else (p_litro_actual - of["precio_por_litro"]) * (float(row["ml"]) / 1000.0),
                        2,
                    ),
                    "es_mejor_precio": bool(of["precio_por_litro"] < p_litro_actual - 0.05),
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
            rec["es_precio_mas_bajo"] = True
            rec["diferencia_vs_minimo"] = 0.0
            rec["ofertas_cross_tienda"] = []

        records.append(rec)

    return records


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
