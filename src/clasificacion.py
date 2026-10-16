"""
Módulo Unificado de Clasificación, Normalización de Volumen y Reglas NOM.

Concentra la lógica de negocio del proyecto (NOM-006 para Tequila, NOM-070 para Mezcal,
Whisky Blended Scotch, Licor Honey y Vino Tinto de Mesa/Clericot) resolviendo los
hallazgos H1 y H2 de la auditoría técnica.

Funciones públicas:
- extraer_ml(nombre, ml_defecto=750) -> int
- corregir_ml_producto(nombre, ml_actual=750) -> int
- limpiar_precio(val) -> float | None
- clasificar_agave_mezcal(nombre) -> str
- clasificar_estricto(row_o_nombre, categoria=None) -> tuple[str, str, str]
- clasificar_categoria(nombre) -> tuple[str, str]
- detectar_categoria_base(nombre) -> str
"""

import re
from typing import Any, Tuple, Optional, Union

# ---------------------------------------------------------------------------
# Constantes y vocabularios normativos
# ---------------------------------------------------------------------------

KEYWORDS_SILVESTRES = [
    'tobalá', 'tobala', 'cupreata', 'cuishe', 'cuixe', 'madrecuishe',
    'madrecuixe', 'tepeztate', 'tepextate', 'arroqueño', 'arroqueno',
    'jabalí', 'jabali', 'barril', 'papalometl', 'sincoyote', 'ensamble',
    'silvestre', 'salmiana', 'cenizo'
]

KEYWORDS_BLENDED_WHISKY = [
    'blended', 'red label', 'black label', 'black & white', 'black and white',
    'ballantine', 'william lawson', 'dewar', 'grant', 'chivas', 'passport',
    'j&b', 'jb', 'famous grouse', 'white horse', 'bell', 'cutty sark',
    'johnnie walker', 'sir edward', 'vat 69', 'clan campbell', 'teachers',
    'teacher', 'buchanan', 'label 5', 'old parr', 'gold label', 'swing'
]

PALABRAS_EXCLUIDAS = [
    'vinagre', 'salsa', 'aderezo', 'aceite', 'mostaza', 'mermelada', 'jalea',
    'chocolate', 'bombon', 'bombón', 'pastel', 'rosca', 'galleta', 'helado',
    'paleta', 'gomita', 'dulce', 'vaso', 'copa', 'caballito', 'decantador',
    'licorera', 'sacacorchos', 'destapador', 'hielera', 'bolsa de regalo',
    'sal de ', 'sal con ', 'sangrita', 'mezclador', 'agua quina', 'agua tonica',
    'refresco', 'jugo', 'cerveza', 'sidra', 'rompope', 'jarabe', 'concentrado',
    'sin alcohol', '0.0%', 'desalcoholizado', 'lata ', 'latas', 'lemonade',
    'rtd ', 'cooler', 'hard seltzer', 'pachita', 'miniatura', 'crema de ',
    'licor de agave', 'licor de mezcal', 'bebida preparada', 'new mix',
    'carne', 'queso', 'jamon', 'jamón', 'chorizo', 'salchicha', 'estuche vacío',
    'aguamiel', 'bacanora'
]

# Marcas cuyo "Cristalino" (cuando el súper omite la palabra "Reposado")
# es normativamente un Reposado Cristalino bajo la NOM-006.
MARCAS_REPOSADO_CRISTALINO_POR_NORMA = [
    'centenario ultra', 'gran centenario ultra', 'cuervo tradicional',
    'jose cuervo tradicional', 'josé cuervo tradicional', 'jimador cristalino',
    'el jimador cristalino', 'viuda de romero', 'mayorazgo cristalino',
    'hacienda de tepa cristalino', 'hornitos cristalino', 'ollitas cristalino',
    'antiguo cristalino', 'orendain cristalino', 'manoderecha cristalino',
    'mano derecha', 'contraluz', 'herradura cristal ', 'herradura cristalino',
    'volcán de mi tierra', 'volcan de mi tierra', 'tierra noble cristalino',
    'el tequileño', 'casa loy'
]

CATEGORIAS_COMPARABLES_VALIDAS = [
    'Tequila - Añejo Cristalino',
    'Tequila - Reposado Cristalino',
    'Tequila - Añejo Tradicional',
    'Tequila - Reposado Tradicional',
    'Tequila - Blanco / Plata',
    'Mezcal - Silvestre',
    'Mezcal - Reposado Cristalino',
    'Mezcal - Añejo',
    'Mezcal - Reposado',
    'Mezcal - Espadín Joven',
    'Whisky - Blended Scotch',
    'Licor de Whisky - Honey',
    'Vino - Tinto Clericot'
]


# ---------------------------------------------------------------------------
# Extracción y corrección de volumen (H2 y H6)
# ---------------------------------------------------------------------------

def extraer_ml(nombre: str, ml_defecto: int = 750) -> int:
    """
    Extrae o normaliza el volumen en mililitros a partir del nombre del producto.
    
    Soporta:
    - Multipacks con indicación explícita (ej. "2 pzas de 750 ml" -> 1500, "Pack 6 ... 700ml" -> 4200)
    - Formato litros con decimales (ej. 1.75 L, 1.5 L, 4 L, 1 L)
    - Formato mililitros o cc con decimales (ej. 187.5 ml, 700 ml, 750cc, 946 ml)
    - Multiplicadores de paquete ("Pack de N", "Paquete de N", "N pack", "N botellas")
    - Miniaturas / pachitas (<650 ml) retornando el volumen correspondiente
    - Fallback seguro a ml_defecto si no se detecta patrón de volumen
    """
    if not nombre:
        return ml_defecto

    nom_l = str(nombre).lower()

    # 1. Multipacks explícitos de botellas completas: ej. "2 pzas de 750 ml", "6 botellas de 700 ml"
    m_pack = re.search(r'(\d+)\s*(?:pzas|piezas|botellas)\s*(?:de\s*)?(\d+)\s*ml', nom_l)
    if m_pack:
        return int(m_pack.group(1)) * int(m_pack.group(2))

    # 2. Detectar multiplicador de paquete (1 a 24 unidades)
    # Evitar colisión con ml (ej. "pack 750 ml" no debe tomar 750 como multiplicador)
    mult_pack = 1
    m_n_pack = re.search(r'\b(\d{1,2})\s*(?:pack|botellas?|piezas?|pzas?)\b', nom_l)
    if m_n_pack:
        mult_pack = int(m_n_pack.group(1))
    else:
        m_pack_de = re.search(r'\b(?:pack|paquete)\s*(?:de\s*)?(\d{1,2})\b(?!\s*(?:ml|mls|cc|l|lt|litro))', nom_l)
        if m_pack_de:
            mult_pack = int(m_pack_de.group(1))

    # 3. Formatos en litros (ej. 1.75 L, 1.75L, 4 L, 5 L, 1.5 L, 1 L, 1 Litro)
    m_l = re.search(r'(\d+(?:\.\d+)?)\s*(?:l|lt|lts|litro|litros)\b', nom_l)
    if m_l:
        val_l = float(m_l.group(1))
        if 0.35 <= val_l <= 6.0:
            return int(round(val_l * 1000)) * mult_pack

    # 4. Formatos en mililitros con posible decimal (ej. 187.5 ml, 700 ml, 750 ml, 946 ml, 750 cc)
    m_ml = re.search(r'(\d+(?:\.\d+)?)\s*(?:ml|mls|mililitros|cc)\b', nom_l)
    if m_ml:
        return int(round(float(m_ml.group(1)))) * mult_pack

    # 5. Menciones a miniaturas/pachitas sin volumen numérico
    if re.search(r'\b(?:pachitas?|miniaturas?)\b', nom_l):
        return 200 * mult_pack

    base_ml = int(ml_defecto) if (ml_defecto and int(ml_defecto) >= 350) else 750
    return base_ml * mult_pack


def corregir_ml_producto(nombre: str, ml_actual: int = 750) -> int:
    """Alias compatible para corregir_ml_producto."""
    return extraer_ml(nombre, ml_defecto=ml_actual)


# ---------------------------------------------------------------------------
# Limpieza y normalización de precios
# ---------------------------------------------------------------------------

def limpiar_precio(val: Any) -> Optional[float]:
    """
    Parsea y limpia representaciones de precio numéricas o en cadena de texto.
    Retorna float positivo o None si no es válido.
    """
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val) if val > 0 else None
    s = str(val).replace('\xa0', ' ').strip()
    m = re.search(r'[\$]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d+(?:\.\d{2})?)', s)
    if m:
        try:
            v = float(m.group(1).replace(',', ''))
            return v if v > 0 else None
        except ValueError:
            return None
    return None


# ---------------------------------------------------------------------------
# Identificación botánica de Agaves en Mezcal (NOM-070)
# ---------------------------------------------------------------------------

def clasificar_agave_mezcal(nombre: str) -> str:
    """
    Identifica la especie de agave o ensamble para mezcales según la NOM-070.
    """
    nom_l = str(nombre).lower()
    if 'espadín' in nom_l and ('tobalá' in nom_l or 'tobala' in nom_l):
        return 'Ensamble Espadín-Tobalá'
    if 'cuishe' in nom_l or 'cuixe' in nom_l:
        return 'Cuishe silvestre (A. karwinskii)'
    if 'tobalá' in nom_l or 'tobala' in nom_l:
        return 'Tobalá silvestre (A. potatorum)'
    if 'cupreata' in nom_l:
        return 'Cupreata silvestre (A. cupreata)'
    if 'tepeztate' in nom_l or 'tepextate' in nom_l:
        return 'Tepeztate silvestre (A. marmorata)'
    if 'arroqueño' in nom_l or 'arroqueno' in nom_l:
        return 'Arroqueño silvestre (A. americana)'
    if 'cenizo' in nom_l:
        return 'Cenizo silvestre (A. durangensis)'
    if 'salmiana' in nom_l:
        return 'Salmiana silvestre'
    if 'jabalí' in nom_l or 'jabali' in nom_l:
        return 'Jabalí silvestre (A. convallis)'
    if 'barril' in nom_l:
        return 'Barril silvestre (A. karwinskii)'
    if 'madrecuishe' in nom_l or 'madrecuixe' in nom_l:
        return 'Madrecuishe silvestre (A. karwinskii)'
    if 'papalometl' in nom_l:
        return 'Papalometl silvestre (A. potatorum)'
    if 'espadín' in nom_l or 'espadin' in nom_l:
        return 'Espadín (A. angustifolia)'
    return 'Agave mezcalero (NOM-070)'


# ---------------------------------------------------------------------------
# Detección y Clasificación Estricta (NOM-006 / NOM-070 / Licores)
# ---------------------------------------------------------------------------

def detectar_categoria_base(nombre: str) -> str:
    """Infiere la macro-categoría de bebida a partir del nombre del producto."""
    nom_l = str(nombre).lower()
    if "tequila" in nom_l:
        return "Tequila"
    if "mezcal" in nom_l:
        return "Mezcal"
    # Licor Honey de marcas de whisky
    if ("jack daniel" in nom_l or "passport" in nom_l or "jim beam" in nom_l or "wild turkey" in nom_l or "william lawson" in nom_l) and ("honey" in nom_l or "miel" in nom_l):
        return "Licor de Whisky"
    if "honey" in nom_l and ("whisky" in nom_l or "whiskey" in nom_l):
        return "Licor de Whisky"
    if "whisky" in nom_l or "whiskey" in nom_l or any(k in nom_l for k in KEYWORDS_BLENDED_WHISKY):
        return "Whisky"
    if "vino" in nom_l or "carlo rossi" in nom_l or "lambrusco" in nom_l or "padre kino" in nom_l or "california" in nom_l:
        return "Vino"
    return "Otros"


def clasificar_estricto(
    row_o_nombre: Union[dict, Any, str],
    categoria: Optional[str] = None
) -> Tuple[str, str, str]:
    """
    Clasifica estrictamente un producto bajo las normas oficiales y el estándar del proyecto.
    
    Acepta:
    - Un dict o pd.Series con claves 'producto' y 'categoria'
    - Un nombre de producto (str) y una categoría opcional (str)
    
    Retorna:
    - (categoria_comparable, subcategoria, clase)
    """
    if isinstance(row_o_nombre, str):
        nom = row_o_nombre.strip()
        cat = categoria or detectar_categoria_base(nom)
    elif hasattr(row_o_nombre, 'get'):
        nom = str(row_o_nombre.get('producto', '')).strip()
        cat = str(row_o_nombre.get('categoria', '') or categoria or detectar_categoria_base(nom)).strip()
    else:
        # pd.Series / objeto indexable
        nom = str(row_o_nombre['producto']).strip()
        cat = str(row_o_nombre.get('categoria', categoria or detectar_categoria_base(nom))).strip()

    nom_l = nom.lower()

    # -----------------------------------------------------------------------
    # TEQUILA (NOM-006-SCFI)
    # -----------------------------------------------------------------------
    if cat == 'Tequila' or 'tequila' in nom_l:
        # 1. BLANCO / PLATA (0 meses barrica)
        if ('plata' in nom_l or 'blanco' in nom_l or 'silver' in nom_l) and not ('añejo' in nom_l or 'anejo' in nom_l or 'reposado' in nom_l):
            return 'Tequila - Blanco / Plata', 'Blanco', 'Blanco'
        if 'don ramón plata' in nom_l or 'don ramon plata' in nom_l:
            return 'Tequila - Blanco / Plata', 'Blanco', 'Blanco'

        # 2. CASO DON JULIO 70 (Añejo Cristalino por NOM-006)
        if 'don julio 70' in nom_l or 'don julio 70 añejo' in nom_l:
            return 'Tequila - Añejo Cristalino', 'Añejo Cristalino', 'Añejo Cristalino'

        # 3. CASO DON RAMÓN
        if 'don ramón' in nom_l or 'don ramon' in nom_l:
            if 'añejo cristalino' in nom_l or ('añejo' in nom_l and ('platinium' in nom_l or 'cristalino' in nom_l)):
                return 'Tequila - Añejo Cristalino', 'Añejo Cristalino', 'Añejo Cristalino'
            elif 'reposado cristalino' in nom_l or ('reposado' in nom_l and ('platinium' in nom_l or 'cristalino' in nom_l)):
                return 'Tequila - Reposado Cristalino', 'Reposado Cristalino', 'Reposado Cristalino'
            elif 'reposado' in nom_l:
                return 'Tequila - Reposado Tradicional', 'Reposado', 'Reposado'
            elif 'añejo' in nom_l or 'dark' in nom_l:
                return 'Tequila - Añejo Tradicional', 'Añejo Tradicional', 'Añejo'

        # 4. MARCAS REPOSADO CRISTALINO POR NORMA (cuando omiten la palabra 'Reposado')
        if any(m in nom_l for m in MARCAS_REPOSADO_CRISTALINO_POR_NORMA) and not ('añejo' in nom_l or 'anejo' in nom_l or 'ultra añejo' in nom_l):
            return 'Tequila - Reposado Cristalino', 'Reposado Cristalino', 'Reposado Cristalino'

        # 5. MAESTRO DOBEL DIAMANTE (Ensamble clarificado carbón activado -> Añejo Cristalino)
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

    # -----------------------------------------------------------------------
    # MEZCAL (NOM-070-SCFI)
    # -----------------------------------------------------------------------
    elif cat == 'Mezcal' or 'mezcal' in nom_l:
        es_silvestre = any(k in nom_l for k in KEYWORDS_SILVESTRES)
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

    # -----------------------------------------------------------------------
    # OTROS DESTILADOS Y BEBIDAS
    # -----------------------------------------------------------------------
    elif cat == 'Whisky' or 'whisky' in nom_l or 'whiskey' in nom_l:
        return 'Whisky - Blended Scotch', 'Blended Scotch', 'Blended Scotch'
    elif cat == 'Licor de Whisky' or ('honey' in nom_l and ('whisky' in nom_l or 'whiskey' in nom_l or 'jack' in nom_l)):
        return 'Licor de Whisky - Honey', 'Honey Liqueur', 'Honey Liqueur'
    elif cat == 'Vino' or 'vino' in nom_l:
        return 'Vino - Tinto Clericot', 'Tinto Clericot', 'Tinto Clericot'

    return cat, 'General', 'General'


def clasificar_categoria(nombre: str) -> Tuple[str, str]:
    """
    Función de compatibilidad para scrapers simples.
    Retorna (categoria_principal, subcategoria).
    """
    cat_base = detectar_categoria_base(nombre)
    _, subcat, _ = clasificar_estricto(nombre, cat_base)
    return cat_base, subcat
