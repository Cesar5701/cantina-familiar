"""
Normalización textual de etiquetas de productos y detección de combos/paquetes (H8, H35, H38).
"""

import re
import unicodedata
from typing import Any, NamedTuple, Optional

import pandas as pd

from src.catalogo.detector_volumen import extraer_ml


class ReglaNormalizacion(NamedTuple):
    """Estructura declarativa para reglas de normalización textual (H38)."""

    patron: re.Pattern
    reemplazo: str
    nombre: str


# =====================================================================
# TABLA DECLARATIVA DE NORMALIZACIÓN DE PRODUCTOS Y ETIQUETAS (H38)
# =====================================================================
REGLAS_NORMALIZACION_CLAVE: tuple[ReglaNormalizacion, ...] = (
    # 1. Unificar posesivos ingleses eliminando apóstrofes (Daniel's / Daniel’s -> Daniels, Buchanan's -> Buchanans)
    ReglaNormalizacion(re.compile(r"['’`]"), "", "unificar_posesivos"),
    # 2. Eliminar especificaciones de volumen en el título (ej. 700 ml, 750ml, 1.75 L, 1 L, 750 mililitros)
    ReglaNormalizacion(
        re.compile(r"\b\d+(\.\d+)?\s*(ml|l|litros?|mililitros?)\b", re.IGNORECASE),
        " ",
        "eliminar_volumen",
    ),
    # 3. Unificar variantes ortográficas de bebidas (whiskey/wisky -> whisky, licor de whisky -> whisky)
    ReglaNormalizacion(re.compile(r"\b(whiskey|wisky)\b", re.IGNORECASE), "whisky", "variantes_whisky"),
    ReglaNormalizacion(re.compile(r"\blicor\s+de\s+whisky\b", re.IGNORECASE), "whisky", "licor_de_whisky"),
    ReglaNormalizacion(re.compile(r"\blicor\s+de\b", re.IGNORECASE), " ", "prefijo_licor"),
    # 4. Omitir descriptores regionales/opcionales en marcas reconocidas (ej. Tennessee en Jack Daniel's)
    ReglaNormalizacion(re.compile(r"\btennessee?\b", re.IGNORECASE), " ", "descriptor_regional"),
    # 5. Abreviaturas de reposado frecuentes en retail (Rep -> reposado)
    ReglaNormalizacion(re.compile(r"\brep\.?(?!\w)", re.IGNORECASE), "reposado", "abreviatura_reposado"),
    # 6. Descriptores de pureza de agave / artesanales / envase genérico en Tequila y Mezcal
    ReglaNormalizacion(
        re.compile(r"\b100%?\s*(puro\s+de\s+|de\s+)?(agave(\s+azul)?)?\b", re.IGNORECASE),
        " ",
        "pureza_agave",
    ),
    ReglaNormalizacion(re.compile(r"\b(artesanal|botella)\b", re.IGNORECASE), " ", "descriptores_envase"),
    # 7. Descriptores genéricos de Scotch en Whisky
    ReglaNormalizacion(re.compile(r"\bblended\s+scotch\b", re.IGNORECASE), " ", "blended_scotch"),
    ReglaNormalizacion(re.compile(r"\bscotch\b", re.IGNORECASE), " ", "descriptor_scotch"),
    # 8. Espaciado en marcas conocidas (Mc Harrison -> Mcharrison)
    ReglaNormalizacion(re.compile(r"\bmc\s+harrison\b", re.IGNORECASE), "mcharrison", "marca_mcharrison"),
    # 9. Normalización de Cristalinos de clase única en Tequila y Mezcal
    ReglaNormalizacion(
        re.compile(r"\bpatron\s+cristalino\b", re.IGNORECASE),
        "patron anejo cristalino",
        "patron_cristalino",
    ),
    ReglaNormalizacion(
        re.compile(r"\bdobel\s+diamante\s+cristalino\b", re.IGNORECASE),
        "dobel diamante",
        "dobel_diamante",
    ),
    ReglaNormalizacion(
        re.compile(r"\b(mayorazgo|ollitas|viuda\s+de\s+romero|contraluz)\s+cristalino\b", re.IGNORECASE),
        r"\1 reposado cristalino",
        "marcas_reposado_cristalino",
    ),
    # 10. Normalización de Jack Daniel's Old No. 7 estándar (cuando el súper omite 'Old No. 7' o 'No. 7')
    ReglaNormalizacion(
        re.compile(
            r"\bjack\s+daniels?\b(?!\s+(?:honey|apple|gentleman|single\s+barrel|blackberry|fire|cola|mclaren|rye|sin\s+alcohol))\s*(?:old\s*no\.?\s*7|no\.?\s*7)?",
            re.IGNORECASE,
        ),
        "jack daniels old no 7",
        "jack_daniels_old_no_7",
    ),
    # 11. Variantes ortográficas de marcas y ediciones (Crystalgold -> crystal gold)
    ReglaNormalizacion(
        re.compile(r"\bcrystalgold\b", re.IGNORECASE),
        "crystal gold",
        "chivas_crystal_gold",
    ),
)


STOP_WORDS_CLAVE: frozenset[str] = frozenset(
    {"de", "del", "el", "la", "los", "las", "en", "para", "licor", "100", "y", "a", "al", "c"}
)


def normalizar_texto_clave(texto: str) -> str:
    """Normaliza un nombre de producto aplicando la tabla declarativa REGLAS_NORMALIZACION_CLAVE (H38), eliminando acentos, stop-words y unificando el volumen estándar (650-800 ml) para match cross-tienda (H8 / H35). Preserva el tamaño canónico para formatos no estándar (<650 o >800 ml)."""
    if not texto or pd.isnull(texto):
        return ""

    s_orig = str(texto).strip()
    # H35: Extraer volumen previo a la limpieza para preservar formatos no estándar
    ml = extraer_ml(s_orig, ml_defecto=750)

    s = unicodedata.normalize("NFKD", s_orig).encode("ascii", "ignore").decode("utf-8")
    s = re.sub(r"[\-_/]+", " ", s)

    # Aplicar tabla declarativa de transformaciones por regex compiladas (H38)
    for regla in REGLAS_NORMALIZACION_CLAVE:
        s = regla.patron.sub(regla.reemplazo, s)

    s = re.sub(r"[^a-zA-Z0-9\s]", " ", s.lower())
    s = re.sub(r"\s+", " ", s).strip()
    tokens = [t for t in s.split() if t and t not in STOP_WORDS_CLAVE]

    # Blindaje H35: botellas no estándar (<650 ml o >800 ml) conservan su tamaño canónico
    if ml and (ml < 650 or ml > 800):
        tokens.append(f"{ml}ml")

    tokens.sort()
    return " ".join(tokens)


def es_producto_paquete(row_o_nombre: Any, condiciones: Optional[str] = None) -> bool:
    """
    Identifica si un producto es un paquete, combo promocional, kit o edición con obsequio.
    """
    if isinstance(row_o_nombre, str):
        nom = row_o_nombre
        cond = condiciones or ""
    elif hasattr(row_o_nombre, "get"):
        nom = str(row_o_nombre.get("producto", ""))
        cond = str(row_o_nombre.get("condiciones", ""))
    else:
        nom = str(row_o_nombre["producto"])
        cond = str(row_o_nombre.get("condiciones", ""))

    cond_l = cond.lower()
    nom_l = nom.lower()

    # Normalizar acentos para robustez en búsquedas
    nom_norm = unicodedata.normalize("NFKD", nom_l).encode("ascii", "ignore").decode("utf-8")
    cond_norm = unicodedata.normalize("NFKD", cond_l).encode("ascii", "ignore").decode("utf-8")

    if (
        "🎁" in cond
        or "obsequio" in cond_norm
        or "combo" in cond_norm
        or "kit" in cond_norm
        or "paquete" in cond_norm
        or "regalo" in cond_norm
    ):
        return True

    # 1. Palabras clave de paquetes, combos, multipacks y promociones 2x1 / 3x2 en el nombre
    patron_multipack = (
        r"\b(?:pack|duopack|tripack|multipack|paquete|combo|kit|caja|set)\b"
        r"|\b\d+\s*pzas?\b"
        r"|\bx\s*\d+\b"
        r"|\b\d+\s*botellas?\b"
        r"|\b(?:pack\s*)?[234]x[123]\b"
    )
    if re.search(patron_multipack, nom_norm):
        return True

    # 2. Cristalería, accesorios y ediciones especiales con obsequio
    patron_accesorios = (
        r"vasos?|copas?|tarros?|hieleras?|termos?|shakers?|tumblers?|caballitos?|"
        r"sal\b|kit|estuches?|cilindros?|mezclador(?:es)?|escurridor(?:es)?|destapador(?:es)?|mandil(?:es)?"
    )

    if re.search(r"\bedici[oó]n\s+especial\s+con\b", nom_norm) or re.search(
        rf"\bcon\s+(?:\d+\s*)?(?:{patron_accesorios})", nom_norm
    ):
        return True

    # 3. Detección de complementos en el nombre con '+' o 'c/'
    if "+" in nom_norm or "c/" in nom_norm or "con" in nom_norm:
        if re.search(
            rf"\+\s*(?:\d*\s*(?:{patron_accesorios}|bot|agua|refresco|chivas|jack|absolut|woodford|mason)|\d+)",
            nom_norm,
        ):
            return True
        if re.search(
            rf"c\/\s*(?:\d*\s*(?:{patron_accesorios}|bot|balon|porta|concentrado|tamborin|sangria|tinto|vino|ultra|reposado|joven|pechuga)|\d+)",
            nom_norm,
        ):
            return True

    return False
