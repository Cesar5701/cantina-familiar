"""
Utilidades de Entrada/Salida Atómica y Registro de Ejecución (H10).

Garantiza que la escritura de datasets CSV y JSON en disco sea atómica
(escribiendo primero a un archivo temporal y reemplazando con os.replace),
evitando la corrupción de datos ante caídas de red, cancelaciones o errores de scraping.
"""

import json
import os
import tempfile
from typing import Any, Dict, List, Optional

import pandas as pd

from src.logger import get_logger

logger = get_logger("io_utils")


def guardar_csv_atomico(df: pd.DataFrame, ruta_archivo: str, **kwargs) -> str:
    """
    Guarda un DataFrame de pandas en formato CSV de forma atómica.

    Escribe primero en un archivo temporal en el mismo directorio y realiza
    un os.replace atómico, evitando estados intermedios o archivos corruptos.
    """
    directorio = os.path.dirname(os.path.abspath(ruta_archivo))
    os.makedirs(directorio, exist_ok=True)

    # kwargs por defecto si no se especifican
    if "index" not in kwargs:
        kwargs["index"] = False
    if "encoding" not in kwargs:
        kwargs["encoding"] = "utf-8"

    fd, ruta_tmp = tempfile.mkstemp(dir=directorio, prefix=".tmp_", suffix=".csv")
    os.close(fd)

    try:
        df.to_csv(ruta_tmp, **kwargs)
        os.replace(ruta_tmp, ruta_archivo)
    except (OSError, TypeError, ValueError):
        if os.path.exists(ruta_tmp):
            os.remove(ruta_tmp)
        raise

    return ruta_archivo


def guardar_json_atomico(data: Any, ruta_archivo: str, indent: Optional[int] = None, ensure_ascii: bool = False) -> str:
    """
    Guarda una estructura de datos en formato JSON de forma atómica.
    """
    directorio = os.path.dirname(os.path.abspath(ruta_archivo))
    os.makedirs(directorio, exist_ok=True)

    fd, ruta_tmp = tempfile.mkstemp(dir=directorio, prefix=".tmp_", suffix=".json")
    try:
        with open(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=ensure_ascii, indent=indent)
        os.replace(ruta_tmp, ruta_archivo)
    except (OSError, TypeError, ValueError):
        if os.path.exists(ruta_tmp):
            os.remove(ruta_tmp)
        raise

    return ruta_archivo


class ResumenScraping:
    """Registra y reporta el conteo estructurado de éxitos, fallos y omisiones de un scraper."""

    def __init__(self, tienda: str):
        self.tienda = tienda
        self.total_consultados: int = 0
        self.exitosos: int = 0
        self.descartados_criterio: int = 0
        self.fallos_red: int = 0
        self.errores_parseo: int = 0
        self.motivos_descarte: Dict[str, int] = {}
        self.detalles_errores: List[str] = []

    def registrar_exito(self):
        self.total_consultados += 1
        self.exitosos += 1

    def registrar_descarte(self, motivo: str = ""):
        self.total_consultados += 1
        self.descartados_criterio += 1
        clave = motivo or "sin_especificar"
        self.motivos_descarte[clave] = self.motivos_descarte.get(clave, 0) + 1

    def registrar_error_red(self, url_o_termino: str, error: Exception):
        self.total_consultados += 1
        self.fallos_red += 1
        self.detalles_errores.append(f"Red [{url_o_termino}]: {error}")

    def registrar_error_parseo(self, producto: str, error: Exception):
        self.total_consultados += 1
        self.errores_parseo += 1
        self.detalles_errores.append(f"Parseo [{producto}]: {error}")

    def a_dict(self) -> Dict[str, Any]:
        return {
            "tienda": self.tienda,
            "total_consultados": self.total_consultados,
            "exitosos": self.exitosos,
            "descartados_criterio": self.descartados_criterio,
            "fallos_red": self.fallos_red,
            "errores_parseo": self.errores_parseo,
            "motivos_descarte": self.motivos_descarte,
            "errores": self.detalles_errores[:10],  # Limitar a primeros 10
        }

    def imprimir_resumen(self):
        logger.info(f"--- Resumen de Extracción: {self.tienda} ---")
        logger.info(f"  Total procesados: {self.total_consultados}")
        logger.info(f"  Exitosos válidos: {self.exitosos}")
        logger.info(f"  Descartados (criterio/rango): {self.descartados_criterio}")
        logger.info(f"  Fallos de red: {self.fallos_red}")
        logger.info(f"  Errores de parseo: {self.errores_parseo}")
        if self.detalles_errores:
            logger.warning(f"  Primeros errores: {self.detalles_errores[:3]}")
