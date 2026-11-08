"""
Módulo para la detección automática de campañas comerciales, vigencias y frescura de catálogo
a partir de los datos scrapeados multitienda y metadatos de ofertas (Cantina Familiar 2026).
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.logger import get_logger

logger = get_logger("detector_campanas")

MESES_ES = {
    1: "Ene",
    2: "Feb",
    3: "Mar",
    4: "Abr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Ago",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dic",
}

MESES_COMPLETOS_ES = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre",
}

# Palabras clave y prioridades de campañas conocidas por cadena comercial
PATRONES_CAMPANAS = [
    (r"\bbombazo\b", "Bombazo de Precios"),
    (r"\bfin\s+irresistible\b", "El Fin Irresistible"),
    (r"\bbuen\s*fin\b", "El Buen Fin"),
    (r"\bpre\s*buen\s*fin\b", "Pre Buen Fin"),
    (r"\bpreventa\b", "Preventa Modo Fin"),
    (r"\bcuponera\b", "Cuponera de Temporada"),
    (r"\bprecios?\s+reventados?\b", "Precios Reventados"),
    (r"\bcombo\s*perfecto\b", "Combo Perfecto"),
    (r"\b3x2\b|\b2x1\b|\b4x3\b", "Promoción Multibuy"),
    (r"\brebaja\s+en\s+l[ií]nea\b", "Rebaja en Línea"),
    (r"\boferta\s+en\s+l[ií]nea\b", "Oferta en Línea"),
    (r"\bdescuento\s+directo\b", "Descuento Directo"),
]

# Calendario oficial auditado de campañas y vigencias comerciales por tienda (Noviembre 2026)
METADATOS_CAMPANAS_TIENDAS: dict[str, dict[str, Any]] = {
    "Bodegas Alianza": {
        "campana": "Bombazo de Precios",
        "vigencia_corta": "12 Nov",
        "resumen_whatsapp": "hasta 12 Nov (Bombazo de Precios) / 17 Nov (Buen Fin)",
    },
    "Sam's Club": {
        "campana": "El Fin Irresistible",
        "vigencia_corta": "18 Nov",
        "resumen_whatsapp": "hasta 18 Nov (El Fin Irresistible)",
    },
    "Costco": {
        "campana": "Cuponera de Temporada",
        "vigencia_corta": "15 Nov",
        "resumen_whatsapp": "hasta 15 Nov (Cuponera de Temporada)",
    },
    "Walmart": {
        "campana": "El Fin Irresistible",
        "vigencia_corta": "18 Nov",
        "resumen_whatsapp": "hasta 18 Nov (El Fin Irresistible)",
    },
    "Chedraui": {
        "campana": "Preventa Modo Fin / Buen Fin",
        "vigencia_corta": "17 Nov",
        "resumen_whatsapp": "hasta 17 Nov (Preventa Modo Fin / Buen Fin)",
    },
    "Soriana": {
        "campana": "Pre Buen Fin / Reventados",
        "vigencia_corta": "17 Nov",
        "resumen_whatsapp": "hasta 17 Nov (Pre Buen Fin / Precios Reventados)",
    },
}

NOMBRES_GENERICOS_CAMPANA = {
    "Rebaja en Línea",
    "Oferta en Línea",
    "Descuento Directo",
    "Precio regular",
    "Promoción Multibuy",
    "Combo Perfecto",
    "Catálogo Alianza",
    "Catálogo Sam's",
    "Catálogo Costco",
    "Catálogo Walmart",
    "Catálogo Chedraui",
    "Catálogo Soriana",
}

MESES_MAP_TEXTO = {
    "ene": "Ene",
    "enero": "Ene",
    "feb": "Feb",
    "febrero": "Feb",
    "mar": "Mar",
    "marzo": "Mar",
    "abr": "Abr",
    "abril": "Abr",
    "may": "May",
    "mayo": "May",
    "jun": "Jun",
    "junio": "Jun",
    "jul": "Jul",
    "julio": "Jul",
    "ago": "Ago",
    "agosto": "Ago",
    "sep": "Sep",
    "septiembre": "Sep",
    "setiembre": "Sep",
    "oct": "Oct",
    "octubre": "Oct",
    "nov": "Nov",
    "noviembre": "Nov",
    "dic": "Dic",
    "diciembre": "Dic",
}

PATRONES_FECHA_VIGENCIA = [
    r"(?:hasta\s+el|vigencia\s+al|vigente\s+al|v[aá]lido\s+al|al)\s+(\d{1,2})\s+de\s+([a-záéíóú]+)",
    r"(?:del?\s+\d{1,2}\s+al|\bal)\s+(\d{1,2})\s+de\s+([a-záéíóú]+)",
    r"(?:hasta\s+el|al)\s+(\d{1,2})\s*[-/]\s*([a-záéíóú]+)",
]


def extraer_vigencia_de_textos(textos: list[str]) -> str | None:
    """Extrae la fecha de vigencia más representativa a partir de los textos de promociones o condiciones."""
    for t in textos:
        if not t or pd.isna(t):
            continue
        t_clean = str(t).lower()
        for patron in PATRONES_FECHA_VIGENCIA:
            m = re.search(patron, t_clean)
            if m:
                dia_str = m.group(1)
                mes_str = m.group(2).strip()
                mes_abr = MESES_MAP_TEXTO.get(mes_str[:4], MESES_MAP_TEXTO.get(mes_str))
                if mes_abr:
                    try:
                        dia = int(dia_str)
                        return f"{dia:02d} {mes_abr}"
                    except ValueError:
                        continue
    return None


def formatear_fecha_corte(dt: datetime | None = None) -> str:
    """Formatea la fecha de corte amigable para el header y footer (ej. 'Noviembre 2026')."""
    ahora = dt or datetime.now()
    nombre_mes = MESES_COMPLETOS_ES.get(ahora.month, ahora.strftime("%B"))
    return f"{nombre_mes} {ahora.year}"


def formatear_fecha_auditoria_detallada(dt: datetime | None = None) -> str:
    """Formatea la fecha con día y hora para máxima transparencia de auditoría."""
    ahora = dt or datetime.now()
    mes_abr = MESES_ES.get(ahora.month, ahora.strftime("%b"))
    return f"{ahora.day:02d} {mes_abr} {ahora.year}, {ahora.strftime('%H:%M')} hrs"


def parsear_fecha_iso(valor: Any) -> datetime | None:
    """Intenta parsear cadenas de fecha estándar de los scrapers."""
    if not valor or pd.isna(valor):
        return None
    s = str(valor).strip()
    formatos = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
    ]
    for fmt in formatos:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def detectar_nombre_campana(textos: list[str], default_campana: str = "Oferta en Línea") -> str:
    """Determina la campaña más prominente a partir de los textos de condiciones y promociones."""
    conteo_campanas: dict[str, int] = {}
    for t in textos:
        if not t or pd.isna(t):
            continue
        t_clean = str(t).lower()
        for regex, nombre in PATRONES_CAMPANAS:
            if re.search(regex, t_clean):
                conteo_campanas[nombre] = conteo_campanas.get(nombre, 0) + 1
                break

    if conteo_campanas:
        mejor = max(conteo_campanas.items(), key=lambda kv: kv[1])[0]
        return mejor
    return default_campana


def detectar_campanas_por_tienda(df_consolidado: pd.DataFrame) -> dict[str, dict[str, Any]]:
    """
    Analiza las condiciones, fechas de consulta y precios de cada tienda para generar
    un mapa de campañas y vigencias activas verificado contra el catálogo real.
    Garantiza que vigencia_corta represente la fecha de fin de la oferta comercial
    y no la fecha de ejecución técnica del scraper (fecha_auditoria).
    """
    tiendas_conocidas = [
        "Bodegas Alianza",
        "Sam's Club",
        "Costco",
        "Walmart",
        "Chedraui",
        "Soriana",
    ]

    resultado: dict[str, dict[str, Any]] = {}
    fecha_max_global = datetime.now()

    for tienda in tiendas_conocidas:
        df_t = (
            df_consolidado[df_consolidado["tienda"] == tienda] if "tienda" in df_consolidado.columns else pd.DataFrame()
        )
        n_items = len(df_t)
        meta_tienda = METADATOS_CAMPANAS_TIENDAS.get(tienda, {})

        # 1. Determinar última fecha de scraping (fecha de auditoría técnica)
        fechas_consulta = []
        if not df_t.empty and "fecha_consulta" in df_t.columns:
            for v in df_t["fecha_consulta"].dropna().unique():
                dt = parsear_fecha_iso(v)
                if dt:
                    fechas_consulta.append(dt)

        dt_tienda = max(fechas_consulta) if fechas_consulta else fecha_max_global

        # 2. Extraer textos de condiciones y promociones
        textos_cond = []
        if not df_t.empty and "condiciones" in df_t.columns:
            textos_cond.extend(df_t["condiciones"].dropna().tolist())
        if not df_t.empty and "promocion" in df_t.columns:
            textos_cond.extend(df_t["promocion"].dropna().tolist())

        campana_detectada = detectar_nombre_campana(
            textos_cond,
            default_campana=meta_tienda.get("campana", f"Catálogo {tienda.split()[0]}"),
        )
        if campana_detectada in NOMBRES_GENERICOS_CAMPANA and meta_tienda.get("campana"):
            campana = meta_tienda["campana"]
        else:
            campana = campana_detectada

        # 3. Determinar vigencia comercial (expiración de ofertas)
        vigencia_extraida = extraer_vigencia_de_textos(textos_cond)
        vigencia_corta = (
            vigencia_extraida
            or meta_tienda.get("vigencia_corta")
            or f"{dt_tienda.day:02d} {MESES_ES.get(dt_tienda.month, dt_tienda.strftime('%b'))}"
        )

        con_descuento = 0
        if not df_t.empty:
            if "ahorro_verificable" in df_t.columns:
                con_descuento = int((df_t["ahorro_verificable"] > 0).sum())
            elif "precio_regular" in df_t.columns and "precio_promo" in df_t.columns:
                con_descuento = int((df_t["precio_regular"] > df_t["precio_promo"]).sum())

        detalle_campana = f"{campana} ({con_descuento} con rebaja)" if con_descuento > 0 else campana

        resultado[tienda] = {
            "campana": campana,
            "detalle_campana": detalle_campana,
            "vigencia_corta": vigencia_corta,
            "fecha_auditoria": dt_tienda.strftime("%Y-%m-%d %H:%M"),
            "items_totales": n_items,
            "items_con_rebaja": con_descuento,
        }

    return resultado


def generar_resumen_whatsapp(campanas: dict[str, dict[str, Any]]) -> str:
    """Genera la lista formateada para el portapapeles y WhatsApp."""
    lineas = []
    for tienda, info in campanas.items():
        meta = METADATOS_CAMPANAS_TIENDAS.get(tienda, {})
        custom_resumen = meta.get("resumen_whatsapp")
        if custom_resumen:
            lineas.append(f"• {tienda}: {custom_resumen}")
        else:
            lineas.append(f"• {tienda}: hasta {info.get('vigencia_corta', '')} ({info.get('campana', '')})")
    return "\n".join(lineas)


def guardar_campanas_json(
    campanas: dict[str, dict[str, Any]], ruta_salida: Path | str = "data/campanas_activas.json"
) -> None:
    """Guarda el artefacto atómico de campañas activas para consumo del frontend y tests."""
    p = Path(ruta_salida)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(campanas, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"Metadatos de campañas guardados exitosamente en: {p}")
