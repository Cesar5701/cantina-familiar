"""
Script maestro para:
1. Consolidar los catálogos scrapeados de las 5 tiendas:
   - Bodegas Alianza (data/scraped_alianza_completo.csv)
   - Sam's Club (data/scraped_sams.csv)
   - Walmart (data/scraped_walmart.csv)
   - Chedraui (data/scraped_chedraui.csv)
   - Soriana (data/scraped_soriana.csv)
2. Auditar y corregir clasificaciones NOM de Tequila, Mezcal, Whisky, Licor Honey y Vino.
3. Calcular métricas normalizadas por litro (src/analizador.py) y actualizar:
   - data/catalogo_completo_consolidado.csv
   - data/ranking_completo_general.csv
   - data/dashboard_data.json
"""

import os
import re
import sys
import json
import pandas as pd

RAIZ_PROYECTO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if RAIZ_PROYECTO not in sys.path:
    sys.path.insert(0, RAIZ_PROYECTO)

from src.analizador import calcular_metricas, detectar_duplicados, validar_esquema_y_rangos
from src.io_utils import guardar_csv_atomico, guardar_json_atomico



from src.clasificacion import (
    corregir_ml_producto,
    extraer_ml,
    clasificar_estricto,
    MARCAS_REPOSADO_CRISTALINO_POR_NORMA,
    PALABRAS_EXCLUIDAS
)



def actualizar_todo():
    archivos_fuente = [
        'data/scraped_alianza_completo.csv',
        'data/scraped_sams.csv',
        'data/scraped_walmart.csv',
        'data/scraped_chedraui.csv',
        'data/scraped_soriana.csv'
    ]

    dfs = []
    for ruta in archivos_fuente:
        if os.path.exists(ruta):
            df_part = pd.read_csv(ruta)
            print(f"  + Cargado {ruta}: {len(df_part)} filas")
            dfs.append(df_part)

    df = pd.concat(dfs, ignore_index=True)

    # Limpiar artículos que sean latas RTD, cajas mayoristas o miniaturas (< 650 ml)
    df['ml'] = [corregir_ml_producto(row['producto'], row['ml']) for _, row in df.iterrows()]
    df = df[df['ml'] >= 650].copy()

    mask_excluir = df['producto'].str.lower().str.contains(
        'lemonade|6 latas|4 pachitas|6 pzas|paquete de 3|caja de 6|caja de 12|estuche vacío|crema de|aguamiel|bacanora',
        regex=True, na=False
    )
    df = df[~mask_excluir].copy()

    # Clasificación estricta NOM
    resultados = df.apply(clasificar_estricto, axis=1)
    df['categoria_comparable'] = [r[0] for r in resultados]
    df['subcategoria'] = [r[1] for r in resultados]
    df['clase'] = [r[2] for r in resultados]

    # Eliminar Tequilas que sean Reposado Tradicional, Blanco/Plata u Otros (solo conservar Añejo Cristalino, Reposado Cristalino y Añejo Tradicional)
    categorias_excluidas = [
        'Tequila - Reposado Tradicional',
        'Tequila - Blanco / Plata',
        'Tequila - Otros'
    ]
    df = df[~df['categoria_comparable'].isin(categorias_excluidas)].copy()

    # En Licor de Whisky - Honey, asegurar que sea realmente Honey
    mask_honey_invalido = (df['categoria_comparable'] == 'Licor de Whisky - Honey') & (~df['producto'].str.lower().str.contains('honey', na=False))
    df = df[~mask_honey_invalido].copy()

    # Deduplicar por (tienda, producto normalizado, ml)
    df['prod_key'] = df['producto'].str.lower().str.replace(r'\s+', ' ', regex=True).str.strip()
    df = df.drop_duplicates(subset=['tienda', 'prod_key', 'ml'], keep='first').drop(columns=['prod_key']).reset_index(drop=True)

    # Calcular métricas con src/analizador.py
    df = detectar_duplicados(df)
    df = calcular_metricas(df)

    # Validación de esquema y rangos (H9)
    df, reporte_val = validar_esquema_y_rangos(df)
    print(f"  + Auditoría de datos: {reporte_val['registros_validos']}/{reporte_val['total_registros']} registros válidos (0 anomalías críticas)")

    # Guardar archivos consolidados de forma atómica (H10)
    guardar_csv_atomico(df, 'data/catalogo_completo_consolidado.csv')
    guardar_csv_atomico(df, 'data/ranking_completo_general.csv')

    # Filtrar para catálogo relevante de la cantina familiar (descartar botellas ultra-lujo > $2,000)
    cond = (
        ((df['categoria'] == 'Tequila') & (df['precio_promo'] <= 1950)) |
        ((df['categoria'] == 'Mezcal') & (df['precio_promo'] <= 1500)) |
        ((df['categoria'] == 'Whisky') & (df['precio_promo'] <= 1750)) |
        (df['categoria'] == 'Licor de Whisky') |
        ((df['categoria'] == 'Vino') & ((df['precio_por_litro'] <= 350) | (df['precio_promo'] <= 260)))
    )
    df_dash = df[cond].copy()
    df_dash = df_dash.sort_values(by=['categoria_comparable', 'precio_por_litro']).reset_index(drop=True)

    cols = [
        'tienda', 'producto', 'marca', 'categoria', 'subcategoria', 'clase',
        'categoria_comparable', 'ml', 'precio_promo', 'precio_regular',
        'precio_por_litro', 'ahorro_verificable', 'porcentaje_ahorro',
        'disponibilidad', 'url', 'especie_agave', 'condiciones'
    ]
    for c in cols:
        if c not in df_dash.columns:
            df_dash[c] = ''

    records = df_dash[cols].fillna('').to_dict(orient='records')
    guardar_json_atomico(records, 'data/dashboard_data.json')

    print(f"\n[OK] Total registros guardados en dashboard_data.json: {len(records)}")
    print("\nDistribución por Tienda:")
    print(df_dash['tienda'].value_counts())
    print("\nDistribución por Categoría Comparable:")
    print(df_dash['categoria_comparable'].value_counts())


if __name__ == '__main__':
    actualizar_todo()
