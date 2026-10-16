"""
Suite de pruebas unitarias para Sprint 2:
- H8: Deduplicación y comparativas de precios cross-tienda (obtener_comparativa_cross_tienda).
- H9: Validación exhaustiva de esquema y rangos (validar_esquema_y_rangos).
- H10: Operaciones atómicas de guardado (guardar_csv_atomico, guardar_json_atomico, ResumenScraping).
"""

import os
import tempfile

import numpy as np
import pandas as pd
import pytest

from src.analizador import (
    detectar_duplicados,
    obtener_comparativa_cross_tienda,
    validar_esquema_y_rangos,
)
from src.io_utils import ResumenScraping, guardar_csv_atomico, guardar_json_atomico


def crear_df_prueba(filas: list[dict]) -> pd.DataFrame:
    base = {
        "tienda": "Bodegas Alianza",
        "producto": "Tequila Dobel Diamante 750 ml",
        "marca": "Maestro Dobel",
        "categoria": "Tequila",
        "subcategoria": "Añejo Cristalino",
        "clase": "Añejo Cristalino",
        "tipo_mezcal": "no_aplica",
        "especie_agave": "Tequilana Weber azul",
        "productor": "José Cuervo",
        "sello_regulador": "sí",
        "ml": 750,
        "abv": 35.0,
        "precio_regular": 750.0,
        "precio_promo": 650.0,
        "unidades_promo": 1,
        "precio_total_promo": 650.0,
        "condiciones": "Precio regular",
        "disponibilidad": "disponible",
        "url": "https://tienda.com/producto",
        "fecha_consulta": "2026-10-16 12:00",
        "fuente": "Test",
        "confianza": "Confirmado",
    }
    registros = []
    for f in filas:
        item = base.copy()
        item.update(f)
        registros.append(item)
    return pd.DataFrame(registros)


# ---------------------------------------------------------------------------
# Pruebas H8: Deduplicación y Comparativa Cross-Tienda
# ---------------------------------------------------------------------------


def test_deteccion_cross_tienda_multiples_tiendas():
    """Valida que un mismo producto cotizado en diferentes tiendas se marque como comparable."""
    df = crear_df_prueba(
        [
            {
                "tienda": "Bodegas Alianza",
                "producto": "Tequila Dobel Diamante 750 ml",
                "ml": 750,
                "precio_promo": 650.0,
            },
            {"tienda": "Sam's Club", "producto": "Tequila Dobel Diamante 750 ml", "ml": 750, "precio_promo": 599.0},
            {"tienda": "Walmart", "producto": "Tequila Dobel Diamante 750 ml", "ml": 750, "precio_promo": 680.0},
            {"tienda": "Chedraui", "producto": "Whisky Johnnie Walker Black 750 ml", "ml": 750, "precio_promo": 720.0},
        ]
    )
    df = detectar_duplicados(df)

    assert "clave_comparativa" in df.columns
    assert "es_comparable_cross_tienda" in df.columns
    assert "num_tiendas_disponibles" in df.columns

    # Dobel Diamante está en 3 tiendas -> es comparable
    assert df.loc[0, "es_comparable_cross_tienda"]
    assert df.loc[1, "es_comparable_cross_tienda"]
    assert df.loc[2, "es_comparable_cross_tienda"]
    assert df.loc[0, "num_tiendas_disponibles"] == 3

    # Johnnie Walker solo está en Chedraui -> no es comparable
    assert not df.loc[3, "es_comparable_cross_tienda"]
    assert df.loc[3, "num_tiendas_disponibles"] == 1


def test_obtener_comparativa_cross_tienda_calculo_arbitraje():
    """Valida que la tabla de comparativas calcule tienda más barata, más cara y ahorro máximo."""
    df = crear_df_prueba(
        [
            {"tienda": "Bodegas Alianza", "producto": "Don Julio 70 700 ml", "ml": 700, "precio_promo": 780.0},
            {"tienda": "Walmart", "producto": "Don Julio 70 700 ml", "ml": 700, "precio_promo": 950.0},
            {"tienda": "Soriana", "producto": "Don Julio 70 700 ml", "ml": 700, "precio_promo": 850.0},
        ]
    )
    df_comp = obtener_comparativa_cross_tienda(df)

    assert not df_comp.empty
    assert len(df_comp) == 1
    fila = df_comp.iloc[0]

    assert fila["tienda_mas_barata"] == "Bodegas Alianza"
    assert fila["precio_minimo"] == 780.0
    assert fila["tienda_mas_cara"] == "Walmart"
    assert fila["precio_maximo"] == 950.0
    assert fila["ahorro_maximo"] == 170.0  # 950 - 780
    assert fila["tiendas_disponibles"] == ["Bodegas Alianza", "Soriana", "Walmart"]


# ---------------------------------------------------------------------------
# Pruebas H9: Validación de Esquema y Rangos
# ---------------------------------------------------------------------------


def test_validar_esquema_y_rangos_dataset_valido():
    """Un dataset correcto no debe arrojar anomalías."""
    df = crear_df_prueba(
        [
            {"producto": "Botella 1", "ml": 750, "abv": 38.0, "precio_promo": 500.0},
            {"producto": "Botella 2", "ml": 1000, "abv": 40.0, "precio_promo": 750.0},
        ]
    )
    df_val, reporte = validar_esquema_y_rangos(df)

    assert reporte["total_registros"] == 2
    assert reporte["registros_validos"] == 2
    assert reporte["anomalias_volumen_ml"] == 0
    assert reporte["anomalias_graduacion_abv"] == 0
    assert reporte["registros_sin_precio"] == 0
    assert df_val["datos_validos"].all()


def test_validar_esquema_y_rangos_deteccion_anomalias():
    """Detecta volúmenes absurdos, graduaciones imposibles y precios ausentes."""
    df = crear_df_prueba(
        [
            {"producto": "Volumen Nulo", "ml": np.nan, "precio_promo": 500.0},
            {"producto": "Volumen Fuera de Rango", "ml": 25000, "precio_promo": 500.0},
            {"producto": "ABV Imposible", "ml": 750, "abv": 150.0, "precio_promo": 500.0},
            {
                "producto": "Sin Precio",
                "ml": 750,
                "precio_regular": np.nan,
                "precio_promo": np.nan,
                "precio_total_promo": np.nan,
            },
        ]
    )
    df_val, reporte = validar_esquema_y_rangos(df)

    assert reporte["total_registros"] == 4
    assert reporte["anomalias_volumen_ml"] == 2  # NaN y 25000
    assert reporte["anomalias_graduacion_abv"] == 1  # 150.0%
    assert reporte["registros_sin_precio"] == 1  # Sin precio


def test_validar_esquema_columnas_faltantes():
    """Si faltan columnas requeridas y lanzar_error=True, debe lanzar ValueError."""
    df_incompleto = pd.DataFrame([{"producto": "Incompleto"}])
    with pytest.raises(ValueError, match="El dataset no contiene las columnas requeridas"):
        validar_esquema_y_rangos(df_incompleto, lanzar_error=True)


# ---------------------------------------------------------------------------
# Pruebas H10: I/O Atómico y Resumen de Scraping
# ---------------------------------------------------------------------------


def test_guardar_csv_atomico():
    """Verifica que el guardado atómico cree el archivo y reemplace sin corrupción."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ruta = os.path.join(tmpdir, "test_atomico.csv")
        df = pd.DataFrame([{"id": 1, "nombre": "Producto A"}, {"id": 2, "nombre": "Producto B"}])

        guardar_csv_atomico(df, ruta)
        assert os.path.exists(ruta)

        df_leido = pd.read_csv(ruta)
        assert len(df_leido) == 2
        assert list(df_leido["nombre"]) == ["Producto A", "Producto B"]


def test_guardar_json_atomico():
    """Verifica la escritura atómica de archivos JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ruta = os.path.join(tmpdir, "test_atomico.json")
        data = [{"id": 100, "tienda": "Alianza"}]

        guardar_json_atomico(data, ruta)
        assert os.path.exists(ruta)

        import json

        with open(ruta, "r", encoding="utf-8") as f:
            cargado = json.load(f)
        assert cargado == data


def test_resumen_scraping_metricas():
    """Valida el acumulador estructurado de métricas de scraping."""
    resumen = ResumenScraping("Walmart")
    resumen.registrar_exito()
    resumen.registrar_exito()
    resumen.registrar_descarte("artículo no alcohólico")
    resumen.registrar_error_red("https://test.com", ConnectionError("Timeout"))

    data = resumen.a_dict()
    assert data["tienda"] == "Walmart"
    assert data["total_consultados"] == 4
    assert data["exitosos"] == 2
    assert data["descartados_criterio"] == 1
    assert data["fallos_red"] == 1
    assert len(data["errores"]) == 1


def test_h6_pack_x_n_multipack():
    """Valida que los formatos Pack x N y x N multipliquen correctamente el volumen (H6)."""
    from src.clasificacion import extraer_ml

    # Caso reportado en auditoría: Walmart Pack x 3 Blue Label 750 ml -> 2250 ml
    assert extraer_ml("Walmart | Pack x 3 Whisky Johnnie Walker Blue Label 750 ml") == 2250
    # Caso alternativo: Buchanan's x 2 750 ml -> 1500 ml
    assert extraer_ml("Whisky Buchanan's x 2 750 ml") == 1500
    # Caso mayúsculas: PACK X 6 Cerveza / Tequila 700 ml -> 4200 ml
    assert extraer_ml("PACK X 6 Tequila 700 ml") == 4200


def test_h8_normalizar_texto_clave_orden_tokens():
    """Valida que títulos con orden invertido de palabras generen la misma clave comparativa (H8)."""
    from src.analizador import normalizar_texto_clave

    clave1 = normalizar_texto_clave("Tequila 1800 Cristalino Añejo 700 ml")
    clave2 = normalizar_texto_clave("Tequila 1800 Añejo Cristalino 700 ml")
    assert clave1 == clave2

    clave_don1 = normalizar_texto_clave("Tequila Añejo Cristalino Don Julio 70 700 ml")
    clave_don2 = normalizar_texto_clave("Tequila Don Julio 70 Añejo Cristalino 700 ml")
    assert clave_don1 == clave_don2


def test_h8_enriquecimiento_cross_tienda_dashboard_json():
    """Valida que dashboard_data.json contenga los campos cross-tienda requeridos por el frontend."""
    import json
    from pathlib import Path

    from src.actualizar_dashboard_completo import actualizar_todo

    raiz = Path(__file__).resolve().parent.parent
    ruta_json = raiz / "data" / "dashboard_data.json"

    # Si no existe previamente (ej. en un clone limpio o CI), se genera
    if not ruta_json.exists():
        actualizar_todo()

    assert ruta_json.exists()

    with open(ruta_json, "r", encoding="utf-8") as f:
        datos = json.load(f)

    comparables = [d for d in datos if d.get("es_comparable_cross_tienda")]
    assert len(comparables) > 0

    item = comparables[0]
    campos_requeridos = [
        "clave_comparativa",
        "es_comparable_cross_tienda",
        "num_tiendas_cross",
        "tienda_mas_barata",
        "precio_minimo_cross",
        "tienda_mas_cara",
        "precio_maximo_cross",
        "ahorro_maximo_cross",
        "es_precio_mas_bajo",
        "diferencia_vs_minimo",
        "ofertas_cross_tienda",
    ]
    for c in campos_requeridos:
        assert c in item, f"Falta campo requerido: {c}"

    assert isinstance(item["ofertas_cross_tienda"], list)
    assert len(item["ofertas_cross_tienda"]) >= 1
    assert "tienda" in item["ofertas_cross_tienda"][0]
    assert "precio_promo" in item["ofertas_cross_tienda"][0]
