"""
Módulo de Gestión y Consulta del Historial de Precios de Cantina Familiar.

Permite:
1. Reconstruir el historial acumulado de precios a partir de los commits históricos de Git.
2. Registrar automáticamente nuevos snapshots de precios tras cada corrida de adquisición/consolidación.
3. Consultar la evolución temporal de precios de cualquier botella o tienda.
"""

import argparse
import io
import os
import subprocess
from typing import Optional

import pandas as pd

from src.clasificacion import normalizar_medidas_en_nombre
from src.io_utils import guardar_csv_atomico
from src.logger import get_logger

logger = get_logger("historial")

RAIZ_PROYECTO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RUTA_HISTORIAL_POR_DEFECTO = os.path.join(RAIZ_PROYECTO, "data", "historial_precios.csv")

ARCHIVOS_TIENDAS = [
    "data/scraped_alianza_completo.csv",
    "data/scraped_walmart.csv",
    "data/scraped_sams.csv",
    "data/scraped_soriana.csv",
    "data/scraped_chedraui.csv",
    "data/scraped_costco.csv",
]

COLUMNAS_HISTORIAL = [
    "fecha_dia",
    "fecha_consulta",
    "tienda",
    "producto",
    "marca",
    "categoria",
    "subcategoria",
    "ml",
    "precio_regular",
    "precio_promo",
    "precio_por_litro",
    "ahorro_verificable",
    "condiciones",
    "url",
]


def normalizar_df_para_historial(df: pd.DataFrame, fecha_por_defecto: str) -> pd.DataFrame:
    """Homologa columnas, formatos numéricos y métricas de precio por litro."""
    if df is None or df.empty:
        return pd.DataFrame(columns=COLUMNAS_HISTORIAL)

    df_norm = df.copy()

    # Resolver fecha de consulta
    if "fecha_consulta" not in df_norm.columns or df_norm["fecha_consulta"].isnull().all():
        df_norm["fecha_consulta"] = fecha_por_defecto
    else:
        df_norm["fecha_consulta"] = df_norm["fecha_consulta"].fillna(fecha_por_defecto).astype(str)

    df_norm["fecha_dia"] = df_norm["fecha_consulta"].str.slice(0, 10)

    # Conversión segura de ml
    if "ml" not in df_norm.columns:
        df_norm["ml"] = 0
    else:
        df_norm["ml"] = pd.to_numeric(df_norm["ml"], errors="coerce").fillna(0).astype(int)

    # Precios seguros
    if "precio_regular" not in df_norm.columns:
        df_norm["precio_regular"] = 0.0
    else:
        df_norm["precio_regular"] = pd.to_numeric(df_norm["precio_regular"], errors="coerce").fillna(0.0).round(2)

    if "precio_promo" not in df_norm.columns:
        df_norm["precio_promo"] = df_norm["precio_regular"]
    else:
        df_norm["precio_promo"] = pd.to_numeric(df_norm["precio_promo"], errors="coerce").fillna(0.0).round(2)

    # Si precio regular es 0 o menor que promo, igualar a promo
    mask_regular_invalido = df_norm["precio_regular"] < df_norm["precio_promo"]
    df_norm.loc[mask_regular_invalido, "precio_regular"] = df_norm.loc[mask_regular_invalido, "precio_promo"]

    # Precio por litro
    mask_ml_valido = df_norm["ml"] > 0
    df_norm["precio_por_litro"] = 0.0
    df_norm.loc[mask_ml_valido, "precio_por_litro"] = (
        df_norm.loc[mask_ml_valido, "precio_promo"] / (df_norm.loc[mask_ml_valido, "ml"] / 1000.0)
    ).round(2)

    # Ahorro verificable
    df_norm["ahorro_verificable"] = (df_norm["precio_regular"] - df_norm["precio_promo"]).round(2)

    # Asegurar existencia de columnas estándar
    for col in COLUMNAS_HISTORIAL:
        if col not in df_norm.columns:
            df_norm[col] = ""

    return df_norm[COLUMNAS_HISTORIAL].copy()


def obtener_snapshots_git() -> list[tuple[str, str]]:
    """Obtiene commits ordenados cronológicamente que modificaron los catálogos en Git."""
    try:
        cmd = [
            "git",
            "log",
            "--format=%H %cd",
            "--date=short",
            "--reverse",
            "--",
        ] + ARCHIVOS_TIENDAS
        resultado = subprocess.run(
            cmd,
            cwd=RAIZ_PROYECTO,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
    except (subprocess.SubprocessError, OSError) as e:
        logger.warning(f"No fue posible consultar git log: {e}")
        return []

    lineas = [lin.strip() for lin in resultado.stdout.split("\n") if lin.strip()]
    vistos = set()
    snapshots = []
    for lin in lineas:
        partes = lin.split()
        if len(partes) >= 2:
            sha, fecha = partes[0], partes[1]
            if (sha, fecha) not in vistos:
                vistos.add((sha, fecha))
                snapshots.append((sha, fecha))

    return snapshots


def extraer_archivo_git(commit_sha: str, ruta_relativa: str) -> Optional[pd.DataFrame]:
    """Extrae un archivo CSV de un commit de Git sin alterar el working tree."""
    try:
        cmd = ["git", "show", f"{commit_sha}:{ruta_relativa}"]
        res = subprocess.run(
            cmd,
            cwd=RAIZ_PROYECTO,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        return pd.read_csv(io.StringIO(res.stdout))
    except (subprocess.SubprocessError, OSError, pd.errors.EmptyDataError, ValueError):
        return None


def construir_historial_desde_git(ruta_salida: str = RUTA_HISTORIAL_POR_DEFECTO) -> pd.DataFrame:
    """
    Reconstruye el historial completo consolidando los snapshots históricos presentes en Git.
    """
    logger.info("Iniciando reconstrucción del historial de precios desde Git...")
    snapshots = obtener_snapshots_git()

    dfs_extraidos = []
    for sha, fecha in snapshots:
        for archivo in ARCHIVOS_TIENDAS:
            df_part = extraer_archivo_git(sha, archivo)
            if df_part is not None and not df_part.empty:
                df_norm = normalizar_df_para_historial(df_part, fecha_por_defecto=fecha)
                dfs_extraidos.append(df_norm)

    # También incorporar el estado actual en el disco.
    # La fecha por defecto debe ser la del momento de la reconstrucción, no una fija:
    # los CSV sin columna fecha_consulta se registran como captura de hoy.
    fecha_actual = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
    for archivo in ARCHIVOS_TIENDAS:
        ruta_disco = os.path.join(RAIZ_PROYECTO, archivo)
        if os.path.exists(ruta_disco):
            try:
                df_disco = pd.read_csv(ruta_disco)
                df_norm = normalizar_df_para_historial(df_disco, fecha_por_defecto=fecha_actual)
                dfs_extraidos.append(df_norm)
            except (OSError, pd.errors.EmptyDataError, ValueError, KeyError) as exc:
                logger.debug("Error leyendo archivo de disco %s: %s", archivo, exc)

    if not dfs_extraidos:
        logger.warning("No se encontraron registros para reconstruir historial.")
        df_vacio = pd.DataFrame(columns=COLUMNAS_HISTORIAL)
        guardar_csv_atomico(df_vacio, ruta_salida)
        return df_vacio

    df_total = pd.concat(dfs_extraidos, ignore_index=True)
    # Deduplicar por (fecha_dia, tienda, producto, ml)
    df_total = df_total.drop_duplicates(subset=["fecha_dia", "tienda", "producto", "ml"], keep="last")
    df_total = df_total.sort_values(by=["fecha_dia", "tienda", "categoria", "producto"]).reset_index(drop=True)

    guardar_csv_atomico(df_total, ruta_salida)
    logger.info(f"Historial reconstruido exitosamente: {len(df_total)} registros guardados en {ruta_salida}")
    return df_total


def registrar_precios_historicos(
    df_nuevo: pd.DataFrame, ruta_historial: str = RUTA_HISTORIAL_POR_DEFECTO
) -> pd.DataFrame:
    """
    Registra e incorpora el nuevo lote de precios en la tabla histórica sin sobreescribir fechas pasadas.
    """
    if not os.path.exists(ruta_historial):
        if os.path.abspath(ruta_historial) == os.path.abspath(RUTA_HISTORIAL_POR_DEFECTO):
            df_existente = construir_historial_desde_git(ruta_historial)
        else:
            df_existente = pd.DataFrame(columns=COLUMNAS_HISTORIAL)
    else:
        try:
            df_existente = pd.read_csv(ruta_historial)
        except (OSError, pd.errors.EmptyDataError, ValueError):
            if os.path.abspath(ruta_historial) == os.path.abspath(RUTA_HISTORIAL_POR_DEFECTO):
                df_existente = construir_historial_desde_git(ruta_historial)
            else:
                df_existente = pd.DataFrame(columns=COLUMNAS_HISTORIAL)

    if df_nuevo is None or df_nuevo.empty:
        return df_existente

    fecha_hoy = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
    df_norm_nuevo = normalizar_df_para_historial(df_nuevo, fecha_por_defecto=fecha_hoy)

    df_consolidado = pd.concat([df_existente, df_norm_nuevo], ignore_index=True)
    df_consolidado = df_consolidado.drop_duplicates(subset=["fecha_dia", "tienda", "producto", "ml"], keep="last")
    df_consolidado = df_consolidado.sort_values(by=["fecha_dia", "tienda", "categoria", "producto"]).reset_index(
        drop=True
    )

    guardar_csv_atomico(df_consolidado, ruta_historial)
    logger.info(
        f"Historial actualizado con lote actual: {len(df_consolidado)} registros históricos totales en {ruta_historial}"
    )
    return df_consolidado


def enriquecer_con_metricas_historicas(df: pd.DataFrame, df_historial: pd.DataFrame) -> pd.DataFrame:
    """
    Cruza el catálogo actual contra el historial de precios para calcular el semáforo anti-inflación:
    - 'descuento_inflado': la tienda subió el precio_regular por encima de su regular histórico para abultar el descuento.
    - 'minimo_historico': el producto está en su precio mínimo histórico con variación real respecto a su máximo.
    - 'subio_vs_minimo': el producto está más caro que su mejor precio histórico registrado en esa misma tienda.
    - 'estable': precio sin variación relevante en al menos 2 capturas históricas.
    - 'nuevo': producto con menos de 2 capturas históricas.
    """
    df_out = df.copy()
    if df_out.empty or df_historial is None or df_historial.empty:
        df_out["precio_min_historico"] = df_out.get("precio_promo", 0.0)
        df_out["precio_max_historico"] = df_out.get("precio_promo", 0.0)
        df_out["precio_reg_min_historico"] = df_out.get("precio_regular", 0.0)
        df_out["capturas_historicas"] = 1
        df_out["semaforo_historico"] = "nuevo"
        return df_out

    hist = df_historial.copy()
    hist["_prod_key"] = hist["producto"].astype(str).apply(normalizar_medidas_en_nombre)
    hist["ml"] = pd.to_numeric(hist["ml"], errors="coerce").fillna(0).astype(int)
    hist["precio_promo"] = pd.to_numeric(hist["precio_promo"], errors="coerce").fillna(0.0)
    hist["precio_regular"] = pd.to_numeric(hist["precio_regular"], errors="coerce").fillna(0.0)
    hist = hist[hist["precio_promo"] > 0]

    stats = hist.groupby(["tienda", "_prod_key", "ml"], as_index=False).agg(
        capturas_historicas=("fecha_dia", "nunique"),
        precio_min_historico=("precio_promo", "min"),
        precio_max_historico=("precio_promo", "max"),
        precio_reg_min_historico=("precio_regular", "min"),
        ultima_captura_historica=("fecha_dia", "max"),
    )

    df_out["_prod_key"] = df_out["producto"].astype(str).apply(normalizar_medidas_en_nombre)
    df_out["_ml_int"] = pd.to_numeric(df_out["ml"], errors="coerce").fillna(0).astype(int)

    df_merged = df_out.merge(
        stats,
        left_on=["tienda", "_prod_key", "_ml_int"],
        right_on=["tienda", "_prod_key", "ml"],
        how="left",
        suffixes=("", "_hist"),
    )

    p_promo = pd.to_numeric(df_merged["precio_promo"], errors="coerce").fillna(0.0)
    p_reg = pd.to_numeric(df_merged["precio_regular"], errors="coerce").fillna(p_promo)
    ahorro = pd.to_numeric(df_merged.get("ahorro_verificable", 0.0), errors="coerce").fillna(0.0)

    fecha_fallback = pd.Timestamp.now().strftime("%Y-%m-%d")
    df_out["capturas_historicas"] = df_merged["capturas_historicas"].fillna(1).astype(int)
    df_out["precio_min_historico"] = df_merged["precio_min_historico"].fillna(p_promo).round(2)
    df_out["precio_max_historico"] = df_merged["precio_max_historico"].fillna(p_promo).round(2)
    df_out["precio_reg_min_historico"] = df_merged["precio_reg_min_historico"].fillna(p_reg).round(2)
    df_out["ultima_captura_historica"] = df_merged["ultima_captura_historica"].fillna(fecha_fallback).astype(str)
    df_out["ultima_vez_visto"] = df_out["ultima_captura_historica"]
    stale_mask = (
        df_out["es_stale"].astype(bool) if "es_stale" in df_out.columns else pd.Series(False, index=df_out.index)
    )
    disp_mask = (
        df_out["disponibilidad"].astype(str).str.lower() == "agotado"
        if "disponibilidad" in df_out.columns
        else pd.Series(False, index=df_out.index)
    )
    df_out["activo"] = ~(stale_mask | disp_mask)

    semaforos = []
    for i in range(len(df_out)):
        n_cap = int(df_out["capturas_historicas"].iloc[i])
        actual = float(p_promo.iloc[i])
        reg_actual = float(p_reg.iloc[i])
        ah_actual = float(ahorro.iloc[i])
        min_h = float(df_out["precio_min_historico"].iloc[i])
        max_h = float(df_out["precio_max_historico"].iloc[i])
        reg_min_h = float(df_out["precio_reg_min_historico"].iloc[i])

        if n_cap < 2:
            semaforos.append("nuevo")
        elif ah_actual > 0 and reg_min_h > 0 and reg_actual > reg_min_h + 1.0:
            semaforos.append("descuento_inflado")
        elif actual <= min_h + 0.05 and max_h > min_h + 1.0:
            semaforos.append("minimo_historico")
        elif actual > min_h + 1.0:
            semaforos.append("subio_vs_minimo")
        else:
            semaforos.append("estable")

    df_out["semaforo_historico"] = semaforos
    df_out = df_out.drop(columns=["_prod_key", "_ml_int"], errors="ignore")
    return df_out


def consultar_historial(
    producto: str,
    tienda: Optional[str] = None,
    ruta_historial: str = RUTA_HISTORIAL_POR_DEFECTO,
) -> pd.DataFrame:
    """
    Filtra y devuelve el historial de precios para un producto y opcionalmente tienda.
    """
    if not os.path.exists(ruta_historial):
        construir_historial_desde_git(ruta_historial)

    df = pd.read_csv(ruta_historial)
    # Búsqueda literal: el texto del usuario no debe interpretarse como regex
    # (evita crashes con entradas como "[" y comodines accidentales como ".").
    mask = df["producto"].str.contains(producto, case=False, na=False, regex=False)
    if tienda:
        mask = mask & df["tienda"].str.contains(tienda, case=False, na=False, regex=False)

    df_res = df[mask].sort_values(by=["producto", "fecha_dia", "tienda"]).reset_index(drop=True)
    return df_res


def formatear_tabla_historial(df_res: pd.DataFrame) -> str:
    """Genera una vista en tabla legible del historial consultado."""
    if df_res.empty:
        return "No se encontraron registros históricos para los criterios especificados."

    cols_ver = [
        "fecha_dia",
        "tienda",
        "producto",
        "ml",
        "precio_regular",
        "precio_promo",
        "precio_por_litro",
        "condiciones",
    ]
    df_sub = df_res[[c for c in cols_ver if c in df_res.columns]].copy()
    return df_sub.to_string(index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Gestor y Consultor de Historial de Precios de Cantina Familiar.")
    parser.add_argument(
        "--reconstruir",
        action="store_true",
        help="Reconstruir historial_precios.csv desde commits de Git.",
    )
    parser.add_argument(
        "--producto",
        type=str,
        default=None,
        help="Nombre o término de búsqueda del producto a consultar.",
    )
    parser.add_argument(
        "--tienda",
        type=str,
        default=None,
        help="Filtrar por nombre de tienda (Alianza, Walmart, Soriana, Sams, Chedraui, Costco).",
    )
    parser.add_argument(
        "--resumen",
        action="store_true",
        help="Mostrar resumen de fechas registradas y volumen de datos en el historial.",
    )

    args = parser.parse_args()

    if args.reconstruir:
        df_hist = construir_historial_desde_git()
        print(f"Historial reconstruido con {len(df_hist)} registros.")
        return

    if args.resumen:
        if not os.path.exists(RUTA_HISTORIAL_POR_DEFECTO):
            construir_historial_desde_git()
        df = pd.read_csv(RUTA_HISTORIAL_POR_DEFECTO)
        print("=== RESUMEN DEL HISTORIAL DE PRECIOS ===")
        print(f"Total registros: {len(df)}")
        print("\nRegistros por fecha:")
        print(df["fecha_dia"].value_counts().sort_index().to_string())
        print("\nRegistros por tienda:")
        print(df["tienda"].value_counts().to_string())
        return

    if args.producto:
        df_res = consultar_historial(args.producto, tienda=args.tienda)
        print(f"=== HISTORIAL DE PRECIOS: '{args.producto}' ===")
        print(formatear_tabla_historial(df_res))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
