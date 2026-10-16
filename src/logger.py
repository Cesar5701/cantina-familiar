"""
Sistema Centralizado de Logging Estructurado (H19).

Proporciona registros con niveles (DEBUG, INFO, WARNING, ERROR), salida legible en consola
y persistencia automática en logs/cantina_familiar.log para auditoría y diagnóstico de pipelines.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
DIR_LOGS = RAIZ_PROYECTO / "logs"
ARCHIVO_LOG_DEFAULT = DIR_LOGS / "cantina_familiar.log"


class FormateadorConsola(logging.Formatter):
    """Formateador limpio para consola con iconos de nivel."""

    ICONOS = {
        logging.DEBUG: "🔍 [DEBUG]",
        logging.INFO: "ℹ️ [INFO]",
        logging.WARNING: "⚠️ [AVISO]",
        logging.ERROR: "❌ [ERROR]",
        logging.CRITICAL: "🚨 [CRÍTICO]",
    }

    def format(self, record: logging.LogRecord) -> str:
        prefijo = self.ICONOS.get(record.levelno, "[LOG]")
        mensaje = record.getMessage()
        if record.levelno >= logging.WARNING:
            return f"{prefijo} {record.name}: {mensaje}"
        return f"{prefijo} {mensaje}"


def configurar_logging(
    nivel: Optional[str] = None,
    archivo_log: Optional[Path] = None,
    rotacion_bytes: int = 2 * 1024 * 1024,  # 2 MB
    backups: int = 3,
    forzar: bool = False,
) -> None:
    """Configura el logger raíz del proyecto con salida a consola y archivo."""
    nivel_str = nivel or os.environ.get("LOG_LEVEL", "INFO").upper()
    nivel_numerico = getattr(logging, nivel_str, logging.INFO)

    logger_raiz = logging.getLogger("cantina_familiar")
    logger_raiz.setLevel(nivel_numerico)

    # Evitar duplicar handlers en reinvocaciones a menos que se fuerce
    if logger_raiz.handlers:
        if not forzar:
            return
        for h in list(logger_raiz.handlers):
            logger_raiz.removeHandler(h)
            try:
                h.close()
            except Exception:
                pass

    # 1. Handler de Consola
    handler_consola = logging.StreamHandler(sys.stdout)
    handler_consola.setLevel(nivel_numerico)
    handler_consola.setFormatter(FormateadorConsola())
    logger_raiz.addHandler(handler_consola)

    # 2. Handler de Archivo (Persistente con rotación)
    try:
        DIR_LOGS.mkdir(parents=True, exist_ok=True)
        ruta_archivo = archivo_log or ARCHIVO_LOG_DEFAULT
        handler_archivo = RotatingFileHandler(
            ruta_archivo, maxBytes=rotacion_bytes, backupCount=backups, encoding="utf-8"
        )
        handler_archivo.setLevel(logging.DEBUG)  # Archivo siempre captura todo para depuración
        formato_archivo = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler_archivo.setFormatter(formato_archivo)
        logger_raiz.addHandler(handler_archivo)
    except Exception as e:
        sys.stderr.write(f"Aviso: No se pudo inicializar archivo de log: {e}\n")


def get_logger(modulo: str = "") -> logging.Logger:
    """
    Obtiene una instancia de logger para el módulo especificado.

    Ejemplo:
        from src.logger import get_logger
        logger = get_logger("scraper_multitienda")
        logger.info("Iniciando extracción...")
    """
    configurar_logging()
    if modulo:
        return logging.getLogger(f"cantina_familiar.{modulo}")
    return logging.getLogger("cantina_familiar")
