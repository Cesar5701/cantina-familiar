"""
Suite de pruebas unitarias para scraper_selenium.py (H34).
Cubre la lógica pura de parseo (JSON-LD, __NEXT_DATA__, DOM con BeautifulSoup),
detección de desafíos/WAF con mocks y control de flujo del scraper sin requerir navegador real.
"""

from unittest.mock import MagicMock, patch

from bs4 import BeautifulSoup
from selenium.common.exceptions import WebDriverException

from src.scraper_selenium import (
    _construir_registro_producto,
    consultar_urls_secuenciales,
    detectar_desafio,
    extraer_de_json_embebido,
    inicializar_driver,
    parsear_html_con_bs4,
    pausa_humana,
    verificar_y_esperar_desafio,
)

# ---------------------------------------------------------------------------
# 1. Pruebas de construcción y estandarización de registros
# ---------------------------------------------------------------------------


def test_construir_registro_producto():
    """Valida que _construir_registro_producto genere el esquema normalizado."""
    rec = _construir_registro_producto(
        tienda="Sam's Club",
        nombre="Tequila 1800 Cristalino Añejo 700 ml",
        precio_regular=850.0,
        precio_promo=699.0,
        condicion="Descuento en línea",
        url="https://www.sams.com.mx/p/tequila-1800/123",
        fecha_consulta="2026-10-17 12:00",
    )
    assert rec["tienda"] == "Sam's Club"
    assert rec["producto"] == "Tequila 1800 Cristalino Añejo 700 ml"
    assert rec["categoria"] == "Tequila"
    assert rec["subcategoria"] == "Añejo Cristalino"
    assert rec["ml"] == 700
    assert rec["abv"] == 38.0
    assert rec["precio_regular"] == 850.0
    assert rec["precio_promo"] == 699.0
    assert rec["condiciones"] == "Descuento en línea"
    assert rec["confianza"] == "Confirmado"


# ---------------------------------------------------------------------------
# 2. Pruebas de extracción de JSON embebido (JSON-LD y __NEXT_DATA__)
# ---------------------------------------------------------------------------


def test_extraer_de_json_embebido_json_ld():
    """Valida la extracción de productos desde bloques JSON-LD con @type ItemList."""
    html = """
    <html>
      <head>
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "ItemList",
          "itemListElement": [
            {
              "@type": "ListItem",
              "position": 1,
              "item": {
                "@type": "Product",
                "name": "Tequila Don Julio 70 Añejo Cristalino 700 ml",
                "url": "https://www.sams.com.mx/p/don-julio-70",
                "offers": {
                  "@type": "Offer",
                  "price": "899.00",
                  "priceCurrency": "MXN"
                }
              }
            }
          ]
        }
        </script>
      </head>
      <body></body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    prods = extraer_de_json_embebido(soup, "https://www.sams.com.mx", "Sam's Club", "2026-10-17 12:00")
    assert len(prods) == 1
    p = prods[0]
    assert p["producto"] == "Tequila Don Julio 70 Añejo Cristalino 700 ml"
    assert p["precio_promo"] == 899.0
    assert p["ml"] == 700
    assert "JSON-LD" in p["condiciones"]


def test_extraer_de_json_embebido_next_data():
    """Valida la extracción recursiva desde el script __NEXT_DATA__ de Next.js/Electrode."""
    html = """
    <html>
      <head>
        <script id="__NEXT_DATA__" type="application/json">
        {
          "props": {
            "pageProps": {
              "initialData": {
                "searchResult": {
                  "items": [
                    {
                      "name": "Mezcal 400 Conejos Joven Espadín 750 ml",
                      "priceInfo": {
                        "price": 549.0
                      },
                      "productUrl": "/ip/mezcal-400-conejos/999"
                    },
                    {
                      "displayName": "Whisky Johnnie Walker Black Label 750 ml",
                      "itemPrice": "$750.00",
                      "canonicalUrl": "/ip/jw-black/888"
                    }
                  ]
                }
              }
            }
          }
        }
        </script>
      </head>
      <body></body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    prods = extraer_de_json_embebido(soup, "https://www.walmart.com.mx", "Walmart", "2026-10-17 12:00")
    assert len(prods) == 2
    nombres = [p["producto"] for p in prods]
    assert "Mezcal 400 Conejos Joven Espadín 750 ml" in nombres
    assert "Whisky Johnnie Walker Black Label 750 ml" in nombres
    assert all("__NEXT_DATA__" in p["condiciones"] for p in prods)


def test_extraer_de_json_embebido_corrupto_o_irrelevante():
    """Valida que scripts JSON corruptos o no estructurados se ignoren sin lanzar excepciones."""
    html = """
    <html>
      <head>
        <script type="application/json">{ corrupto invalid json ... }</script>
        <script type="application/json">{"@type": "BreadcrumbList", "items": []}</script>
        <script type="application/json">short</script>
      </head>
      <body></body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    prods = extraer_de_json_embebido(soup, "https://www.test.com", "Tienda", "2026-10-17 12:00")
    assert prods == []


# ---------------------------------------------------------------------------
# 3. Pruebas de parseo HTML completo con BeautifulSoup
# ---------------------------------------------------------------------------


def test_parsear_html_pdp_producto_individual():
    """Valida el parseo en página individual de producto (PDP) con etiqueta <h1> y precio."""
    html = """
    <html>
      <body>
        <h1 class="product-title">Tequila Maestro Dobel Diamante 700 ml</h1>
        <div class="product-price-val">$649.00</div>
      </body>
    </html>
    """
    prods = parsear_html_con_bs4(html, "https://www.sams.com.mx/p/dobel-diamante", "Sam's Club")
    assert len(prods) == 1
    p = prods[0]
    assert p["producto"] == "Tequila Maestro Dobel Diamante 700 ml"
    assert p["precio_promo"] == 649.0
    assert p["ml"] == 700


def test_parsear_html_plp_tarjetas_de_catalogo():
    """Valida el parseo en listado de búsqueda (PLP) con tarjetas de producto y descuentos."""
    html = """
    <html>
      <body>
        <div data-testid="product-card">
          <a class="product-title-link" href="/p/tequila-herradura-ultra/101">Tequila Herradura Ultra Añejo 700 ml</a>
          <div class="price-old">$799.00</div>
          <div class="price-val">$647.56</div>
        </div>
        <div data-testid="product-card">
          <a class="name" href="/p/mezcal-amaras/102">Mezcal Amarás Espadín Joven 750 ml</a>
          <span class="price">$480.00</span>
        </div>
      </body>
    </html>
    """
    prods = parsear_html_con_bs4(html, "https://www.sams.com.mx/c/licores", "Sam's Club")
    assert len(prods) == 2

    herradura = next(p for p in prods if "Herradura" in p["producto"])
    assert herradura["precio_regular"] == 799.0
    assert herradura["precio_promo"] == 647.56
    assert herradura["condiciones"] == "Descuento en línea"
    assert herradura["url"] == "https://www.sams.com.mx/p/tequila-herradura-ultra/101"

    amaras = next(p for p in prods if "Amarás" in p["producto"])
    assert amaras["precio_regular"] == 480.0
    assert amaras["precio_promo"] == 480.0
    assert amaras["condiciones"] == "Precio regular de catálogo"


def test_parsear_html_sin_productos():
    """Valida que un HTML sin elementos relevantes devuelva lista vacía."""
    html = "<html><body><div>Página de error 404 o sin stock</div></body></html>"
    prods = parsear_html_con_bs4(html, "https://www.sams.com.mx/vacio", "Sam's Club")
    assert prods == []


# ---------------------------------------------------------------------------
# 4. Pruebas de detección de retos WAF / CAPTCHA (detectar_desafio)
# ---------------------------------------------------------------------------


class MockWebElement:
    def __init__(self, visible: bool = True, text: str = ""):
        self.visible = visible
        self.text = text

    def is_displayed(self) -> bool:
        return self.visible


def test_detectar_desafio_por_titulo():
    """Valida la detección de desafíos basados en palabras clave del título."""
    driver = MagicMock()
    driver.title = "Verifica tu identidad | Walmart México"
    driver.page_source = "<html></html>"
    driver.find_elements.return_value = []

    hay, motivo = detectar_desafio(driver)
    assert hay is True
    assert "Verifica tu identidad" in motivo


def test_detectar_desafio_por_elemento_px_captcha():
    """Valida la detección de desafíos por presencia de elemento #px-captcha activo."""
    driver = MagicMock()
    driver.title = "Catálogo de Bebidas"
    driver.page_source = "<html></html>"

    def mock_find_elements(by, value):
        if value == "px-captcha":
            return [MockWebElement(visible=True)]
        return []

    driver.find_elements.side_effect = mock_find_elements

    hay, motivo = detectar_desafio(driver)
    assert hay is True
    assert "#px-captcha" in motivo


def test_detectar_desafio_por_topmessage_o_cloudflare():
    """Valida la detección de desafíos por #topmessage o #challenge-running."""
    driver = MagicMock()
    driver.title = "Catálogo de Bebidas"
    driver.page_source = "<html></html>"

    def mock_find_elements(by, value):
        if value == "challenge-running":
            return [MockWebElement(visible=True)]
        return []

    driver.find_elements.side_effect = mock_find_elements

    hay, motivo = detectar_desafio(driver)
    assert hay is True
    assert "#challenge-running" in motivo


def test_detectar_desafio_por_cuerpo_html():
    """Valida la detección si el código fuente contiene texto de PerimeterX."""
    driver = MagicMock()
    driver.title = "Página de inicio"
    driver.find_elements.return_value = []
    driver.page_source = "<html><body>px-captcha: mantén presionado el botón para continuar</body></html>"

    hay, motivo = detectar_desafio(driver)
    assert hay is True
    assert "PerimeterX en código fuente" in motivo


def test_detectar_desafio_pagina_limpia():
    """Valida que una página sin bloqueos devuelva (False, '')."""
    driver = MagicMock()
    driver.title = "Tequilas y Licores | Sam's Club"
    driver.find_elements.return_value = []
    driver.page_source = "<html><body>Catálogo de compras normales</body></html>"

    hay, motivo = detectar_desafio(driver)
    assert hay is False
    assert motivo == ""


def test_detectar_desafio_con_excepcion_webdriver():
    """Valida que excepciones de WebDriver en el chequeo se capturen limpiamente."""
    driver = MagicMock()
    driver.find_elements.side_effect = WebDriverException("Conexión perdida con ChromeDriver")
    driver.title = "Test"
    driver.page_source = "<html></html>"

    hay, motivo = detectar_desafio(driver)
    assert hay is False
    assert motivo == ""


# ---------------------------------------------------------------------------
# 5. Pruebas de pausas y verificación interactiva
# ---------------------------------------------------------------------------


def test_pausa_humana():
    """Valida que pausa_humana invoque time.sleep en el rango configurado."""
    with patch("time.sleep") as mock_sleep:
        pausa_humana(1.0, 2.0)
        assert mock_sleep.called
        args, _ = mock_sleep.call_args
        assert 1.0 <= args[0] <= 2.0


def test_verificar_y_esperar_desafio_sin_desafio():
    """Valida que si no hay desafío, verificar_y_esperar_desafio retorne True de inmediato."""
    driver = MagicMock()
    with patch("src.scraper_selenium.detectar_desafio", return_value=(False, "")):
        res = verificar_y_esperar_desafio(driver, timeout_humano=5)
        assert res is True


def test_verificar_y_esperar_desafio_resuelto():
    """Valida que si hay desafío y se resuelve antes del timeout, retorne True."""
    driver = MagicMock()
    # Primera detección: hay desafío; Segunda detección: resuelto
    with patch("src.scraper_selenium.detectar_desafio", side_effect=[(True, "px-captcha"), (False, "")]):
        with patch("time.sleep"):
            res = verificar_y_esperar_desafio(driver, timeout_humano=10)
            assert res is True


# ---------------------------------------------------------------------------
# 6. Pruebas de inicialización de driver y fallback
# ---------------------------------------------------------------------------


def test_inicializar_driver_chrome_exitoso():
    """Valida que inicializar_driver configure ChromeOptions y flags antibot."""
    mock_driver_instance = MagicMock()
    with patch("selenium.webdriver.Chrome", return_value=mock_driver_instance) as mock_chrome:
        driver = inicializar_driver(headless=True, navegador="chrome")
        assert driver == mock_driver_instance
        assert mock_chrome.called
        assert mock_driver_instance.execute_cdp_cmd.called
        assert mock_driver_instance.set_page_load_timeout.called


def test_inicializar_driver_chrome_falla_fallback_firefox():
    """Valida el fallback automático a Firefox cuando Chrome no puede iniciarse."""
    mock_firefox_instance = MagicMock()
    with patch("selenium.webdriver.Chrome", side_effect=WebDriverException("Chrome no encontrado")):
        with patch("selenium.webdriver.Firefox", return_value=mock_firefox_instance) as mock_firefox:
            driver = inicializar_driver(headless=True, navegador="chrome")
            assert driver == mock_firefox_instance
            assert mock_firefox.called


# ---------------------------------------------------------------------------
# 7. Pruebas de orquestación de URLs secuenciales (consultar_urls_secuenciales)
# ---------------------------------------------------------------------------


def test_consultar_urls_secuenciales_mock():
    """Valida el ciclo de consulta, parseo, registro de éxitos y cierre limpio del navegador."""
    mock_driver = MagicMock()
    mock_driver.page_source = """
    <html><body>
      <div data-testid="product-card">
        <a href="/p/tequila-1800/1">Tequila 1800 Añejo 700 ml</a>
        <div class="price">$650.00</div>
      </div>
    </body></html>
    """
    with patch("src.scraper_selenium.inicializar_driver", return_value=mock_driver):
        with patch("src.scraper_selenium.verificar_y_esperar_desafio", return_value=True):
            with patch("src.scraper_selenium.pausa_humana"):
                with patch("time.sleep"):
                    resultados = consultar_urls_secuenciales(
                        urls=["https://www.sams.com.mx/c/tequilas"],
                        tienda="Sam's Club",
                        headless=True,
                    )
                    assert len(resultados) == 1
                    assert resultados[0]["producto"] == "Tequila 1800 Añejo 700 ml"
                    assert mock_driver.quit.called
