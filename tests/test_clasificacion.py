"""
Pruebas exhaustivas para el módulo unificado de clasificación (src/clasificacion.py).
Cubre:
- H1: Clasificación estricta NOM-006 (Tequila), NOM-070 (Mezcal), Whisky, Honey y Vino.
- H2: Extracción y corrección de volumen (ml) con casos límite (litros, mililitros, multipacks, decimales).
- Limpieza y parseo de precios con distintos formatos y valores nulos/cero.
- Clasificación botánica de agaves para mezcal.
"""

import pytest

from src.clasificacion import (
    clasificar_agave_mezcal,
    clasificar_categoria,
    clasificar_estricto,
    corregir_ml_producto,
    extraer_ml,
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


def test_clasificacion_estricta_mezcal():
    # Silvestres
    cat, sub, cla = clasificar_estricto("Mezcal 400 Conejos Tobalá 750 ml", "Mezcal")
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
