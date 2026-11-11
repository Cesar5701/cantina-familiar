"""
Paquete de interfaz web y ensamblaje del Dashboard BI interactivo para Cantina Familiar.
"""

from src.interfaz.compilador_web import (
    DATA_JSON_PATH,
    INDEX_HTML_PATH,
    TEMPLATE_PATH,
    TEMPLATES_DIR,
    cargar_plantilla_dashboard,
    ensamblar_plantilla_modular,
    generar_dashboard,
    main,
    renderizar_plantilla,
)

__all__ = [
    "DATA_JSON_PATH",
    "INDEX_HTML_PATH",
    "TEMPLATES_DIR",
    "TEMPLATE_PATH",
    "cargar_plantilla_dashboard",
    "ensamblar_plantilla_modular",
    "generar_dashboard",
    "main",
    "renderizar_plantilla",
]
