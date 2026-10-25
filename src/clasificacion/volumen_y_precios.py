"""
Extracción y normalización de volumen (ml / L) y parseo de precios (H2 y H6).
"""

import re
from typing import Any, Optional


def limpiar_obsequios_mezcladores_para_volumen(nom_l: str) -> str:
    """
    Aísla el nombre del producto principal eliminando cláusulas de obsequio,
    mezcladores, aguas, refrescos o cristalería agregados para evitar que sus
    volúmenes o unidades inflen o sustituyan el volumen real de la botella de licor.
    """
    pat_obsequio = re.compile(
        r"(\+|\bcon\b|\bc/\b|\bmás\b|\bmas\b|\bincluye\b|\bobsequio\b|\bgratis\b)\s*.*?"
        r"\b(?:agua|mineral|squirt|peñafiel|penafiel|refresco|soda|coca|perrier|panna|topo\s*chico|vaso|copa|tarro|hielera|termo|sal\b|botana).*$",
        re.IGNORECASE,
    )
    limpio = pat_obsequio.sub("", nom_l).strip()
    return limpio if len(limpio) >= 6 else nom_l


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
    nom_l_analizar = limpiar_obsequios_mezcladores_para_volumen(nom_l)

    # 1. Multipacks explícitos de botellas completas: ej. "2 pzas de 750 ml", "6 botellas de 700 ml"
    m_pack = re.search(r"(\d+)\s*(?:pzas|piezas|botellas)\s*(?:de\s*)?(\d+)\s*ml", nom_l_analizar)
    if m_pack:
        return int(m_pack.group(1)) * int(m_pack.group(2))

    # 2. Detectar multiplicador de paquete (1 a 24 unidades): Pack N, Pack de N, Pack x N, N pack, x N
    # Evitar colisión con ml (ej. "pack 750 ml" no debe tomar 750 como multiplicador)
    mult_pack = 1
    m_n_pack = re.search(r"\b(\d{1,2})\s*(?:pack|botellas?|bot|piezas?|pzas?)\b", nom_l_analizar)
    if m_n_pack:
        mult_pack = int(m_n_pack.group(1))
    else:
        m_pack_de = re.search(
            r"\b(?:pack|paquete|caja)\s*(?:de\s*|x\s*)?(\d{1,2})\b(?!\s*(?:ml|mls|cc|l|lt|litro))", nom_l_analizar
        )
        if m_pack_de:
            mult_pack = int(m_pack_de.group(1))
        else:
            m_x_n = re.search(r"\bx\s*(\d{1,2})\b(?!\s*(?:ml|mls|cc|l|lt|litro))", nom_l_analizar)
            if m_x_n:
                mult_pack = int(m_x_n.group(1))

    # 3. Formatos en litros (ej. 1.75 L, 1.75L, 4 L, 5 L, 1.5 L, 1 L, 1 Litro)
    m_l = re.search(r"(\d+(?:\.\d+)?)\s*(?:l|lt|lts|litro|litros)\b", nom_l_analizar)
    if m_l:
        val_l = float(m_l.group(1))
        if 0.35 <= val_l <= 6.0:
            return round(val_l * 1000) * mult_pack

    # 4. Formatos en mililitros con posible decimal (ej. 187.5 ml, 700 ml, 750 ml, 946 ml, 750 cc)
    m_ml = re.search(r"(\d+(?:\.\d+)?)\s*(?:ml|mls|mililitros|cc)\b", nom_l_analizar)
    if m_ml:
        return round(float(m_ml.group(1))) * mult_pack

    # 5. Menciones a miniaturas/pachitas sin volumen numérico
    if re.search(r"\b(?:pachitas?|miniaturas?)\b", nom_l):
        return 200 * mult_pack

    base_ml = int(ml_defecto) if (ml_defecto and int(ml_defecto) >= 350) else 750
    return base_ml * mult_pack


def corregir_ml_producto(nombre: str, ml_actual: int = 750) -> int:
    """Alias compatible para corregir_ml_producto."""
    return extraer_ml(nombre, ml_defecto=ml_actual)


def normalizar_medidas_en_nombre(nombre: str) -> str:
    """
    Separa y unifica el espaciado/unidad de las medidas (ml y L) dentro de un
    nombre de producto. Convierte <1000 ml a 'ml' y >=1000 ml a 'L'.
    Idempotente. No suma volúmenes de medidas múltiples.
    """
    if not nombre:
        return nombre
    U_ML = r"mililitros|mililitro|mls|ml|cc"
    U_L = r"litros|litro|lts|lt|l"
    patron = re.compile(rf"(?P<num>\d+(?:[.,]\d+)?)\s*(?P<u>{U_ML}|{U_L})\b", re.IGNORECASE)

    def _repl(m):
        num = m.group("num").replace(",", ".")
        u = m.group("u").lower()
        ml = float(num) * 1000.0 if u in {"l", "lt", "lts", "litro", "litros"} else float(num)
        if ml >= 1000:
            texto = f"{ml / 1000:.3f}".rstrip("0").rstrip(".")
            return f"{texto} L"
        return f"{int(ml)} ml" if ml == int(ml) else f"{ml} ml"

    resultado = patron.sub(_repl, str(nombre))
    return re.sub(r"\s+", " ", resultado).strip()


def limpiar_precio(val: Any) -> Optional[float]:
    """
    Parsea y limpia representaciones de precio numéricas o en cadena de texto.
    Retorna float positivo o None si no es válido.
    """
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val) if val > 0 else None
    s = str(val).replace("\xa0", " ").strip()
    m = re.search(r"[\$]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d+(?:\.\d{2})?)", s)
    if m:
        try:
            v = float(m.group(1).replace(",", ""))
            return v if v > 0 else None
        except ValueError:
            return None
    return None
