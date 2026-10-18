"""
Motor de procesamiento y análisis de precios de bebidas (Cantina Familiar).
Utiliza pandas para auditar datos, calcular métricas por litro, detectar duplicados
y generar rankings estrictamente separados por categorías comparables.
"""

from src.analizador.cross_tienda import (
    calcular_grupos_cross_tienda,
    detectar_duplicados,
    enriquecer_registros_cross_tienda,
    obtener_comparativa_cross_tienda,
)
from src.analizador.esquema_y_auditoria import (
    COLUMNAS_OBLIGATORIAS,
    auditar_datos_faltantes,
    cargar_datos,
    validar_esquema_y_rangos,
)
from src.analizador.metricas_y_outliers import (
    calcular_metricas,
    filtrar_catalogo_dashboard,
    marcar_outliers_lujo,
)
from src.analizador.normalizacion import (
    REGLAS_NORMALIZACION_CLAVE,
    STOP_WORDS_CLAVE,
    ReglaNormalizacion,
    es_producto_paquete,
    normalizar_texto_clave,
)
from src.analizador.rankings_y_cli import (
    generar_rankings_por_categoria,
    imprimir_resumen_rankings,
    main,
    procesar_archivo,
)

__all__ = [
    "COLUMNAS_OBLIGATORIAS",
    "REGLAS_NORMALIZACION_CLAVE",
    "STOP_WORDS_CLAVE",
    "ReglaNormalizacion",
    "auditar_datos_faltantes",
    "calcular_grupos_cross_tienda",
    "calcular_metricas",
    "cargar_datos",
    "detectar_duplicados",
    "enriquecer_registros_cross_tienda",
    "es_producto_paquete",
    "filtrar_catalogo_dashboard",
    "generar_rankings_por_categoria",
    "imprimir_resumen_rankings",
    "main",
    "marcar_outliers_lujo",
    "normalizar_texto_clave",
    "obtener_comparativa_cross_tienda",
    "procesar_archivo",
    "validar_esquema_y_rangos",
]
