"""
Generador Maestro del Dashboard BI interactivo v6.0 para Cantina Familiar 2026.
Desacoplado en arquitectura modular de plantillas (CSS, parciales HTML y módulos JS)
que se ensamblan en un index.html autocontenido para publicación en GitHub Pages (H29).
"""

import base64
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.analizador.campanas import formatear_fecha_corte, generar_resumen_whatsapp
from src.logger import get_logger

logger = get_logger("dashboard_v4")
INDEX_HTML_PATH = ROOT_DIR / "index.html"
DATA_JSON_PATH = ROOT_DIR / "data" / "dashboard_data.json"
TEMPLATES_DIR = ROOT_DIR / "src" / "templates"
TEMPLATE_PATH = TEMPLATES_DIR / "dashboard_template.html"

PATRON_INCLUDE = re.compile(r"<!--\s*@include\s+([^\s]+)\s*-->\n?")
PATRON_DATAURI = re.compile(r"<!--\s*@datauri\s+([^\s]+)\s*-->")
PROFUNDIDAD_MAX_INCLUDE = 5
MIME_RECURSOS = {
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".webp": "image/webp",
}

CAMPANAS_JSON_PATH = ROOT_DIR / "data" / "campanas_activas.json"


# =====================================================================
# MATRIZ DINÁMICA DE VIGENCIAS Y CAMPAÑAS ACTIVAS (SCRAPING AUTOMÁTICO)
# =====================================================================
def obtener_configuracion_vigencia() -> dict[str, Any]:
    """Carga las campañas activas generadas por el scraper o infiere defaults de la fecha actual."""
    corte_dinamico = formatear_fecha_corte(datetime.now())
    campanas_map = {}

    if CAMPANAS_JSON_PATH.exists():
        try:
            campanas_map = json.loads(CAMPANAS_JSON_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            campanas_map = {}

    if campanas_map:
        resumen = generar_resumen_whatsapp(campanas_map)
    else:
        resumen = (
            "Bodegas Alianza: Bombazo de Precios / Buen Fin\n"
            "Sam's Club: El Fin Irresistible\n"
            "Costco: Cuponera de Temporada\n"
            "Chedraui: Buen Fin\n"
            "Soriana: Pre Buen Fin / Precios Reventados\n"
            "Walmart: El Fin Irresistible"
        )

    return {
        "corte_auditoria": corte_dinamico,
        "resumen_whatsapp": resumen,
        "campanas": campanas_map,
    }


def ensamblar_plantilla_modular(template_content: str, base_dir: Path | None = None) -> str:
    """
    Expande las directivas <!-- @include ruta --> leyendo los submódulos de CSS, HTML y JS,
    y las directivas <!-- @datauri ruta --> incrustando recursos (favicon, íconos) como data: URI
    en base64 para mantener el index.html autocontenido.
    """
    directorio_base = base_dir or TEMPLATES_DIR

    def _reemplazar_include(match: re.Match) -> str:
        rel_path = match.group(1)
        inc_path = directorio_base / rel_path
        if not inc_path.exists():
            raise FileNotFoundError(f"Módulo de plantilla no encontrado: {inc_path}")
        return inc_path.read_text(encoding="utf-8")

    def _reemplazar_datauri(match: re.Match) -> str:
        rel_path = match.group(1)
        recurso = directorio_base / rel_path
        if not recurso.exists():
            raise FileNotFoundError(f"Recurso de plantilla no encontrado: {recurso}")
        mime = MIME_RECURSOS.get(recurso.suffix.lower())
        if mime is None:
            raise ValueError(f"Tipo de recurso no soportado para @datauri: {recurso.suffix}")
        codificado = base64.b64encode(recurso.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{codificado}"

    expandida = template_content
    for _ in range(PROFUNDIDAD_MAX_INCLUDE):
        if not PATRON_INCLUDE.search(expandida):
            break
        expandida = PATRON_INCLUDE.sub(_reemplazar_include, expandida)
    if PATRON_INCLUDE.search(expandida):
        raise RecursionError(
            f"Inclusiones anidadas más allá de {PROFUNDIDAD_MAX_INCLUDE} niveles (¿referencia circular?)"
        )
    return PATRON_DATAURI.sub(_reemplazar_datauri, expandida)


def cargar_plantilla_dashboard(template_path: Path | str | None = None) -> str:
    """Lee la plantilla maestra y resuelve todos sus submódulos (@include)."""
    tpl_path = Path(template_path) if template_path else TEMPLATE_PATH
    if not tpl_path.exists():
        raise FileNotFoundError(f"Plantilla HTML no encontrada: {tpl_path}")
    raw_content = tpl_path.read_text(encoding="utf-8")
    return ensamblar_plantilla_modular(raw_content, base_dir=tpl_path.parent)


CAMPOS_OMITIR_FRONTEND = {
    "ofertas_cross_tienda",
    "precio_por_litro_minimo_cross",
    "tienda_mas_cara",
    "precio_maximo_cross",
}


def compactar_datos_para_frontend(datos_json_str: str) -> str:
    """
    Elimina campos anidados redundantes que no se usan en el cliente (como ofertas_cross_tienda)
    y serializa el JSON de forma compacta sin espacios innecesarios para reducir el peso de index.html.
    """
    if len(datos_json_str) < 1000 and not any(c in datos_json_str for c in CAMPOS_OMITIR_FRONTEND):
        return datos_json_str

    try:
        datos = json.loads(datos_json_str)
    except json.JSONDecodeError:
        return datos_json_str

    if not isinstance(datos, list):
        return datos_json_str

    optimizados = [
        {k: v for k, v in item.items() if k not in CAMPOS_OMITIR_FRONTEND} if isinstance(item, dict) else item
        for item in datos
    ]
    return json.dumps(optimizados, ensure_ascii=False, separators=(",", ":"))


def renderizar_plantilla(
    template_content: str,
    datos_json_str: str,
    corte_auditoria: str | None = None,
    resumen_whatsapp: str | None = None,
    campanas_json_str: str | None = None,
    base_dir: Path | None = None,
) -> str:
    """Ensambla submódulos e inyecta el catálogo JSON y variables de vigencia en la plantilla HTML."""
    cfg = obtener_configuracion_vigencia()
    corte = corte_auditoria or cfg["corte_auditoria"]
    whatsapp = resumen_whatsapp or cfg["resumen_whatsapp"]
    campanas_str = (
        campanas_json_str
        if campanas_json_str is not None
        else json.dumps(cfg["campanas"], ensure_ascii=False, separators=(",", ":"))
    )
    datos_compactos = compactar_datos_para_frontend(datos_json_str)
    ensamblada = ensamblar_plantilla_modular(template_content, base_dir=base_dir)

    return (
        ensamblada.replace("__DATA_JSON__", datos_compactos)
        .replace("__CAMPANAS_JSON__", campanas_str)
        .replace("__CORTE_AUDITORIA__", corte)
        .replace("__RESUMEN_WHATSAPP_VIGENCIAS__", whatsapp)
    )


def generar_dashboard(
    data_json_path: Path | str | None = None,
    template_path: Path | str | None = None,
    output_paths: list[Path | str] | None = None,
) -> str:
    """
    Carga los datos JSON, ensambla y renderiza la plantilla HTML modular y guarda el dashboard
    autocontenido en las rutas especificadas.
    """
    json_path = Path(data_json_path) if data_json_path else DATA_JSON_PATH
    tpl_path = Path(template_path) if template_path else TEMPLATE_PATH

    if not json_path.exists():
        raise FileNotFoundError(f"Archivo de datos no encontrado: {json_path}")
    if not tpl_path.exists():
        raise FileNotFoundError(f"Plantilla HTML no encontrada: {tpl_path}")

    datos_json_str = json_path.read_text(encoding="utf-8")
    template_content = tpl_path.read_text(encoding="utf-8")

    html_final = renderizar_plantilla(template_content, datos_json_str, base_dir=tpl_path.parent)

    # Definir destinos de salida por defecto (solo index.html, autocontenido y publicado)
    destinos = [Path(p) for p in output_paths] if output_paths is not None else [INDEX_HTML_PATH]

    # Ruta opcional de artefactos de entorno asistido
    artifact_dir = os.environ.get("ANTIGRAVITY_ARTIFACT_DIR")
    if artifact_dir and output_paths is None:
        destinos.append(Path(artifact_dir) / "dashboard_bi.html")

    for dest in destinos:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html_final, encoding="utf-8")

    logger.info("Dashboard v6.0 sincronizado exitosamente:")
    for dest in destinos:
        if dest.exists():
            logger.info(f"  - Destino:  {dest} ({dest.stat().st_size:,} bytes)")

    return html_final


def main() -> None:
    """Entry point CLI para regenerar el dashboard HTML (H50)."""
    generar_dashboard()


if __name__ == "__main__":
    main()
