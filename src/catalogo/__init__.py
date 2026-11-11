"""
Paquete de Motor de Catálogo, Reglas NOM, Arbitraje y Series Históricas.

Centraliza la denominación de origen (NOM-006 y NOM-070), detección de volumen,
filtrado de mercancía, validación de esquema, detección de anomalías, arbitraje
cross-tienda, campañas promocionales y series históricas de precios.
"""

from src.catalogo.arbitraje_precios import (
    calcular_grupos_cross_tienda,
    detectar_duplicados,
    enriquecer_registros_cross_tienda,
    obtener_comparativa_cross_tienda,
)
from src.catalogo.campanas_promocionales import (
    METADATOS_CAMPANAS_TIENDAS,
    detectar_campanas_por_tienda,
    detectar_nombre_campana,
    extraer_vigencia_de_textos,
    formatear_fecha_corte,
    generar_resumen_whatsapp,
    guardar_campanas_json,
    parsear_fecha_iso,
)
from src.catalogo.constantes import (
    CATEGORIAS_COMPARABLES_VALIDAS,
    KEYWORDS_BLENDED_WHISKY,
    KEYWORDS_SILVESTRES,
    LIMITES_PRESUPUESTO_DASHBOARD,
    MARCAS_REPOSADO_CRISTALINO_POR_NORMA,
    PALABRAS_EXCLUIDAS,
    TECHOS_LITRO_OUTLIERS,
)
from src.catalogo.denominacion_nom import (
    REGLAS_AGAVE_MEZCAL,
    clasificar_agave_mezcal,
    clasificar_categoria,
    clasificar_estricto,
    detectar_categoria_base,
)
from src.catalogo.deteccion_anomalias import (
    calcular_metricas,
    filtrar_catalogo_dashboard,
    marcar_outliers_lujo,
)
from src.catalogo.detector_volumen import (
    corregir_ml_producto,
    extraer_ml,
    limpiar_obsequios_mezcladores_para_volumen,
    limpiar_precio,
    normalizar_medidas_en_nombre,
)
from src.catalogo.esquema_y_auditoria import (
    COLUMNAS_OBLIGATORIAS,
    auditar_datos_faltantes,
    cargar_datos,
    validar_esquema_y_rangos,
)
from src.catalogo.filtros_mercancia import (
    es_mercancia_o_no_bebible,
    generar_etiqueta_condicion,
    sincronizar_clasificacion_catalogo,
)
from src.catalogo.normalizacion_texto import (
    REGLAS_NORMALIZACION_CLAVE,
    STOP_WORDS_CLAVE,
    ReglaNormalizacion,
    es_producto_paquete,
    normalizar_texto_clave,
)
from src.catalogo.rankings_cli import (
    generar_rankings_por_categoria,
    imprimir_resumen_rankings,
    main,
    procesar_archivo,
)
from src.catalogo.series_historicas import (
    construir_historial_desde_git,
    consultar_historial,
    enriquecer_con_metricas_historicas,
    extraer_archivo_git,
    formatear_tabla_historial,
    normalizar_df_para_historial,
    obtener_snapshots_git,
    registrar_precios_historicos,
)

__all__ = [
    "CATEGORIAS_COMPARABLES_VALIDAS",
    "COLUMNAS_OBLIGATORIAS",
    "KEYWORDS_BLENDED_WHISKY",
    "KEYWORDS_SILVESTRES",
    "LIMITES_PRESUPUESTO_DASHBOARD",
    "MARCAS_REPOSADO_CRISTALINO_POR_NORMA",
    "METADATOS_CAMPANAS_TIENDAS",
    "PALABRAS_EXCLUIDAS",
    "REGLAS_AGAVE_MEZCAL",
    "REGLAS_NORMALIZACION_CLAVE",
    "ReglaNormalizacion",
    "STOP_WORDS_CLAVE",
    "TECHOS_LITRO_OUTLIERS",
    "auditar_datos_faltantes",
    "calcular_grupos_cross_tienda",
    "calcular_metricas",
    "cargar_datos",
    "clasificar_agave_mezcal",
    "clasificar_categoria",
    "clasificar_estricto",
    "construir_historial_desde_git",
    "consultar_historial",
    "corregir_ml_producto",
    "detectar_campanas_por_tienda",
    "detectar_categoria_base",
    "detectar_duplicados",
    "detectar_nombre_campana",
    "enriquecer_con_metricas_historicas",
    "enriquecer_registros_cross_tienda",
    "es_mercancia_o_no_bebible",
    "es_producto_paquete",
    "extraer_archivo_git",
    "extraer_ml",
    "extraer_vigencia_de_textos",
    "filtrar_catalogo_dashboard",
    "formatear_fecha_corte",
    "formatear_tabla_historial",
    "generar_etiqueta_condicion",
    "generar_rankings_por_categoria",
    "generar_resumen_whatsapp",
    "guardar_campanas_json",
    "imprimir_resumen_rankings",
    "limpiar_obsequios_mezcladores_para_volumen",
    "limpiar_precio",
    "main",
    "marcar_outliers_lujo",
    "normalizar_df_para_historial",
    "normalizar_medidas_en_nombre",
    "normalizar_texto_clave",
    "obtener_comparativa_cross_tienda",
    "obtener_snapshots_git",
    "parsear_fecha_iso",
    "procesar_archivo",
    "registrar_precios_historicos",
    "sincronizar_clasificacion_catalogo",
    "validar_esquema_y_rangos",
]
