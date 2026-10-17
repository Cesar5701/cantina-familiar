"""
Generador Maestro del Dashboard BI interactivo v6.0 para Cantina Familiar 2026.
Desacoplado de la plantilla HTML (H29) para máxima mantenibilidad y facilidad de prueba.
"""

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.logger import get_logger

logger = get_logger("dashboard_v4")
LOCAL_HTML_PATH = ROOT_DIR / "data" / "dashboard_bi.html"
INDEX_HTML_PATH = ROOT_DIR / "index.html"
DATA_JSON_PATH = ROOT_DIR / "data" / "dashboard_data.json"
TEMPLATE_PATH = ROOT_DIR / "src" / "templates" / "dashboard_template.html"

# =====================================================================
# MATRIZ OFICIAL DE VIGENCIAS Y PROMOCIONES MULTITIENDA (OCTUBRE 2026)
# =====================================================================
VIGENCIAS_TIENDAS = {
    "alianza": "25 de octubre 2026 (Aniversario Web)",
    "sams": "2 de noviembre 2026 (Cuponera Octubre / Día de Muertos)",
    "chedraui": "31 de octubre 2026 (Quincena MiChedraui)",
    "soriana": "22 de octubre 2026 (Folleto Semanal de Licores)",
    "walmart": "31 de octubre 2026 (Rebajas de Temporada en Línea)",
}

CONFIG_VIGENCIA = {
    "corte_auditoria": "Octubre 2026",
    "resumen_whatsapp": (
        "🟠 Bodegas Alianza: hasta 25 Oct (Aniversario)\n"
        "🔵 Sam's Club: hasta 2 Nov (Cuponera)\n"
        "🟧 Chedraui: hasta 31 Oct (Quincena)\n"
        "🔴 Soriana: hasta 22 Oct (Folleto semanal)\n"
        "🩵 Walmart: hasta 31 Oct (Rebajas)"
    ),
}


def renderizar_plantilla(
    template_content: str,
    datos_json_str: str,
    corte_auditoria: str | None = None,
    resumen_whatsapp: str | None = None,
) -> str:
    """Inyecta el catálogo JSON y variables de vigencia dentro de la plantilla HTML."""
    corte = corte_auditoria or CONFIG_VIGENCIA["corte_auditoria"]
    whatsapp = resumen_whatsapp or CONFIG_VIGENCIA["resumen_whatsapp"]

    return (
        template_content.replace("__DATA_JSON__", datos_json_str)
        .replace("__CORTE_AUDITORIA__", corte)
        .replace("__RESUMEN_WHATSAPP_VIGENCIAS__", whatsapp)
    )


def generar_dashboard(
    data_json_path: Path | str | None = None,
    template_path: Path | str | None = None,
    output_paths: list[Path | str] | None = None,
) -> str:
    """
    Carga los datos JSON, renderiza la plantilla HTML y guarda el dashboard generado
    en las rutas especificadas.
    """
    json_path = Path(data_json_path) if data_json_path else DATA_JSON_PATH
    tpl_path = Path(template_path) if template_path else TEMPLATE_PATH

    if not json_path.exists():
        raise FileNotFoundError(f"Archivo de datos no encontrado: {json_path}")
    if not tpl_path.exists():
        raise FileNotFoundError(f"Plantilla HTML no encontrada: {tpl_path}")

    datos_json_str = json_path.read_text(encoding="utf-8")
    template_content = tpl_path.read_text(encoding="utf-8")

    html_final = renderizar_plantilla(template_content, datos_json_str)

    # Definir destinos de salida por defecto
    destinos = [Path(p) for p in output_paths] if output_paths is not None else [LOCAL_HTML_PATH, INDEX_HTML_PATH]

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


if __name__ == "__main__":
    generar_dashboard()
