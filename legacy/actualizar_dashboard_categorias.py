"""
Actualiza data/dashboard_data.json y genera dashboard_bi.html con separación estricta
de categorías comparables (Regla 6) para Tequilas (Añejo Cristalino vs Reposado Cristalino vs Añejo Tradicional)
y Mezcales (Reposado vs Añejo vs Silvestres).
"""

import os
import json
import pandas as pd

df = pd.read_csv('data/ranking_completo_general.csv')

def asignar_categoria_comparable(row):
    cat = row['categoria']
    sub = str(row['subcategoria'])
    nom = str(row['producto']).lower()

    if cat == 'Tequila':
        # Distinción precisa
        if 'añejo cristalino' in sub.lower() or ('cristalino' in nom and ('añejo' in nom or 'anejo' in nom or 'ultra' in nom)):
            return 'Tequila - Añejo Cristalino'
        elif 'reposado cristalino' in sub.lower() or ('cristalino' in nom and ('rep' in nom or 'punta diamante' in nom or 'hacienda de tepa' in nom or 'centenario ultra' in nom)):
            return 'Tequila - Reposado Cristalino'
        elif 'cristalino' in nom or 'cristalino' in sub.lower() or 'diamante' in nom:
            # Si no especifica pero es cristalino de gama alta (Dobel Diamante es ensamble con base añeja)
            return 'Tequila - Añejo Cristalino'
        elif 'añejo' in sub or 'añejo' in nom or 'anejo' in nom:
            return 'Tequila - Añejo Tradicional'
        else:
            return 'Tequila - Otros'
    elif cat == 'Mezcal':
        if 'silvestre' in sub.lower() or any(k in nom for k in ['tobalá', 'tobala', 'cupreata', 'cuishe', 'tepeztate', 'arroqueño', 'jabalí', 'ensamble']):
            return 'Mezcal - Silvestre'
        elif 'añejo' in sub.lower() or 'añejo' in nom or 'anejo' in nom:
            return 'Mezcal - Añejo'
        elif 'reposado cristalino' in sub.lower() or 'cristalino' in nom:
            return 'Mezcal - Reposado Cristalino'
        elif 'reposado' in sub.lower() or 'rep' in nom:
            return 'Mezcal - Reposado'
        else:
            return 'Mezcal - Espadín Joven'
    elif cat == 'Whisky':
        return 'Whisky - Blended Scotch'
    elif cat == 'Licor de Whisky':
        return 'Licor de Whisky - Honey'
    elif cat == 'Vino':
        return 'Vino - Tinto Clericot'
    return cat

df['categoria_comparable'] = df.apply(asignar_categoria_comparable, axis=1)

# Filtrar para catálogo relevante
cond = (
    ((df['categoria'] == 'Tequila') & (df['precio_promo'] <= 1100)) |
    (df['categoria'] == 'Mezcal') |
    ((df['categoria'] == 'Whisky') & (df['precio_promo'] <= 1000)) |
    (df['categoria'] == 'Licor de Whisky') |
    ((df['categoria'] == 'Vino') & (df['precio_promo'] <= 250))
)
df_dash = df[cond].copy()
df_dash = df_dash.sort_values(by=['categoria_comparable', 'precio_por_litro'])

cols = ['tienda', 'producto', 'marca', 'categoria', 'subcategoria', 'clase', 'categoria_comparable', 'ml', 'precio_promo', 'precio_regular', 'precio_por_litro', 'ahorro_verificable', 'porcentaje_ahorro', 'disponibilidad', 'url', 'especie_agave']

records = df_dash[cols].fillna('').to_dict(orient='records')

with open('data/dashboard_data.json', 'w', encoding='utf-8') as f:
    json.dump(records, f, ensure_ascii=False)

print(f"Total registros guardados: {len(records)}")
print("\nDistribución por Categoría Comparable:")
print(df_dash['categoria_comparable'].value_counts())
