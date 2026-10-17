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
    es_producto_paquete,
    generar_rankings_por_categoria,
    marcar_outliers_lujo,
    normalizar_texto_clave,
    obtener_comparativa_cross_tienda,
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
    assert cla_rep == "Reposado"

    # Gran Centenario Ultra debe ser Reposado Cristalino
    cat_gc, sub_gc, _ = clasificar_estricto(
        {"categoria": "Tequila", "producto": "Tequila Gran Centenario Ultra Reposado Cristalino 700 ml"}
    )
    assert cat_gc == "Tequila - Reposado Cristalino"
    assert sub_gc == "Reposado Cristalino"

    # Don Ramón Añejo Cristalino Platinium sí es Añejo Cristalino
    cat_dr_ac, sub_dr_ac, _ = clasificar_estricto(
        {"categoria": "Tequila", "producto": "Tequila Don Ramón Platinium Cristalino Añejo 700 ml"}
    )
    assert cat_dr_ac == "Tequila - Añejo Cristalino"
    assert sub_dr_ac == "Añejo Cristalino"


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
    """Valida que detectar_duplicados maneje ml float, int y string numérico sin corromper la clave (H21/H35)."""
    df = crear_df_base(
        [
            {"tienda": "Tienda A", "producto": "Tequila Dobel Diamante", "ml": 700.0},
            {"tienda": "Tienda B", "producto": "Tequila Dobel Diamante", "ml": 700},
            {"tienda": "Tienda C", "producto": "Tequila Dobel Diamante", "ml": "700.0"},
            {"tienda": "Tienda D", "producto": "Tequila Dobel Diamante", "ml": np.nan},
            {"tienda": "Tienda E", "producto": "Whisky Red Label 1 L", "ml": 1000.0},
            {"tienda": "Tienda F", "producto": "Whisky Red Label 1 L", "ml": "1000.0"},
        ]
    )
    df_dup = detectar_duplicados(df)

    # Las cuatro primeras corresponden al formato estándar y deben unificarse con _std (H35)
    assert df_dup.loc[0, "clave_comparativa"].endswith("_std")
    assert df_dup.loc[1, "clave_comparativa"].endswith("_std")
    assert df_dup.loc[2, "clave_comparativa"].endswith("_std")
    assert df_dup.loc[3, "clave_comparativa"].endswith("_std")
    assert (
        df_dup.loc[0, "clave_comparativa"]
        == df_dup.loc[1, "clave_comparativa"]
        == df_dup.loc[2, "clave_comparativa"]
        == df_dup.loc[3, "clave_comparativa"]
    )

    # Formatos no estándar (1000 ml) conservan su valor numérico entero exacto sin decimales corruptos (H21)
    assert df_dup.loc[4, "clave_comparativa"].endswith("_1000")
    assert df_dup.loc[5, "clave_comparativa"].endswith("_1000")
    assert df_dup.loc[4, "clave_comparativa"] == df_dup.loc[5, "clave_comparativa"]


def test_h35_comparativa_cross_tienda_700_vs_750ml():
    """
    Valida la unificación de botellas estándar (700ml vs 750ml) y el arbitraje por precio por litro (H35):
    - 700ml y 750ml se unifican bajo la misma clave_comparativa.
    - Formatos no estándar (1.75 L) permanecen independientes.
    - La tienda más barata se determina por $/L cuando los volúmenes difieren.
    """
    df = crear_df_base(
        [
            # Tienda A: Herradura Ultra 700 ml @ $647.56 ($925.09 / L)
            {
                "tienda": "Sam's Club",
                "producto": "Tequila Herradura Ultra Añejo 700 ml",
                "categoria": "Tequila",
                "ml": 700,
                "precio_promo": 647.56,
            },
            # Tienda B: Herradura Ultra 750 ml @ $958.00 ($1277.33 / L)
            {
                "tienda": "Walmart",
                "producto": "Tequila Herradura Ultra Añejo 750 ml",
                "categoria": "Tequila",
                "ml": 750,
                "precio_promo": 958.00,
            },
            # Tienda C: Herradura Ultra 1.75 L (formato no estándar, no debe mezclarse)
            {
                "tienda": "Bodegas Alianza",
                "producto": "Tequila Herradura Ultra Añejo 1.75 L",
                "categoria": "Tequila",
                "ml": 1750,
                "precio_promo": 1600.00,
            },
        ]
    )
    df_calc = calcular_metricas(df)
    df_dup = detectar_duplicados(df_calc)

    # 700 ml y 750 ml unificados en la misma clave comparativa
    clave_700 = df_dup.loc[0, "clave_comparativa"]
    clave_750 = df_dup.loc[1, "clave_comparativa"]
    clave_1750 = df_dup.loc[2, "clave_comparativa"]

    assert clave_700.endswith("_std")
    assert clave_750.endswith("_std")
    assert clave_700 == clave_750
    assert bool(df_dup.loc[0, "es_comparable_cross_tienda"]) is True
    assert bool(df_dup.loc[1, "es_comparable_cross_tienda"]) is True

    # 1.75 L no debe unirse al grupo estándar
    assert clave_1750.endswith("_1750")
    assert clave_1750 != clave_700
    assert bool(df_dup.loc[2, "es_comparable_cross_tienda"]) is False

    # Comparativa cross-tienda con ranking por $/L
    df_comp = obtener_comparativa_cross_tienda(df_dup)
    assert not df_comp.empty
    assert len(df_comp) == 1
    res = df_comp.iloc[0]

    assert res["tienda_mas_barata"] == "Sam's Club"
    assert res["precio_minimo"] == 647.56
    assert res["tienda_mas_cara"] == "Walmart"
    assert res["precio_maximo"] == 958.00
    # Ahorro normalizado: ($1277.33 - $925.09) * 0.70 L = $246.57 aprox
    assert res["ahorro_maximo"] > 240.0
    assert res["porcentaje_ahorro_maximo"] > 25.0


def test_h35_normalizar_texto_clave_distingue_volumen_no_estandar():
    """
    Valida el blindaje de normalizar_texto_clave (H35):
    - 700 ml y 750 ml unifican su clave al ser botellas estándar equivalentes.
    - 1.75 L, 1 L y formatos no estándar (<650 ml o >800 ml) conservan su tamaño canónico
      evitando cualquier riesgo latente de comparaciones engañosas.
    """
    clave_700 = normalizar_texto_clave("Tequila Herradura Ultra Añejo 700 ml")
    clave_750 = normalizar_texto_clave("Tequila Herradura Ultra Añejo 750 ml")
    clave_1750 = normalizar_texto_clave("Tequila Herradura Ultra Añejo 1.75 L")
    clave_1000 = normalizar_texto_clave("Tequila Herradura Ultra Añejo 1 L")
    clave_200 = normalizar_texto_clave("Tequila Herradura Ultra Añejo 200 ml")

    # Estándar unificado
    assert clave_700 == clave_750
    assert clave_700 == "anejo herradura tequila ultra"

    # No estándar preservan volumen canónico y no colisionan
    assert clave_1750 == "1750ml anejo herradura tequila ultra"
    assert clave_1000 == "1000ml anejo herradura tequila ultra"
    assert clave_200 == "200ml anejo herradura tequila ultra"

    assert clave_1750 != clave_750
    assert clave_1000 != clave_750
    assert clave_200 != clave_750


def test_unificacion_honey_cross_tienda():
    """
    Valida la unificación de claves cross-tienda para Licor de Whisky - Honey:
    - Passport Honey (Chedraui vs Walmart).
    - Jack Daniel's Honey 700 ml (Alianza, Soriana, Chedraui, Walmart).
    - Jack Daniel's 1 L (Sam's Club) permanece independiente.
    - Posesivos ingleses con apóstrofes (Buchanan's, Ballantine's, William Lawson's).
    """
    # 1. Passport Honey
    clave_chedraui_p = normalizar_texto_clave("Whisky Passport Honey 700 ml")
    clave_walmart_p = normalizar_texto_clave("Licor de Whisky Passport Honey 700 ml")
    assert clave_chedraui_p == clave_walmart_p == "honey passport whisky"

    # 2. Jack Daniel's Honey 700 ml
    clave_alianza_jd = normalizar_texto_clave("Whiskey Jack Daniel’s Honey Tennessee 700 ml")
    clave_soriana_jd = normalizar_texto_clave("Whisky Jack Daniels Tennessee Honey 700 ml")
    clave_chedraui_jd = normalizar_texto_clave("Whisky Jack Daniel's Tennessee Honey 700 ml")
    clave_walmart_jd = normalizar_texto_clave("Whiskey Jack Daniel's Honey 700 ml")

    assert clave_alianza_jd == clave_soriana_jd == clave_chedraui_jd == clave_walmart_jd == "daniels honey jack whisky"

    # 3. Jack Daniel's 1 L (Sam's Club) no se mezcla
    clave_sams_1l = normalizar_texto_clave("Whiskey Jack Daniel's Tennessee Honey 1 L")
    assert clave_sams_1l == "1000ml daniels honey jack whisky"
    assert clave_sams_1l != clave_alianza_jd

    # 4. Posesivos ingleses con apóstrofes (Buchanan's, Ballantine's, William Lawson's)
    assert normalizar_texto_clave("Whisky Buchanan’s 12 Años 750 ml") == normalizar_texto_clave(
        "Whisky Buchanan's 12 Años 750 ml"
    )
    assert normalizar_texto_clave("Whisky Ballantine’s Finest 700 ml") == normalizar_texto_clave(
        "Whisky Ballantine's Finest 700 ml"
    )
    assert normalizar_texto_clave("Whisky William Lawson’s 700 ml") == normalizar_texto_clave(
        "Whisky William Lawson's 700 ml"
    )


def test_h25_marcar_outliers_lujo():
    """Valida la detección y marcaje de botellas de ultra-lujo y colección (H25)."""
    df = crear_df_base(
        [
            # Botella habitual accesible
            {
                "producto": "Tequila 1800 Cristalino 700 ml",
                "categoria": "Tequila",
                "precio_promo": 750.0,
                "ml": 700,
            },
            # Botella magnum bulk (económica por litro, no es outlier)
            {
                "producto": "Tequila Dobel Diamante 3 L",
                "categoria": "Tequila",
                "precio_promo": 3200.0,
                "ml": 3000,
            },
            # Botella ultra-lujo (> 3500 $/L)
            {
                "producto": "Tequila Don Julio 1942 750 ml",
                "categoria": "Tequila",
                "precio_promo": 3500.0,
                "ml": 750,
            },
            # Botella de colección extrema
            {
                "producto": "Whisky Royal Salute 51 Años 700 ml",
                "categoria": "Whisky",
                "precio_promo": 690000.0,
                "ml": 700,
            },
        ]
    )
    df = calcular_metricas(df)
    df = marcar_outliers_lujo(df)

    assert not df.loc[0, "es_outlier_lujo"]  # 1800 Cristalino accesible
    assert not df.loc[1, "es_outlier_lujo"]  # Dobel 3L no es outlier
    assert df.loc[2, "es_outlier_lujo"]  # Don Julio 1942
    assert df.loc[3, "es_outlier_lujo"]  # Royal Salute 51 años

    # Validar que generar_rankings_por_categoria los excluya por defecto
    rankings = generar_rankings_por_categoria(df, excluir_outliers=True)
    for _cat, sub in rankings.items():
        assert "Whisky Royal Salute 51 Años 700 ml" not in sub["producto"].values


def test_es_producto_paquete():
    """Valida la detección precisa de botellas en paquete, combos promocionales o con obsequios."""
    paquetes = [
        (
            "Mezcal 400 Conejos Joven 100% Cosecha Salvaje 700 ml + 2 Vasos + Sal",
            "🎁 Edición con obsequio (2 Vasos + Sal)",
        ),
        ("Pack Whisky Jack Daniels Honey 700 ml + 2 Jack Daniels 200 ml", "Precio regular"),
        ("Tequila Patrón Cristalino Añejo 700 ml Pack de 2", "Rebaja en línea"),
        ("Whisky Johnnie Walker Black 750 ml + Termo", "🎁 Edición con obsequio (Termo)"),
        ("Mezcal Mitre Artesanal Joven 750 ml kit mezcalero", "Precio regular"),
        ("Mezcal Aluchín Joven 100% 750 ml C/4 Caballitos", "Precio regular"),
        ("Whisky Chivas Regal 12 Años 750 ml + Absolut Vodka 200 ml", "Oferta en línea"),
        ("Vino Tinto Cuatro Soles 2 pzas de 750 ml c/u", "Precio socio"),
    ]
    for nom, cond in paquetes:
        assert es_producto_paquete(nom, cond) is True, f"Debería detectarse como paquete/combo: {nom}"

    individuales = [
        ("Whisky Passport Honey 700 ml", "Precio regular"),
        ("Tequila Maestro Dobel Diamante 700 ml", "Descuento directo"),
        ("Mezcal 400 Conejos Joven 100% Cosecha Salvaje 700 ml", "Precio regular"),
        ("Vino Tinto Concha y Toro Reservado Cabernet Sauvignon 750 ml", "Precio regular"),
    ]
    for nom, cond in individuales:
        assert es_producto_paquete(nom, cond) is False, f"NO debería detectarse como paquete: {nom}"


def test_calcular_metricas_columna_es_paquete():
    """Valida que calcular_metricas asigne la columna booleana es_paquete."""
    df = crear_df_base(
        [
            {
                "producto": "Mezcal 400 Conejos 700 ml + 2 Vasos + Sal",
                "condiciones": "🎁 Edición con obsequio",
                "precio_promo": 849.0,
            },
            {"producto": "Mezcal 400 Conejos 700 ml", "condiciones": "Precio regular", "precio_promo": 849.0},
        ]
    )
    df = calcular_metricas(df)
    assert "es_paquete" in df.columns
    assert bool(df.loc[0, "es_paquete"]) is True
    assert bool(df.loc[1, "es_paquete"]) is False
