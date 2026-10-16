"""
Suite de pruebas unitarias para Sprint 2:
- H8: Deduplicación y comparativas de precios cross-tienda (obtener_comparativa_cross_tienda).
- H9: Validación exhaustiva de esquema y rangos (validar_esquema_y_rangos).
- H10: Operaciones atómicas de guardado (guardar_csv_atomico, guardar_json_atomico, ResumenScraping).
"""

import os
import tempfile
import pytest
import pandas as pd
import numpy as np

from src.analizador import (
    detectar_duplicados,
    obtener_comparativa_cross_tienda,
    validar_esquema_y_rangos,
    COLUMNAS_OBLIGATORIAS
)
from src.io_utils import (
    guardar_csv_atomico,
    guardar_json_atomico,
    ResumenScraping
)


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
        "confianza": "Confirmado"
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
    df = crear_df_prueba([
        {"tienda": "Bodegas Alianza", "producto": "Tequila Dobel Diamante 750 ml", "ml": 750, "precio_promo": 650.0},
        {"tienda": "Sam's Club", "producto": "Tequila Dobel Diamante 750 ml", "ml": 750, "precio_promo": 599.0},
        {"tienda": "Walmart", "producto": "Tequila Dobel Diamante 750 ml", "ml": 750, "precio_promo": 680.0},
        {"tienda": "Chedraui", "producto": "Whisky Johnnie Walker Black 750 ml", "ml": 750, "precio_promo": 720.0}
    ])
    df = detectar_duplicados(df)

    assert "clave_comparativa" in df.columns
    assert "es_comparable_cross_tienda" in df.columns
    assert "num_tiendas_disponibles" in df.columns

    # Dobel Diamante está en 3 tiendas -> es comparable
    assert df.loc[0, "es_comparable_cross_tienda"] == True
    assert df.loc[1, "es_comparable_cross_tienda"] == True
    assert df.loc[2, "es_comparable_cross_tienda"] == True
    assert df.loc[0, "num_tiendas_disponibles"] == 3

    # Johnnie Walker solo está en Chedraui -> no es comparable
    assert df.loc[3, "es_comparable_cross_tienda"] == False
    assert df.loc[3, "num_tiendas_disponibles"] == 1


def test_obtener_comparativa_cross_tienda_calculo_arbitraje():
    """Valida que la tabla de comparativas calcule tienda más barata, más cara y ahorro máximo."""
    df = crear_df_prueba([
        {"tienda": "Bodegas Alianza", "producto": "Don Julio 70 700 ml", "ml": 700, "precio_promo": 780.0},
        {"tienda": "Walmart", "producto": "Don Julio 70 700 ml", "ml": 700, "precio_promo": 950.0},
        {"tienda": "Soriana", "producto": "Don Julio 70 700 ml", "ml": 700, "precio_promo": 850.0}
    ])
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
    df = crear_df_prueba([
        {"producto": "Botella 1", "ml": 750, "abv": 38.0, "precio_promo": 500.0},
        {"producto": "Botella 2", "ml": 1000, "abv": 40.0, "precio_promo": 750.0}
    ])
    df_val, reporte = validar_esquema_y_rangos(df)

    assert reporte["total_registros"] == 2
    assert reporte["registros_validos"] == 2
    assert reporte["anomalias_volumen_ml"] == 0
    assert reporte["anomalias_graduacion_abv"] == 0
    assert reporte["registros_sin_precio"] == 0
    assert df_val["datos_validos"].all()


def test_validar_esquema_y_rangos_deteccion_anomalias():
    """Detecta volúmenes absurdos, graduaciones imposibles y precios ausentes."""
    df = crear_df_prueba([
        {"producto": "Volumen Nulo", "ml": np.nan, "precio_promo": 500.0},
        {"producto": "Volumen Fuera de Rango", "ml": 25000, "precio_promo": 500.0},
        {"producto": "ABV Imposible", "ml": 750, "abv": 150.0, "precio_promo": 500.0},
        {"producto": "Sin Precio", "ml": 750, "precio_regular": np.nan, "precio_promo": np.nan, "precio_total_promo": np.nan}
    ])
    df_val, reporte = validar_esquema_y_rangos(df)

    assert reporte["total_registros"] == 4
    assert reporte["anomalias_volumen_ml"] == 2      # NaN y 25000
    assert reporte["anomalias_graduacion_abv"] == 1  # 150.0%
    assert reporte["registros_sin_precio"] == 1      # Sin precio


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
