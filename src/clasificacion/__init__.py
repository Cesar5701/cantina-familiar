"""
Paquete Unificado de Clasificación, Normalización de Volumen y Reglas NOM.

Concentra la lógica de negocio del proyecto (NOM-006 para Tequila, NOM-070 para Mezcal,
Whisky Blended Scotch, Licor Honey y Vino Tinto de Mesa/Clericot) resolviendo los
hallazgos H1 y H2 de la auditoría técnica.
"""

from src.clasificacion.constantes import (
    CATEGORIAS_COMPARABLES_VALIDAS,
    KEYWORDS_BLENDED_WHISKY,
    KEYWORDS_SILVESTRES,
    LIMITES_PRESUPUESTO_DASHBOARD,
    MARCAS_REPOSADO_CRISTALINO_POR_NORMA,
    PALABRAS_EXCLUIDAS,
    TECHOS_LITRO_OUTLIERS,
)
from src.clasificacion.filtros_y_catalogo import (
    es_mercancia_o_no_bebible,
    generar_etiqueta_condicion,
    sincronizar_clasificacion_catalogo,
)
from src.clasificacion.reglas_nom import (
    clasificar_agave_mezcal,
    clasificar_categoria,
    clasificar_estricto,
    detectar_categoria_base,
)
from src.clasificacion.volumen_y_precios import (
    corregir_ml_producto,
    extraer_ml,
    limpiar_precio,
    normalizar_medidas_en_nombre,
)

__all__ = [
    "CATEGORIAS_COMPARABLES_VALIDAS",
    "KEYWORDS_BLENDED_WHISKY",
    "KEYWORDS_SILVESTRES",
    "LIMITES_PRESUPUESTO_DASHBOARD",
    "MARCAS_REPOSADO_CRISTALINO_POR_NORMA",
    "PALABRAS_EXCLUIDAS",
    "TECHOS_LITRO_OUTLIERS",
    "clasificar_agave_mezcal",
    "clasificar_categoria",
    "clasificar_estricto",
    "corregir_ml_producto",
    "detectar_categoria_base",
    "es_mercancia_o_no_bebible",
    "extraer_ml",
    "generar_etiqueta_condicion",
    "limpiar_precio",
    "normalizar_medidas_en_nombre",
    "sincronizar_clasificacion_catalogo",
]
