"""
Suite de pruebas unitarias (pytest) para el analizador de bebidas.
Verifica:
- Conversión de ml a litros y cálculo de precio por litro.
- Descuentos y ahorro verificable.
- Costo efectivo en promociones multiunidad (3x2, packs).
- Detección de duplicados.
- Auditoría de datos faltantes.
- Distinción estricta de categorías en Tequila (Añejo vs Cristalino vs Reposado).
- Distinción estricta en Mezcal (Reposado vs Añejo vs Silvestres).
"""

import numpy as np
import pytest

from src.analizador import (
    auditar_datos_faltantes,
    calcular_metricas,
    detectar_duplicados,
    generar_rankings_por_categoria,
)
from tests.conftest import crear_df_base


# 1. Prueba de conversión ml a litros y cálculo de precio por litro
@pytest.mark.parametrize(
    "ml,precio_unitario,litros_esperados,precio_litro_esperado",
    [
        (700, 600.00, 0.70, 857.14),
        (750, 777.00, 0.75, 1036.00),
        (1000, 650.00, 1.00, 650.00),
        (1750, 627.10, 1.75, 358.34),
        (2000, 470.00, 2.00, 235.00),
        (946, 83.00, 0.946, 87.74),
        (4000, 437.83, 4.00, 109.46),
    ],
)
def test_conversion_ml_a_litros(ml, precio_unitario, litros_esperados, precio_litro_esperado):
    df = crear_df_base([{"ml": ml, "precio_promo": precio_unitario, "precio_regular": precio_unitario}])
    df = calcular_metricas(df)

    assert round(df.loc[0, "litros"], 3) == round(litros_esperados, 3)
    assert df.loc[0, "precio_por_litro"] == precio_litro_esperado


# 2. Prueba de cálculo de descuentos y ahorro verificable
def test_calculo_descuentos_y_ahorros():
    df = crear_df_base(
        [
            {"producto": "Con Descuento", "precio_regular": 885.00, "precio_promo": 600.00},
            {"producto": "Sin Descuento", "precio_regular": 650.00, "precio_promo": 650.00},
            {"producto": "Sin Promo Reportada", "precio_regular": 700.00, "precio_promo": np.nan},
        ]
    )
    df = calcular_metricas(df)

    # Con descuento: ahorro = 285.00, % = 32.2%
    assert df.loc[0, "ahorro_verificable"] == 285.00
    assert df.loc[0, "porcentaje_ahorro"] == 32.2

    # Sin descuento: ahorro = 0.0, % = 0.0%
    assert df.loc[1, "ahorro_verificable"] == 0.00
    assert df.loc[1, "porcentaje_ahorro"] == 0.0

    # Sin promo: precio_efectivo = precio_regular, ahorro = 0
    assert df.loc[2, "precio_efectivo"] == 700.00
    assert df.loc[2, "ahorro_verificable"] == 0.00


# 3. Prueba de costo efectivo en promociones multiunidad (3x2, compras N)
def test_promociones_multiunidad():
    # Caso 3x2: compras 3 botellas por $600 (precio regular individual $300)
    df_3x2 = crear_df_base([{"unidades_promo": 3, "precio_total_promo": 600.00, "precio_regular": 300.00, "ml": 750}])
    df_3x2 = calcular_metricas(df_3x2)
    # Costo efectivo unitario debe ser $200.00
    assert df_3x2.loc[0, "precio_efectivo"] == 200.00
    assert df_3x2.loc[0, "ahorro_verificable"] == 100.00  # $300 - $200
    assert df_3x2.loc[0, "precio_por_litro"] == round(200.00 / 0.75, 2)

    # Caso pack 2 unidades por $500
    df_pack2 = crear_df_base(
        [{"unidades_promo": 2, "precio_total_promo": 500.00, "precio_regular": 300.00, "ml": 1000}]
    )
    df_pack2 = calcular_metricas(df_pack2)
    assert df_pack2.loc[0, "precio_efectivo"] == 250.00
    assert df_pack2.loc[0, "precio_por_litro"] == 250.00


# 4. Prueba de detección de duplicados
def test_deteccion_duplicados():
    df = crear_df_base(
        [
            {"tienda": "Alianza", "producto": "1800 Cristalino", "ml": 700, "url": "https://alianza.com/1800"},
            {"tienda": "Alianza", "producto": "1800 Cristalino", "ml": 700, "url": "https://alianza.com/1800-dupe"},
            {"tienda": "Alianza", "producto": "1800 Cristalino", "ml": 1000, "url": "https://alianza.com/1800-1L"},
        ]
    )
    df = detectar_duplicados(df)

    assert not df.loc[0, "es_duplicado"]
    assert df.loc[1, "es_duplicado"]  # Mismo producto, misma tienda, mismo ml
    assert not df.loc[2, "es_duplicado"]  # Diferente volumen (1L vs 700ml)


# 5. Prueba de auditoría de datos faltantes
def test_auditoria_datos_faltantes():
    df = crear_df_base(
        [
            {"producto": "Completo", "precio_regular": 500.0, "ml": 750, "url": "https://ok.com"},
            {"producto": "Sin ML", "precio_regular": 500.0, "ml": np.nan, "url": "https://ok.com"},
            {"producto": "Sin URL", "precio_regular": 500.0, "ml": 750, "url": np.nan},
            {"producto": "Sin Precio Regular", "precio_regular": np.nan, "ml": 750, "url": "https://ok.com"},
        ]
    )
    df = auditar_datos_faltantes(df)

    assert not df.loc[0, "tiene_datos_faltantes"]
    assert df.loc[1, "tiene_datos_faltantes"]
    assert "ml" in df.loc[1, "campos_faltantes"]

    assert df.loc[2, "tiene_datos_faltantes"]
    assert "url" in df.loc[2, "campos_faltantes"]

    assert df.loc[3, "tiene_datos_faltantes"]
    assert "precio_regular" in df.loc[3, "campos_faltantes"]


# 6. Prueba de distinción estricta en Tequila (Añejo vs Cristalino vs Reposado)
def test_distincion_categorias_tequila():
    df = crear_df_base(
        [
            {
                "producto": "1800 Añejo",
                "categoria": "Tequila",
                "subcategoria": "Añejo Tradicional",
                "precio_promo": 599.25,
                "ml": 700,
            },
            {
                "producto": "1800 Cristalino",
                "categoria": "Tequila",
                "subcategoria": "Añejo Cristalino",
                "precio_promo": 600.00,
                "ml": 700,
            },
            {
                "producto": "Herradura Ultra Cristalino",
                "categoria": "Tequila",
                "subcategoria": "Añejo Cristalino",
                "precio_promo": 623.00,
                "ml": 700,
            },
            {
                "producto": "Cuervo Tradicional Rep.",
                "categoria": "Tequila",
                "subcategoria": "Reposado",
                "precio_promo": 472.00,
                "ml": 750,
            },
        ]
    )
    df = detectar_duplicados(df)
    df = calcular_metricas(df)
    rankings = generar_rankings_por_categoria(df)

    # Cada subcategoría debe ser un grupo independiente
    assert "Tequila - Añejo Tradicional" in rankings
    assert "Tequila - Añejo Cristalino" in rankings
    assert "Tequila - Reposado" in rankings

    df_anejo = rankings["Tequila - Añejo Tradicional"]
    df_cristalino = rankings["Tequila - Añejo Cristalino"]
    df_reposado = rankings["Tequila - Reposado"]

    # Verificar que no se mezclan productos entre categorías
    assert all(df_anejo["subcategoria"] == "Añejo Tradicional")
    assert all(df_cristalino["subcategoria"] == "Añejo Cristalino")
    assert all(df_reposado["subcategoria"] == "Reposado")

    # En cristalino deben estar los 2 cristalinos
    assert len(df_cristalino) == 2
    assert len(df_anejo) == 1
    assert len(df_reposado) == 1


# 7. Prueba de distinción estricta en Mezcal (Reposado vs Añejo vs Silvestres)
def test_distincion_categorias_mezcal_reposado_anejo_silvestres():
    df = crear_df_base(
        [
            {
                "producto": "Amarás Reposado",
                "categoria": "Mezcal",
                "subcategoria": "Reposado",
                "clase": "Reposado",
                "precio_promo": 503.30,
                "ml": 750,
            },
            {
                "producto": "400 Conejos Añejo",
                "categoria": "Mezcal",
                "subcategoria": "Añejo",
                "clase": "Añejo",
                "precio_promo": 667.50,
                "ml": 700,
            },
            {
                "producto": "Amarás Cupreata",
                "categoria": "Mezcal",
                "subcategoria": "Silvestre",
                "clase": "Joven",
                "especie_agave": "Cupreata silvestre",
                "precio_promo": 719.20,
                "ml": 750,
            },
            {
                "producto": "400 Conejos Tobalá",
                "categoria": "Mezcal",
                "subcategoria": "Silvestre",
                "clase": "Joven",
                "especie_agave": "Tobalá silvestre",
                "precio_promo": 652.66,
                "ml": 700,
            },
            {
                "producto": "400 Conejos Joven",
                "categoria": "Mezcal",
                "subcategoria": "Espadín Joven",
                "clase": "Joven",
                "especie_agave": "Espadín",
                "precio_promo": 408.75,
                "ml": 700,
            },
        ]
    )
    df = detectar_duplicados(df)
    df = calcular_metricas(df)
    rankings = generar_rankings_por_categoria(df)

    # Verificar que existan las 4 divisiones de mezcal
    assert "Mezcal - Reposado" in rankings
    assert "Mezcal - Añejo" in rankings
    assert "Mezcal - Silvestre" in rankings
    assert "Mezcal - Espadín Joven" in rankings

    df_rep = rankings["Mezcal - Reposado"]
    df_anejo = rankings["Mezcal - Añejo"]
    df_silvestre = rankings["Mezcal - Silvestre"]
    df_espadin = rankings["Mezcal - Espadín Joven"]

    assert len(df_rep) == 1 and df_rep.loc[0, "producto"] == "Amarás Reposado"
    assert len(df_anejo) == 1 and df_anejo.loc[0, "producto"] == "400 Conejos Añejo"
    assert len(df_silvestre) == 2  # Cupreata y Tobalá
    assert len(df_espadin) == 1 and df_espadin.loc[0, "producto"] == "400 Conejos Joven"

    # Verificar orden por precio por litro en silvestres
    assert df_silvestre.loc[0, "precio_por_litro"] <= df_silvestre.loc[1, "precio_por_litro"]


# 8. Prueba de clasificación estricta: Don Ramón Plata (Blanco) vs Reposado vs Cristalinos
def test_clasificacion_estricta_don_ramon_y_blancos():
    from src.actualizar_dashboard_completo import clasificar_estricto

    # Don Ramón Plata Punta Diamante NUNCA debe ser Añejo ni Cristalino, sino Blanco / Plata (0 meses)
    cat_d, sub_d, cla_d = clasificar_estricto(
        {"categoria": "Tequila", "producto": "Tequila Don Ramón Punta Diamante Plata 750 ml"}
    )
    assert cat_d == "Tequila - Blanco / Plata"
    assert sub_d == "Blanco"
    assert cla_d == "Blanco"

    # Don Ramón Reposado Punta Diamante tradicional debe ser Reposado Tradicional
    cat_rep, sub_rep, cla_rep = clasificar_estricto(
        {"categoria": "Tequila", "producto": "Tequila Don Ramón Reposado Punta Diamante 750 ml"}
    )
    assert cat_rep == "Tequila - Reposado Tradicional"
    assert sub_rep == "Reposado"

    # Gran Centenario Ultra debe ser Reposado Cristalino
    cat_gc, sub_gc, _ = clasificar_estricto(
        {"categoria": "Tequila", "producto": "Tequila Gran Centenario Ultra Reposado Cristalino 700 ml"}
    )
    assert cat_gc == "Tequila - Reposado Cristalino"

    # Don Ramón Añejo Cristalino Platinium sí es Añejo Cristalino
    cat_dr_ac, sub_dr_ac, _ = clasificar_estricto(
        {"categoria": "Tequila", "producto": "Tequila Don Ramón Platinium Cristalino Añejo 700 ml"}
    )
    assert cat_dr_ac == "Tequila - Añejo Cristalino"


def test_precios_ausentes_excluidos_de_rankings():
    """Valida que registros sin precio devuelvan NaN y no se cuelen en el ranking (H7)."""
    df = crear_df_base(
        [
            {
                "producto": "Botella Sin Precio",
                "precio_regular": np.nan,
                "precio_promo": np.nan,
                "precio_total_promo": np.nan,
            },
            {"producto": "Botella Válida", "precio_regular": 600.0, "precio_promo": 500.0},
        ]
    )
    metricas = calcular_metricas(df)
    assert np.isnan(metricas.loc[0, "precio_efectivo"])
    assert np.isnan(metricas.loc[0, "precio_por_litro"])

    rankings = generar_rankings_por_categoria(metricas)
    for _cat, sub_df in rankings.items():
        assert "Botella Sin Precio" not in sub_df["producto"].values


def test_h21_clave_comparativa_con_ml_float():
    """Valida que detectar_duplicados maneje ml float, int y string numérico sin corromper la clave (H21)."""
    df = crear_df_base(
        [
            {"tienda": "Tienda A", "producto": "Tequila Dobel Diamante", "ml": 700.0},
            {"tienda": "Tienda B", "producto": "Tequila Dobel Diamante", "ml": 700},
            {"tienda": "Tienda C", "producto": "Tequila Dobel Diamante", "ml": "700.0"},
            {"tienda": "Tienda D", "producto": "Tequila Dobel Diamante", "ml": np.nan},
        ]
    )
    df_dup = detectar_duplicados(df)

    # Las tres primeras deben normalizar exactamente a _700 y agruparse como comparables
    assert df_dup.loc[0, "clave_comparativa"].endswith("_700")
    assert df_dup.loc[1, "clave_comparativa"].endswith("_700")
    assert df_dup.loc[2, "clave_comparativa"].endswith("_700")
    assert df_dup.loc[0, "clave_comparativa"] == df_dup.loc[1, "clave_comparativa"]
    assert df_dup.loc[1, "clave_comparativa"] == df_dup.loc[2, "clave_comparativa"]

    # Fila con NaN cae a default 750
    assert df_dup.loc[3, "clave_comparativa"].endswith("_750")
