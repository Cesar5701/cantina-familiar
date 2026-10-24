"""
Generador Maestro del Dashboard BI interactivo v6.0 para Cantina Familiar 2026.
Desacoplado en arquitectura modular de plantillas (CSS, parciales HTML y módulos JS)
que se ensamblan en un index.html autocontenido para publicación en GitHub Pages (H29).
"""

import os
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.logger import get_logger

logger = get_logger("dashboard_v4")
INDEX_HTML_PATH = ROOT_DIR / "index.html"
DATA_JSON_PATH = ROOT_DIR / "data" / "dashboard_data.json"
TEMPLATES_DIR = ROOT_DIR / "src" / "templates"
TEMPLATE_PATH = TEMPLATES_DIR / "dashboard_template.html"

PATRON_INCLUDE = re.compile(r"<!--\s*@include\s+([^\s]+)\s*-->\n?")

# =====================================================================
# MATRIZ OFICIAL DE VIGENCIAS Y PROMOCIONES MULTITIENDA (OCTUBRE 2026)
# =====================================================================
CONFIG_VIGENCIA = {
    "corte_auditoria": "Octubre 2026",
    "resumen_whatsapp": (
        "Bodegas Alianza: hasta 25 Oct (Aniversario)\n"
        "Sam's Club: hasta 2 Nov (Cuponera)\n"
        "Costco: hasta 31 Oct (Cuponera Ahorros)\n"
        "Chedraui: hasta 31 Oct (Quincena)\n"
        "Soriana: hasta 22 Oct (Folleto semanal)\n"
        "Walmart: hasta 31 Oct (Rebajas)"
    ),
}


def ensamblar_plantilla_modular(template_content: str, base_dir: Path | None = None) -> str:
    """Expande las directivas <!-- @include ruta --> leyendo los submódulos de CSS, HTML y JS."""
    directorio_base = base_dir or TEMPLATES_DIR

    def _reemplazar_include(match: re.Match) -> str:
        rel_path = match.group(1)
        inc_path = directorio_base / rel_path
        if not inc_path.exists():
            raise FileNotFoundError(f"Módulo de plantilla no encontrado: {inc_path}")
        return inc_path.read_text(encoding="utf-8")

    return PATRON_INCLUDE.sub(_reemplazar_include, template_content)


def cargar_plantilla_dashboard(template_path: Path | str | None = None) -> str:
    """Lee la plantilla maestra y resuelve todos sus submódulos (@include)."""
    tpl_path = Path(template_path) if template_path else TEMPLATE_PATH
    if not tpl_path.exists():
        raise FileNotFoundError(f"Plantilla HTML no encontrada: {tpl_path}")
    raw_content = tpl_path.read_text(encoding="utf-8")
    return ensamblar_plantilla_modular(raw_content, base_dir=tpl_path.parent)


def renderizar_plantilla(
    template_content: str,
    datos_json_str: str,
    corte_auditoria: str | None = None,
    resumen_whatsapp: str | None = None,
    base_dir: Path | None = None,
) -> str:
    """Ensambla submódulos e inyecta el catálogo JSON y variables de vigencia en la plantilla HTML."""
    corte = corte_auditoria or CONFIG_VIGENCIA["corte_auditoria"]
    whatsapp = resumen_whatsapp or CONFIG_VIGENCIA["resumen_whatsapp"]
    ensamblada = ensamblar_plantilla_modular(template_content, base_dir=base_dir)

    return (
        ensamblada.replace("__DATA_JSON__", datos_json_str)
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
