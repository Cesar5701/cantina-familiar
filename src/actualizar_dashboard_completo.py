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

from src.analizador import calcular_metricas, detectar_duplicados


# Marcas cuyo "Cristalino" (cuando la tienda omite la palabra "Reposado") es normativamente un Reposado Cristalino
MARCAS_REPOSADO_CRISTALINO_POR_NORMA = [
    'centenario ultra', 'gran centenario ultra', 'cuervo tradicional', 'jose cuervo tradicional',
    'josé cuervo tradicional', 'jimador cristalino', 'el jimador cristalino', 'viuda de romero',
    'mayorazgo cristalino', 'hacienda de tepa cristalino', 'hornitos cristalino', 'ollitas cristalino',
    'antiguo cristalino', 'orendain cristalino', 'manoderecha cristalino', 'mano derecha',
    'contraluz', 'herradura cristal ', 'herradura cristalino', 'volcán de mi tierra', 'volcan de mi tierra',
    'tierra noble cristalino', 'el tequileño', 'casa loy'
]


def corregir_ml_producto(nombre: str, ml_actual: int) -> int:
    """Corrige el volumen en ml para paquetes dobles, decimales o formatos especiales."""
    nom_l = str(nombre).lower()

    # Multipacks explícitos de botellas completas: ej. "2 pzas de 750 ml"
    m_pack = re.search(r'(\d+)\s*(?:pzas|piezas|botellas)\s*(?:de\s*)?(\d+)\s*ml', nom_l)
    if m_pack:
        return int(m_pack.group(1)) * int(m_pack.group(2))

    # Multipacks de miniaturas (solo si NO incluye una botella principal de >=695ml)
    tiene_botella_grande = re.search(r'\b(?:695|700|750|946|1000)\s*ml\b|\b1(?:\.75|\.5)?\s*l\b', nom_l)
    if not tiene_botella_grande and re.search(r'\b(?:pachitas|miniatura|50\s*ml|187\.?5?\s*ml|200\s*ml|355\s*ml|473\s*ml)\b', nom_l):
        return 200

    # Detectar multiplicador "Pack de N", "Pack N", "Paquete N" o "N pack"
    mult_pack = 1
    m_pack_de = re.search(r'\b(?:pack|paquete)\s*(?:de\s*)?(\d+)\b', nom_l)
    if m_pack_de:
        mult_pack = int(m_pack_de.group(1))
    else:
        m_n_pack = re.search(r'\b(\d+)\s*(?:pack|botellas?)\b', nom_l)
        if m_n_pack:
            mult_pack = int(m_n_pack.group(1))

    # Formatos en litros (ej. 1.75 L, 4 L, 5 L, 1.5 L)
    m_l = re.search(r'(\d+(?:\.\d+)?)\s*(?:l|lt|lts|litro|litros)\b', nom_l)
    if m_l:
        val_l = float(m_l.group(1))
        if 0.35 <= val_l <= 6.0:
            return int(round(val_l * 1000)) * mult_pack

    # Formatos en mililitros con posible decimal (ej. 187.5 ml, 700 ml, 750 ml, 946 ml)
    m_ml = re.search(r'(\d+(?:\.\d+)?)\s*(?:ml|mls|mililitros|cc)\b', nom_l)
    if m_ml:
        return int(round(float(m_ml.group(1)))) * mult_pack

    base_ml = int(ml_actual) if ml_actual and ml_actual >= 350 else 750
    return base_ml * mult_pack


def clasificar_estricto(row):
    nom = str(row['producto']).strip()
    nom_l = nom.lower()
    cat = row['categoria']

    if cat == 'Tequila':
        # 1. BLANCO / PLATA (0 meses de barrica según NOM-006)
        if ('plata' in nom_l or 'blanco' in nom_l or 'silver' in nom_l) and not ('añejo' in nom_l or 'anejo' in nom_l or 'reposado' in nom_l):
            return 'Tequila - Blanco / Plata', 'Blanco', 'Blanco'
        if 'don ramón plata' in nom_l or 'don ramon plata' in nom_l:
            return 'Tequila - Blanco / Plata', 'Blanco', 'Blanco'

        # 2. CASO DON JULIO 70 (Siempre es Añejo Cristalino por norma NOM-006)
        if 'don julio 70' in nom_l:
            return 'Tequila - Añejo Cristalino', 'Añejo Cristalino', 'Añejo Cristalino'

        # 3. CASO DON RAMÓN: Punta Diamante tradicional vs Platinium Cristalino
        if 'don ramón' in nom_l or 'don ramon' in nom_l:
            if 'añejo cristalino' in nom_l or ('añejo' in nom_l and ('platinium' in nom_l or 'cristalino' in nom_l)):
                return 'Tequila - Añejo Cristalino', 'Añejo Cristalino', 'Añejo Cristalino'
            elif 'reposado cristalino' in nom_l or ('reposado' in nom_l and ('platinium' in nom_l or 'cristalino' in nom_l)):
                return 'Tequila - Reposado Cristalino', 'Reposado Cristalino', 'Reposado Cristalino'
            elif 'reposado' in nom_l:
                return 'Tequila - Reposado Tradicional', 'Reposado', 'Reposado'
            elif 'añejo' in nom_l or 'dark' in nom_l:
                return 'Tequila - Añejo Tradicional', 'Añejo Tradicional', 'Añejo'

        # 4. MARCAS QUE POR NORMA SON REPOSADO CRISTALINO (cuando el súper omite "Reposado")
        if any(m in nom_l for m in MARCAS_REPOSADO_CRISTALINO_POR_NORMA) and not ('añejo' in nom_l or 'anejo' in nom_l or 'ultra añejo' in nom_l):
            return 'Tequila - Reposado Cristalino', 'Reposado Cristalino', 'Reposado Cristalino'

        # 5. MAESTRO DOBEL DIAMANTE (Ensamble clarificado con carbón activado -> Añejo Cristalino)
        if 'dobel diamante' in nom_l or 'maestro dobel diamante' in nom_l:
            return 'Tequila - Añejo Cristalino', 'Añejo Cristalino', 'Añejo Cristalino'

        # 6. REGLAS GENERALES PARA OTROS TEQUILAS
        es_rep = 'reposado' in nom_l or 'rep.' in nom_l or 'rep ' in nom_l
        es_crist = 'cristalino' in nom_l or 'crist.' in nom_l or 'ultra' in nom_l or 'platinium' in nom_l or 'diamante' in nom_l or 'cristal' in nom_l
        es_anejo = 'añejo' in nom_l or 'anejo' in nom_l or 'extra añejo' in nom_l or 'milenio' in nom_l

        if es_rep and es_crist and not es_anejo:
            return 'Tequila - Reposado Cristalino', 'Reposado Cristalino', 'Reposado Cristalino'
        elif es_rep and not es_crist and not es_anejo:
            return 'Tequila - Reposado Tradicional', 'Reposado', 'Reposado'
        elif es_anejo and es_crist:
            return 'Tequila - Añejo Cristalino', 'Añejo Cristalino', 'Añejo Cristalino'
        elif es_anejo and not es_crist:
            if 'extra añejo' in nom_l or 'milenio' in nom_l:
                return 'Tequila - Añejo Tradicional', 'Extra Añejo', 'Extra Añejo'
            return 'Tequila - Añejo Tradicional', 'Añejo Tradicional', 'Añejo'
        elif es_crist:
            return 'Tequila - Añejo Cristalino', 'Añejo Cristalino', 'Añejo Cristalino'

        return 'Tequila - Otros', 'Otros', 'Otros'

    elif cat == 'Mezcal':
        keywords_silvestres = ['tobalá', 'tobala', 'cupreata', 'cuishe', 'cuixe', 'tepeztate', 'arroqueño', 'jabalí', 'ensamble', 'salmiana', 'barril', 'madrecuishe', 'cenizo', 'papalometl']
        es_silvestre = any(k in nom_l for k in keywords_silvestres)
        es_rep = 'reposado' in nom_l or 'rep ' in nom_l or 'rep.' in nom_l
        es_anejo = 'añejo' in nom_l or 'anejo' in nom_l
        es_crist = 'cristalino' in nom_l or 'crist ' in nom_l or 'crist.' in nom_l

        if es_silvestre and not es_rep and not es_anejo:
            return 'Mezcal - Silvestre', 'Silvestre', 'Joven Silvestre'
        elif es_crist and es_anejo:
            return 'Mezcal - Añejo', 'Añejo', 'Añejo Cristalino'
        elif es_crist:
            return 'Mezcal - Reposado Cristalino', 'Reposado Cristalino', 'Reposado Cristalino'
        elif es_anejo:
            return 'Mezcal - Añejo', 'Añejo', 'Añejo'
        elif es_rep:
            return 'Mezcal - Reposado', 'Reposado', 'Reposado'
        else:
            return 'Mezcal - Espadín Joven', 'Espadín Joven', 'Joven'

    elif cat == 'Whisky':
        return 'Whisky - Blended Scotch', 'Blended Scotch', 'Blended Scotch'
    elif cat == 'Licor de Whisky':
        return 'Licor de Whisky - Honey', 'Honey Liqueur', 'Honey Liqueur'
    elif cat == 'Vino':
        return 'Vino - Tinto Clericot', 'Tinto Clericot', 'Tinto Clericot'

    return cat, 'General', 'General'


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

    # Guardar archivos consolidados
    df.to_csv('data/catalogo_completo_consolidado.csv', index=False)
    df.to_csv('data/ranking_completo_general.csv', index=False)

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

    with open('data/dashboard_data.json', 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False)

    print(f"\n[OK] Total registros guardados en dashboard_data.json: {len(records)}")
    print("\nDistribución por Tienda:")
    print(df_dash['tienda'].value_counts())
    print("\nDistribución por Categoría Comparable:")
    print(df_dash['categoria_comparable'].value_counts())


if __name__ == '__main__':
    actualizar_todo()
