"""
Fixtures y utilidades compartidas para la suite de pruebas de Cantina Familiar.
Centraliza la creación de DataFrames de prueba y datos base para evitar duplicación.
"""

import pandas as pd
import pytest

BASE_REGISTRO_BEBIDA = {
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


def crear_df_base(filas: list[dict]) -> pd.DataFrame:
    """Crea un DataFrame de prueba rellenando columnas obligatorias por defecto."""
    registros = []
    for f in filas:
        item = BASE_REGISTRO_BEBIDA.copy()
        item.update(f)
        registros.append(item)
    return pd.DataFrame(registros)


# Alias para compatibilidad con suites que usen crear_df_prueba
crear_df_prueba = crear_df_base


@pytest.fixture
def fixture_crear_df():
    """Factory fixture para instanciar DataFrames con valores por defecto."""
    return crear_df_base


@pytest.fixture
def df_base_bebidas() -> pd.DataFrame:
    """Fixture que devuelve un DataFrame representativo con varias categorías y tiendas."""
    return crear_df_base(
        [
            {
                "tienda": "Bodegas Alianza",
                "producto": "Tequila Dobel Diamante 750 ml",
                "marca": "Maestro Dobel",
                "categoria": "Tequila",
                "subcategoria": "Añejo Cristalino",
                "clase": "Añejo Cristalino",
                "ml": 750,
                "precio_regular": 800.0,
                "precio_promo": 650.0,
            },
            {
                "tienda": "La Europea",
                "producto": "Tequila Dobel Diamante 750 ml",
                "marca": "Maestro Dobel",
                "categoria": "Tequila",
                "subcategoria": "Añejo Cristalino",
                "clase": "Añejo Cristalino",
                "ml": 750,
                "precio_regular": 820.0,
                "precio_promo": 690.0,
            },
            {
                "tienda": "Bodegas Alianza",
                "producto": "Mezcal Ojo de Tigre 750 ml",
                "marca": "Ojo de Tigre",
                "categoria": "Mezcal",
                "subcategoria": "Espadín / Tobalá",
                "clase": "Joven",
                "tipo_mezcal": "Artesanal",
                "ml": 750,
                "precio_regular": 600.0,
                "precio_promo": 520.0,
            },
            {
                "tienda": "Walmart",
                "producto": "Whisky Johnnie Walker Black Label 750 ml",
                "marca": "Johnnie Walker",
                "categoria": "Whisky",
                "subcategoria": "Blended Scotch",
                "clase": "12 Años",
                "ml": 750,
                "precio_regular": 900.0,
                "precio_promo": 780.0,
            },
        ]
    )
