"""
Suite de Pruebas de Regresión con Fixtures Reales Congelados (Bloque Q2).

Garantiza que los parsers de Walmart (Next.js SSR pasillos y PDP), VTEX (Chedraui y Bodegas Alianza),
SFCC (Soriana .product-tile) y SAP Commerce OCC v2 (Costco) procesen correctamente las estructuras
de datos crudas de cada retailer y detecten inmediatamente cualquier cambio o desviación de esquema.
"""

import json
from pathlib import Path
from unittest.mock import patch

from bs4 import BeautifulSoup

from src.clasificacion import limpiar_precio
from src.scraper_catalogo_completo.clasificador_alianza import evaluar_item_alianza
from src.scraper_multitienda.chedraui import scrapear_chedraui
from src.scraper_multitienda.costco import scrapear_costco
from src.scraper_multitienda.soriana import scrapear_soriana
from src.scraper_multitienda.walmart_sams import extraer_item_nextjs

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_fixture_walmart_nextjs_pasillo():
    """Valida la extracción de productos y filtrado de descartes desde el HTML real de pasillo Next.js."""
    fixture_path = FIXTURES_DIR / "walmart_nextjs_pasillo.html"
    assert fixture_path.exists(), f"No se encontró el fixture {fixture_path}"

    html = fixture_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    script = soup.find("script", id="__NEXT_DATA__")
    assert script and script.string

    data = json.loads(script.string)
    item_stacks = data["props"]["pageProps"]["initialData"]["searchResult"]["itemStacks"]
    items = item_stacks[0]["items"]
    assert len(items) == 4

    # 1. Tequila Maestro Dobel Diamante
    item_dobel, out_1 = extraer_item_nextjs(
        it=items[0],
        tienda="Walmart",
        base_domain="www.walmart.com.mx",
        fecha_actual="2026-11-09 18:00",
    )
    assert not out_1
    assert item_dobel is not None
    assert item_dobel["producto"] == "Tequila Maestro Dobel Diamante 750 ml"
    assert item_dobel["ml"] == 750
    assert item_dobel["categoria"] == "Tequila"
    assert item_dobel["precio_promo"] == 685.0
    assert item_dobel["precio_regular"] == 820.0
    assert item_dobel["disponibilidad"] == "disponible"
    assert item_dobel["url"] == "https://www.walmart.com.mx/ip/tequila-maestro-dobel-diamante-750-ml/00750100518386"

    # 2. Whisky Johnnie Walker Black Label
    item_jw, out_2 = extraer_item_nextjs(
        it=items[1],
        tienda="Walmart",
        base_domain="www.walmart.com.mx",
        fecha_actual="2026-11-09 18:00",
    )
    assert not out_2
    assert item_jw is not None
    assert item_jw["categoria"] == "Whisky"
    assert item_jw["precio_promo"] == 799.0
    assert item_jw["precio_regular"] == 950.0

    # 3. Mezcal 400 Conejos Espadín
    item_mezcal, out_3 = extraer_item_nextjs(
        it=items[2],
        tienda="Walmart",
        base_domain="www.walmart.com.mx",
        fecha_actual="2026-11-09 18:00",
    )
    assert not out_3
    assert item_mezcal is not None
    assert item_mezcal["categoria"] == "Mezcal"
    assert item_mezcal["precio_promo"] == 540.0
    assert item_mezcal["precio_regular"] == 540.0

    # 4. Refresco descartable (no vino ni licor)
    item_cola, _ = extraer_item_nextjs(
        it=items[3],
        tienda="Walmart",
        base_domain="www.walmart.com.mx",
        fecha_actual="2026-11-09 18:00",
    )
    assert item_cola is None


def test_fixture_walmart_pdp_nodriver():
    """Valida la extracción de metadatos de producto PDP para automatización CDP."""
    fixture_path = FIXTURES_DIR / "walmart_pdp.html"
    assert fixture_path.exists()

    html = fixture_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    script = soup.find("script", id="__NEXT_DATA__")
    assert script and script.string

    data = json.loads(script.string)
    prod = data["props"]["pageProps"]["initialData"]["data"]["product"]

    nombre = prod.get("name")
    marca = prod.get("brand")
    disp = prod.get("availabilityStatus")
    price_info = prod.get("priceInfo", {})

    cur_price = price_info.get("currentPrice", {}).get("price")
    was_price = price_info.get("wasPrice", {}).get("price")

    p_promo = limpiar_precio(cur_price)
    p_reg = limpiar_precio(was_price) or p_promo

    assert nombre == "Tequila Don Julio 70 Cristalino 700 ml"
    assert marca == "Don Julio"
    assert disp == "IN_STOCK"
    assert p_promo == 945.0
    assert p_reg == 1100.0


def test_fixture_vtex_chedraui_regression():
    """Valida el pipeline completo de Chedraui sobre el fixture JSON crudo de VTEX."""
    fixture_path = FIXTURES_DIR / "vtex_search_response.json"
    assert fixture_path.exists()

    raw_data = json.loads(fixture_path.read_text(encoding="utf-8"))

    with patch("src.scraper_multitienda.chedraui._pkg.descargar_json_con_reintentos", return_value=raw_data):
        with patch("src.scraper_multitienda.chedraui.pausa_aleatoria"):
            prods = scrapear_chedraui(terminos=["tequila"])

    assert len(prods) == 2

    # Producto 1: Herradura Reposado
    p1 = next(p for p in prods if "Herradura" in p["producto"])
    assert p1["tienda"] == "Chedraui"
    assert p1["ml"] == 700
    assert p1["precio_promo"] == 580.0
    assert p1["precio_regular"] == 690.0
    assert p1["stock_unidades"] == 12
    assert p1["disponibilidad"] == "disponible"

    # Producto 2: Buchanan's 12
    p2 = next(p for p in prods if "Buchanan" in p["producto"])
    assert p2["ml"] == 750
    assert p2["precio_promo"] == 750.0
    assert p2["precio_regular"] == 890.0
    assert p2["stock_unidades"] == 8


def test_fixture_vtex_alianza_regression():
    """Valida la clasificación y normalización de Bodegas Alianza sobre el fixture VTEX."""
    from src.io_utils import ResumenScraping

    fixture_path = FIXTURES_DIR / "vtex_search_response.json"
    raw_data = json.loads(fixture_path.read_text(encoding="utf-8"))
    resumen = ResumenScraping("Alianza")

    # Item 1: Herradura
    it_herradura = raw_data[0]
    norm_1 = evaluar_item_alianza(it_herradura, fecha_actual="2026-11-09 18:00", resumen=resumen)
    assert norm_1 is not None
    assert norm_1["categoria"] == "Tequila"
    assert norm_1["ml"] == 700
    assert norm_1["precio_promo"] == 580.0
    assert norm_1["precio_regular"] == 690.0
    assert norm_1["disponibilidad"] == "disponible"

    # Item 2: Buchanan's
    it_buchanans = raw_data[1]
    norm_2 = evaluar_item_alianza(it_buchanans, fecha_actual="2026-11-09 18:00", resumen=resumen)
    assert norm_2 is not None
    assert norm_2["categoria"] == "Whisky"
    assert norm_2["ml"] == 750
    assert norm_2["precio_promo"] == 750.0

    # Item 4: Sabritas (debe descartarse)
    it_sabritas = raw_data[3]
    norm_4 = evaluar_item_alianza(it_sabritas, fecha_actual="2026-11-09 18:00", resumen=resumen)
    assert norm_4 is None


def test_fixture_sfcc_soriana_regression():
    """Valida la extracción de productos y detección de agotados en Soriana con el fixture HTML SFCC."""
    fixture_path = FIXTURES_DIR / "soriana_product_tile.html"
    assert fixture_path.exists()

    html = fixture_path.read_text(encoding="utf-8")

    with patch("src.scraper_multitienda.soriana._pkg.descargar_html_con_reintentos", return_value=html):
        with patch("src.scraper_multitienda.soriana.pausa_aleatoria"):
            prods = scrapear_soriana(terminos=["tequila"])

    assert len(prods) == 3

    # 1. Tequila 1800 Cristalino
    p_1800 = next(p for p in prods if "1800" in p["producto"])
    assert p_1800["tienda"] == "Soriana"
    assert p_1800["ml"] == 700
    assert p_1800["precio_promo"] == 599.0
    assert p_1800["precio_regular"] == 720.0
    assert p_1800["disponibilidad"] == "disponible"
    assert "soriana.com" in p_1800["url"]

    # 2. Vino Casillero del Diablo
    p_vino = next(p for p in prods if "Casillero" in p["producto"])
    assert p_vino["ml"] == 750
    assert p_vino["precio_promo"] == 245.0
    assert p_vino["precio_regular"] == 245.0
    assert p_vino["disponibilidad"] == "disponible"

    # 3. Whisky Johnnie Walker Blue Label (Agotado)
    p_jw = next(p for p in prods if "Blue Label" in p["producto"])
    assert p_jw["disponibilidad"] == "agotado"
    assert p_jw["precio_promo"] == 7900.0


def test_fixture_occ_costco_regression():
    """Valida el scraper de Costco sobre el fixture JSON crudo de SAP Commerce Cloud OCC v2."""
    fixture_path = FIXTURES_DIR / "costco_occ_search.json"
    assert fixture_path.exists()

    raw_json = json.loads(fixture_path.read_text(encoding="utf-8"))

    with patch("src.scraper_multitienda.costco._pkg.descargar_json_con_reintentos", return_value=raw_json):
        with patch("src.scraper_multitienda.costco.pausa_aleatoria"):
            prods = scrapear_costco(terminos=["tequila"])

    assert len(prods) == 1
    prod = prods[0]
    assert prod["tienda"] == "Costco"
    assert "Don Ramón" in prod["producto"]
    assert prod["ml"] == 750
    assert prod["precio_promo"] == 589.99
    assert prod["precio_regular"] == 689.99
    assert prod["stock_unidades"] == 25
    assert prod["disponibilidad"] == "disponible"
    assert "Ahorra $100.00" in prod["condiciones"]
