"""
Pruebas exhaustivas para el módulo unificado de clasificación (src/clasificacion.py).
Cubre:
- H1: Clasificación estricta NOM-006 (Tequila), NOM-070 (Mezcal), Whisky, Honey y Vino.
- H2: Extracción y corrección de volumen (ml) con casos límite (litros, mililitros, multipacks, decimales).
- Limpieza y parseo de precios con distintos formatos y valores nulos/cero.
- Clasificación botánica de agaves para mezcal.
"""

import pandas as pd
import pytest

from src.clasificacion import (
    clasificar_agave_mezcal,
    clasificar_categoria,
    clasificar_estricto,
    corregir_ml_producto,
    es_mercancia_o_no_bebible,
    extraer_ml,
    generar_etiqueta_condicion,
    limpiar_precio,
    normalizar_medidas_en_nombre,
)

# ---------------------------------------------------------------------------
# Pruebas de extracción de volumen (H2 y H6)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "nombre,esperado",
    [
        ("Tequila Don Julio 70 Añejo Cristalino 700 ml", 700),
        ("Tequila Maestro Dobel Diamante 750ml", 750),
        ("Tequila Cuervo Tradicional Reposado 946 ml", 946),
        ("Whisky Johnnie Walker Black Label 1 L", 1000),
        ("Whisky Johnnie Walker Red Label 1 Litro", 1000),
        ("Whisky Buchanan's Deluxe 12 Años 1.75 L", 1750),
        ("Whisky Buchanan's Deluxe 1.75L", 1750),
        ("Vino Carlo Rossi Tinto 4 L", 4000),
        ("Vino Carlo Rossi California Red 5 L", 5000),
        ("Vino Reservado Concha y Toro Lambrusco 1.5 L", 1500),
        ("Vino Tinto Miniatura 187.5 ml", 188),
        ("Licor de Whisky Jack Daniel's Honey 700 cc", 700),
        # Multipacks explícitos
        ("2 pzas de 750 ml Tequila Dobel Diamante", 1500),
        ("6 botellas de 700 ml Tequila Herradura Ultra", 4200),
        ("Pack 6 Tequila Cuervo 1800 Milenio 700ml", 4200),
        ("Pack de 2 Tequila Don Ramón Punta Diamante 750 ml", 1500),
        ("Pack x 3 Whisky Johnnie Walker Blue Label 750 ml", 2250),
        ("Whisky Buchanan's x 2 750 ml", 1500),
        ("Paquete 2 Tequila Don Julio 70 700 ml", 1400),
        ("Whisky Black & White 6 pack 750 ml", 4500),
        ("Tequila Centinela Supremo Añejo 750 ml (8 Bot)", 6000),
        ("Caja de 3 Tequila Herradura Selección Suprema 750 ml", 2250),
        # Miniaturas descartables
        ("4 pachitas de 200 ml Tequila Jimador", 200),
        ("Pack miniatura 50 ml Tequila José Cuervo", 50),
        # Fallback si no tiene volumen especificado
        ("Tequila Don Ramón Edición Especial", 750),
    ],
)
def test_extraer_ml_casos_limite(nombre, esperado):
    assert extraer_ml(nombre) == esperado
    assert corregir_ml_producto(nombre) == esperado


# ---------------------------------------------------------------------------
# Pruebas de limpieza y normalización de precios
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "entrada,esperado",
    [
        (540.0, 540.0),
        (750, 750.0),
        ("$1,250.50", 1250.50),
        ("$999.00", 999.00),
        ("  $ 450.75  ", 450.75),
        ("1,890.00", 1890.00),
        ("$0.00", None),
        (0, None),
        (-150.0, None),
        (None, None),
        ("", None),
        ("Consultar en tienda", None),
    ],
)
def test_limpiar_precio(entrada, esperado):
    assert limpiar_precio(entrada) == esperado


# ---------------------------------------------------------------------------
# Pruebas de especies de agave en Mezcal (NOM-070)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "nombre,esperado",
    [
        ("Mezcal 400 Conejos Tobalá 750 ml", "Tobalá silvestre (A. potatorum)"),
        (
            "Mezcal 400 Conejos Joven 100% Cosecha Salvaje 700 ml",
            "Ensamble Silvestre Tobalá-Mexicano (A. potatorum / A. rhodacantha)",
        ),
        (
            "Mezcal 400 Conejos Joven 100% Cosecha Salvaje 700 ml + 2 Vasos + Sal",
            "Ensamble Silvestre Tobalá-Mexicano (A. potatorum / A. rhodacantha)",
        ),
        (
            "Mezcal 400 Conejos Cosecha Salvaje Tobala 700 ml",
            "Ensamble Silvestre Tobalá-Mexicano (A. potatorum / A. rhodacantha)",
        ),
        ("Mezcal Amores Mexicano 750 ml", "Mexicano silvestre (A. rhodacantha)"),
        ("Mezcal Amarás Cupreata 750 ml", "Cupreata silvestre (A. cupreata)"),
        ("Mezcal Creyente Cuishe 750 ml", "Cuishe silvestre (A. karwinskii)"),
        ("Mezcal Alipús San Andrés Cuixe 750 ml", "Cuishe silvestre (A. karwinskii)"),
        ("Mezcal Danzantes Tepeztate 750 ml", "Tepeztate silvestre (A. marmorata)"),
        ("Mezcal Montelobos Arroqueño 750 ml", "Arroqueño silvestre (A. americana)"),
        ("Mezcal Señorío Cenizo 750 ml", "Cenizo silvestre (A. durangensis)"),
        ("Mezcal Mitre Salmiana 750 ml", "Salmiana silvestre"),
        ("Mezcal Ensamble Espadín Tobalá 750 ml", "Ensamble Espadín-Tobalá"),
        ("Mezcal 400 Conejos Joven Espadín 750 ml", "Espadín (A. angustifolia)"),
        ("Mezcal Artesanal Oaxaca 750 ml", "Agave mezcalero (NOM-070)"),
    ],
)
def test_clasificar_agave_mezcal(nombre, esperado):
    assert clasificar_agave_mezcal(nombre) == esperado


# ---------------------------------------------------------------------------
# Pruebas de clasificación estricta (H1: Tequila NOM-006, Mezcal NOM-070, etc.)
# ---------------------------------------------------------------------------


def test_clasificacion_estricta_tequila():
    # Don Julio 70 siempre es Añejo Cristalino
    cat, sub, cla = clasificar_estricto("Tequila Don Julio 70 Añejo Cristalino 700 ml", "Tequila")
    assert cat == "Tequila - Añejo Cristalino"
    assert sub == "Añejo Cristalino"
    assert cla == "Añejo Cristalino"

    # Maestro Dobel Diamante siempre es Añejo Cristalino
    cat, sub, cla = clasificar_estricto("Tequila Maestro Dobel Diamante 750 ml", "Tequila")
    assert cat == "Tequila - Añejo Cristalino"
    assert sub == "Añejo Cristalino"

    # Herradura Ultra es Añejo Cristalino
    cat, sub, _ = clasificar_estricto("Tequila Herradura Ultra Cristalino 700 ml", "Tequila")
    assert cat == "Tequila - Añejo Cristalino"

    # Gran Centenario Ultra por norma es Reposado Cristalino
    cat, sub, _ = clasificar_estricto("Tequila Gran Centenario Ultra 700 ml", "Tequila")
    assert cat == "Tequila - Reposado Cristalino"
    assert sub == "Reposado Cristalino"

    # Don Ramón Punta Diamante Plata es Blanco
    cat, sub, cla = clasificar_estricto("Tequila Don Ramón Punta Diamante Plata 750 ml", "Tequila")
    assert cat == "Tequila - Blanco / Plata"
    assert sub == "Blanco"

    # Don Ramón Punta Diamante Reposado es Reposado Tradicional
    cat, sub, cla = clasificar_estricto("Tequila Don Ramón Punta Diamante Reposado 750 ml", "Tequila")
    assert cat == "Tequila - Reposado Tradicional"
    assert sub == "Reposado"

    # Don Ramón Platinium Cristalino Añejo es Añejo Cristalino
    cat, sub, cla = clasificar_estricto("Tequila Don Ramón Platinium Cristalino Añejo 700 ml", "Tequila")
    assert cat == "Tequila - Añejo Cristalino"

    # 1800 Milenio Extra Añejo
    cat, sub, cla = clasificar_estricto("Tequila 1800 Milenio Extra Añejo 750 ml", "Tequila")
    assert cat == "Tequila - Añejo Tradicional"
    assert cla == "Extra Añejo"

    # José Cuervo Tradicional Reposado (Ámbar tradicional, NO Cristalino)
    cat, sub, cla = clasificar_estricto("Tequila José Cuervo Tradicional Reposado 1.75 L", "Tequila")
    assert cat == "Tequila - Reposado Tradicional"
    assert sub == "Reposado"
    assert cla == "Reposado"

    cat, sub, cla = clasificar_estricto("Tequila José Cuervo Tradicional Reposado 950 ml", "Tequila")
    assert cat == "Tequila - Reposado Tradicional"
    assert sub == "Reposado"

    # José Cuervo Tradicional Cristalino (Sí es Cristalino sobre base Reposado)
    cat, sub, cla = clasificar_estricto("Tequila José Cuervo Tradicional Cristalino 750 ml", "Tequila")
    assert cat == "Tequila - Reposado Cristalino"
    assert sub == "Reposado Cristalino"
    assert cla == "Reposado Cristalino"


def test_clasificacion_estricta_mezcal():
    # Silvestres
    cat, sub, cla = clasificar_estricto("Mezcal 400 Conejos Tobalá 750 ml", "Mezcal")
    assert cat == "Mezcal - Silvestre"
    assert sub == "Silvestre"

    # Cosecha Salvaje (100% Silvestre bajo NOM-070)
    cat, sub, cla = clasificar_estricto("Mezcal 400 Conejos Joven 100% Cosecha Salvaje 700 ml", "Mezcal")
    assert cat == "Mezcal - Silvestre"
    assert sub == "Silvestre"
    assert cla == "Joven Silvestre"

    # Cosecha Salvaje combo promocional con vasos y sal
    cat, sub, cla = clasificar_estricto(
        "Mezcal 400 Conejos Joven 100% Cosecha Salvaje 700 ml + 2 Vasos + Sal", "Mezcal"
    )
    assert cat == "Mezcal - Silvestre"
    assert sub == "Silvestre"
    assert cla == "Joven Silvestre"

    # Mexicano silvestre
    cat, sub, cla = clasificar_estricto("Mezcal Amores Mexicano 750 ml", "Mezcal")
    assert cat == "Mezcal - Silvestre"
    assert sub == "Silvestre"

    # Añejo tradicional
    cat, sub, cla = clasificar_estricto("Mezcal 400 Conejos Añejo 750 ml", "Mezcal")
    assert cat == "Mezcal - Añejo"
    assert sub == "Añejo"

    # Reposado Cristalino
    cat, sub, cla = clasificar_estricto("Mezcal Contraluz Cristalino Reposado 700 ml", "Mezcal")
    assert cat == "Mezcal - Reposado Cristalino"
    assert sub == "Reposado Cristalino"

    # Reposado tradicional
    cat, sub, cla = clasificar_estricto("Mezcal Amarás Reposado 750 ml", "Mezcal")
    assert cat == "Mezcal - Reposado"
    assert sub == "Reposado"

    # Espadín Joven
    cat, sub, cla = clasificar_estricto("Mezcal 400 Conejos Joven 750 ml", "Mezcal")
    assert cat == "Mezcal - Espadín Joven"
    assert sub == "Espadín Joven"
    assert cla == "Joven"

    cat, sub, cla = clasificar_estricto("Mezcal Amarás Joven Espadín 750 ml", "Mezcal")
    assert cat == "Mezcal - Espadín Joven"
    assert sub == "Espadín Joven"

    cat, sub, cla = clasificar_estricto("Mezcal Montelobos Espadín 750 ml", "Mezcal")
    assert cat == "Mezcal - Espadín Joven"
    assert sub == "Espadín Joven"


def test_clasificacion_estricta_otras_bebidas():
    # Whisky Blended Scotch
    cat, sub, cla = clasificar_estricto("Whisky Johnnie Walker Black Label 750 ml", "Whisky")
    assert cat == "Whisky - Blended Scotch"
    assert sub == "Blended Scotch"

    # Licor de Whisky Honey
    cat, sub, cla = clasificar_estricto("Licor Jack Daniel's Tennessee Honey 700 ml", "Licor de Whisky")
    assert cat == "Licor de Whisky - Honey"
    assert sub == "Honey Liqueur"

    # Caso clave: productos cuyo título empieza con "Whiskey" o "Whisky" pero son Honey
    cat, sub, cla = clasificar_estricto("Whiskey Jack Daniel’s Honey Tennessee 700 ml")
    assert cat == "Licor de Whisky - Honey"
    assert sub == "Honey Liqueur"

    cat, sub, cla = clasificar_estricto("Whisky Passport Honey 700ml")
    assert cat == "Licor de Whisky - Honey"
    assert sub == "Honey Liqueur"

    # Vino Tinto Clericot
    cat, sub, cla = clasificar_estricto("Vino Tinto Carlo Rossi California 4 L", "Vino")
    assert cat == "Vino - Tinto Clericot"
    assert sub == "Tinto Clericot"
    assert cla == "Tinto Clericot"


def test_clasificar_categoria_compatibilidad():
    cat, sub = clasificar_categoria("Tequila Maestro Dobel Diamante 750 ml")
    assert cat == "Tequila"
    assert sub == "Añejo Cristalino"

    cat, sub = clasificar_categoria("Mezcal 400 Conejos Tobalá 750 ml")
    assert cat == "Mezcal"
    assert sub == "Silvestre"

    cat, sub = clasificar_categoria("Jack Daniel's Honey 700 ml")
    assert cat == "Licor de Whisky"
    assert sub == "Honey Liqueur"

    cat, sub = clasificar_categoria("Whisky Buchanan's Deluxe 750 ml")
    assert cat == "Whisky"
    assert sub == "Blended Scotch"

    cat, sub = clasificar_categoria("Vino Tinto Carlo Rossi 4L")
    assert cat == "Vino"
    assert sub == "Tinto Clericot"


# ---------------------------------------------------------------------------
# Pruebas de normalización de medidas en nombres de producto (Fase 1)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "entrada,esperado",
    [
        ("Tequila X 700ml", "Tequila X 700 ml"),
        ("Tequila X 700 ml", "Tequila X 700 ml"),
        ("Mezcal Y 750ML", "Mezcal Y 750 ml"),
        ("Whisky Z 1.75L", "Whisky Z 1.75 L"),
        ("Whisky Z 1.75 lt", "Whisky Z 1.75 L"),
        ("Whisky Z 1.75 litros", "Whisky Z 1.75 L"),
        ("Vino W 1.5 l", "Vino W 1.5 L"),
        ("Garrafa 4L", "Garrafa 4 L"),
        ("Garrafa 5 litros", "Garrafa 5 L"),
        ("Tetra 946ml", "Tetra 946 ml"),
        ("Tetra 999 ml", "Tetra 999 ml"),
        ("Botella 1000ml", "Botella 1 L"),
        ("Pack 1500 ml", "Pack 1.5 L"),
        ("Medida 0.75L", "Medida 750 ml"),
        ("Medida 187.5 ml", "Medida 187.5 ml"),
        ("Mezcal J 750 ml C/Reposado 375ml", "Mezcal J 750 ml C/Reposado 375 ml"),
        ("Tequila 1800 Añejo", "Tequila 1800 Añejo"),
        ("Siete Leguas", "Siete Leguas"),
        ("Tequila 100% Agave", "Tequila 100% Agave"),
    ],
)
def test_normalizar_medidas_en_nombre(entrada, esperado):
    """Valida la matriz completa de normalización de medidas en nombres de producto (Fase 1)."""
    assert normalizar_medidas_en_nombre(entrada) == esperado


def test_normalizar_medidas_en_nombre_idempotencia():
    """Valida que aplicar la normalización dos veces arroje el mismo resultado (idempotente)."""
    muestras = [
        "Tequila X 700ml",
        "Whisky Z 1.75 lt",
        "Botella 1000ml",
        "Medida 0.75L",
        "Mezcal J 750 ml C/Reposado 375ml",
        "Tequila 1800 Añejo",
        "Pack 1500 ml",
        "Vino W 1.5 l",
    ]
    for m in muestras:
        una_vez = normalizar_medidas_en_nombre(m)
        dos_veces = normalizar_medidas_en_nombre(una_vez)
        assert dos_veces == una_vez


# ---------------------------------------------------------------------------
# Pruebas de discriminación de mercancía vs combos con obsequio
# ---------------------------------------------------------------------------


def test_es_mercancia_o_no_bebible():
    # Artículos que deben descartarse como mercancía / cristalería pura / comida
    descartados = [
        "Vaso Alianza Carat 280ml (2pz)",
        "Copa Cristalex Lara (6Pzs-450 ml)",
        "Copa Stolzle Burgundy 710 ml Set de 6 Piezas",
        "Vaso Tubo Baraima 6 pz",
        "Sal de gusano 50g",
        "Juego de 6 vasos tequileros",
        "Set de 4 copas de vino tinto",
        "Playera oficial Don Julio",
        "Hielera Corona acero inoxidable",
        "Chocolate Ferrero Rocher",
        "Papas Alianza C/Sal 195 g",
    ]
    for item in descartados:
        assert es_mercancia_o_no_bebible(item) is True, f"Debería descartarse como mercancía: {item}"

    # Combos legítimos con botella completa (ml >= 650) que NO deben descartarse
    admitidos = [
        "Mezcal 400 Conejos Joven 100% Cosecha Salvaje 700 ml + 2 Vasos + Sal",
        "Whisky Label 5 700 ml C/Vaso",
        "Whisky Johnnie Walker Black 750 ml C/Vaso Balón",
        "Whisky Buchanans 750 ml + Termo Tumbler Edición Limitada",
        "Mezcal Mitre Artesanal Joven 750ml kit mezcalero",
        "Vino Tinto Dulce Tres Coronas 750 ml",
        "Tequila Don Ramón Platinium Añejo Cristalino 700 ml con 2 copas",
    ]
    for item in admitidos:
        assert es_mercancia_o_no_bebible(item) is False, f"NO debería descartarse: {item}"


def test_generar_etiqueta_condicion():
    # Combo con 2 vasos y sal sin descuento de precio
    cond1 = generar_etiqueta_condicion(
        "Mezcal 400 Conejos Joven 100% Cosecha Salvaje 700 ml + 2 Vasos + Sal", 849.0, 849.0
    )
    assert cond1 == "🎁 Edición con obsequio (2 Vasos + Sal)"

    # Combo con vaso con descuento web
    cond2 = generar_etiqueta_condicion("Whisky Label 5 700 ml C/Vaso", 250.0, 200.0)
    assert cond2 == "Descuento Web + 🎁 Obsequio (Vaso)"

    # Botella normal sin obsequio ni descuento
    cond3 = generar_etiqueta_condicion("Mezcal 400 Conejos Joven 100% Cosecha Salvaje 700 ml", 849.0, 849.0)
    assert cond3 == "Precio regular catálogo"

    # Botella normal con descuento
    cond4 = generar_etiqueta_condicion("Mezcal 400 Conejos Joven 100% Cosecha Salvaje 700 ml", 900.0, 849.0)
    assert cond4 == "Descuento directo Aniversario Web"


def test_sincronizar_clasificacion_catalogo():
    from src.clasificacion import sincronizar_clasificacion_catalogo

    # Caso borde: vacío o None
    assert sincronizar_clasificacion_catalogo(None) is None
    df_vacio = pd.DataFrame()
    assert sincronizar_clasificacion_catalogo(df_vacio).empty

    # Catálogo sintético con casos mixtos
    data = [
        # 1. Mezcal silvestre con vaso de obsequio
        {
            "producto": "Mezcal Amarás Cupreata 750 ml con vaso",
            "categoria": "Mezcal",
            "precio_regular": 750.0,
            "precio_promo": 650.0,
        },
        # 2. Licor de Whisky Honey legítimo
        {
            "producto": "Jack Daniel's Tennessee Honey 700 ml",
            "categoria": "Whisky",
            "precio_regular": 550.0,
            "precio_promo": 480.0,
        },
        # 3. Tequila Blanco (debe ser excluido del alcance familiar)
        {
            "producto": "Tequila Don Ramón Plata 750 ml",
            "categoria": "Tequila",
            "precio_regular": 320.0,
            "precio_promo": 300.0,
        },
        # 4. Tequila Añejo Cristalino (debe mantenerse)
        {
            "producto": "Tequila 1800 Cristalino Añejo 700 ml",
            "categoria": "Tequila",
            "precio_regular": 850.0,
            "precio_promo": 720.0,
        },
        # 5. Whisky Blended Scotch
        {
            "producto": "Whisky Black & White 700 ml",
            "categoria": "Whisky",
            "precio_regular": 250.0,
            "precio_promo": 210.0,
        },
    ]
    df = pd.DataFrame(data)
    df_res = sincronizar_clasificacion_catalogo(df)

    # 1. El tequila blanco debe haberse descartado
    assert not any("Don Ramón Plata" in p for p in df_res["producto"])
    assert any("1800 Cristalino" in p for p in df_res["producto"])

    # 2. Mezcal debe tener especie_agave = Cupreata y etiqueta de obsequio
    row_mezcal = df_res[df_res["producto"].str.contains("Amarás")].iloc[0]
    assert row_mezcal["categoria"] == "Mezcal"
    assert row_mezcal["categoria_comparable"] == "Mezcal - Silvestre"
    assert "Cupreata" in row_mezcal["especie_agave"]
    assert "🎁" in str(row_mezcal["condiciones"])

    # 3. Jack Daniel's Honey debe quedar en categoria = 'Licor de Whisky'
    row_honey = df_res[df_res["producto"].str.contains("Jack Daniel")].iloc[0]
    assert row_honey["categoria"] == "Licor de Whisky"
    assert row_honey["categoria_comparable"] == "Licor de Whisky - Honey"

    # 4. Black & White debe ser Whisky Blended Scotch
    row_whisky = df_res[df_res["producto"].str.contains("Black & White")].iloc[0]
    assert row_whisky["categoria"] == "Whisky"
    assert row_whisky["categoria_comparable"] == "Whisky - Blended Scotch"
