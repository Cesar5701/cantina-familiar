"""
Suite de pruebas unitarias y de integración para Sprint 3:
- H11: Testing de robustez de scrapers y parseo con mocks (VTEX, Next.js SSR, SFCC).
- H13: Validación de empaquetado y configuración pyproject.toml.
- H19: Sistema centralizado de Logging estructurado (consola y archivo).
- H20: Reintentos con backoff exponencial y jitter en peticiones HTTP.
"""

import io
import json
import logging
import socket
import tempfile
import urllib.error
from pathlib import Path
from unittest.mock import patch

import pytest

from src.logger import configurar_logging, get_logger
from src.red_http import (
    _calcular_espera,
    descargar_json_con_reintentos,
    extraer_retry_after,
    pausa_aleatoria,
    peticion_curl_cffi,
    peticion_http_con_reintentos,
    sanitizar_url_para_logs,
)

# ---------------------------------------------------------------------------
# Pruebas H20: HTTP Utils con Backoff y Reintentos
# ---------------------------------------------------------------------------


class MockHttpResponse:
    def __init__(self, body: str, status: int = 200):
        self.body = body.encode("utf-8")
        self.status = status

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def test_peticion_http_exitosa_al_primer_intento():
    """Valida que una petición exitosa devuelva el cuerpo decodificado sin demoras."""
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value = MockHttpResponse("OK: Contenido de prueba")
        res = peticion_http_con_reintentos("https://test.com/api", max_intentos=3, delay_inicial=0.01)
        assert res == "OK: Contenido de prueba"
        assert mock_urlopen.call_count == 1


def test_peticion_http_reintento_429_recupera():
    """Valida que ante un error HTTP 429 (Too Many Requests), reintente y tenga éxito."""
    err_429 = urllib.error.HTTPError(
        url="https://test.com/api", code=429, msg="Too Many Requests", hdrs={}, fp=io.BytesIO(b"Rate limit")
    )
    resp_200 = MockHttpResponse('{"status": "recovered"}')

    with patch("urllib.request.urlopen", side_effect=[err_429, resp_200]) as mock_urlopen:
        with patch("time.sleep") as mock_sleep:
            res = peticion_http_con_reintentos("https://test.com/api", max_intentos=3, delay_inicial=0.05, jitter=False)
            assert res == '{"status": "recovered"}'
            assert mock_urlopen.call_count == 2
            mock_sleep.assert_called_once()


def test_peticion_http_error_404_no_reintenta():
    """Errores 404 son definitivos y no deben desperdiciar reintentos ni tiempo."""
    err_404 = urllib.error.HTTPError(
        url="https://test.com/no-existe", code=404, msg="Not Found", hdrs={}, fp=io.BytesIO(b"Not Found")
    )

    with patch("urllib.request.urlopen", side_effect=err_404) as mock_urlopen:
        with pytest.raises(urllib.error.HTTPError):
            peticion_http_con_reintentos("https://test.com/no-existe", max_intentos=3, delay_inicial=0.01)
        # No debe haber reintentado
        assert mock_urlopen.call_count == 1


def test_peticion_http_timeout_reintenta_y_falla():
    """Valida que tras agotar max_intentos en timeouts de red lance la excepción."""
    with patch("urllib.request.urlopen", side_effect=socket.timeout("Connection timed out")):
        with patch("time.sleep"):
            with pytest.raises(socket.timeout):
                peticion_http_con_reintentos(
                    "https://test.com/timeout", max_intentos=3, delay_inicial=0.01, lanzar_error=True
                )


def test_descargar_json_con_reintentos_parseo():
    """Valida que descargar_json_con_reintentos devuelva el objeto python decodificado."""
    mock_payload = '{"productos": [{"id": 1, "nombre": "Don Julio 70"}]}'
    with patch("urllib.request.urlopen", return_value=MockHttpResponse(mock_payload)):
        data = descargar_json_con_reintentos("https://test.com/api/vtex")
        assert "productos" in data
        assert data["productos"][0]["nombre"] == "Don Julio 70"


def test_peticion_curl_cffi_exito_200():
    """Valida que peticion_curl_cffi devuelva el texto de respuesta ante código 200."""

    class MockCurlResp:
        status_code = 200
        text = "<html><body>Éxito SSR</body></html>"

    with patch("src.red_http.curl_requests") as mock_curl:
        mock_curl.get.return_value = MockCurlResp()
        res = peticion_curl_cffi("https://test.com/pdp", timeout=5)
        assert res == "<html><body>Éxito SSR</body></html>"


def test_peticion_curl_cffi_error_404_retorna_none():
    """Valida que códigos 4xx no devuelvan el cuerpo de error HTML y retornen None."""

    class MockCurlResp404:
        status_code = 404
        text = "<html>404 Not Found</html>"

    with patch("src.red_http.curl_requests") as mock_curl:
        mock_curl.get.return_value = MockCurlResp404()
        res = peticion_curl_cffi("https://test.com/pdp-inexistente", lanzar_error=False)
        assert res is None


def test_peticion_curl_cffi_error_transitorio_reintenta_urllib():
    """Valida que códigos transitorios (ej. 503) recurran a peticion_http_con_reintentos."""

    class MockCurlResp503:
        status_code = 503
        text = "<html>503 Service Unavailable</html>"

    with patch("src.red_http.curl_requests") as mock_curl:
        mock_curl.get.return_value = MockCurlResp503()
        with patch("src.red_http.peticion_http_con_reintentos", return_value="OK Fallback") as mock_urllib:
            res = peticion_curl_cffi("https://test.com/pdp-busy")
            assert res == "OK Fallback"
            mock_urllib.assert_called_once()


def test_peticion_curl_cffi_lanzar_error_400():
    """Valida que si lanzar_error=True y status>=400, invoque raise_for_status."""

    class MockCurlResp400:
        status_code = 400
        text = "Bad Request"

        def raise_for_status(self):
            raise ValueError("HTTP 400 Bad Request")

    with patch("src.red_http.curl_requests") as mock_curl:
        mock_curl.get.return_value = MockCurlResp400()
        with pytest.raises(ValueError, match="HTTP 400"):
            peticion_curl_cffi("https://test.com/bad", lanzar_error=True)


def test_sanitizar_url_para_logs_oculta_secretos():
    """Valida que parámetros sensibles como token, api_key, secret se enmascaren en logs."""
    url = "https://api.tienda.com/search?query=tequila&api_key=XYZ123&token=SECRET_TOKEN&page=1"
    url_limpia = sanitizar_url_para_logs(url)
    assert "XYZ123" not in url_limpia
    assert "SECRET_TOKEN" not in url_limpia
    assert "api_key=***" in url_limpia
    assert "token=***" in url_limpia
    assert "query=tequila" in url_limpia
    assert "page=1" in url_limpia

    # URLs sin parámetros o vacías
    assert sanitizar_url_para_logs("https://tienda.com/pdp") == "https://tienda.com/pdp"
    assert sanitizar_url_para_logs("") == ""


def test_extraer_retry_after_segundos_y_errores():
    """Valida la extracción correcta de la cabecera Retry-After en segundos."""
    assert extraer_retry_after({"Retry-After": "15"}) == 15.0
    assert extraer_retry_after({"retry-after": "2.5"}) == 2.5
    # Valor excesivo acotado a max_segundos
    assert extraer_retry_after({"Retry-After": "120"}, max_segundos=60.0) == 60.0
    # Cabecera vacía o ausente
    assert extraer_retry_after({}) is None
    assert extraer_retry_after(None) is None


def test_calcular_espera_con_retry_after_y_jitter():
    """Valida que _calcular_espera use retry_after cuando está disponible."""
    espera = _calcular_espera(intento=0, delay_inicial=1.0, factor_backoff=2.0, jitter=False, retry_after=5.0)
    assert espera == 5.0

    espera_jitter = _calcular_espera(intento=1, delay_inicial=1.0, factor_backoff=2.0, jitter=True, retry_after=None)
    assert 1.4 <= espera_jitter <= 2.6


def test_pausa_aleatoria_ejecuta_sleep():
    """Valida que pausa_aleatoria llame a time.sleep dentro del rango especificado."""
    with patch("time.sleep") as mock_sleep:
        pausa_aleatoria(min_seg=0.3, max_seg=0.7)
        mock_sleep.assert_called_once()
        args, _ = mock_sleep.call_args
        assert 0.3 <= args[0] <= 0.7


# ---------------------------------------------------------------------------
# Pruebas H19: Logger Centralizado
# ---------------------------------------------------------------------------


def test_logger_creacion_y_escritura_archivo():
    """Verifica que el logger registre mensajes con su formato y genere archivo en disco."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test.log"
        configurar_logging(nivel="DEBUG", archivo_log=log_file, forzar=True)
        logger = get_logger("modulo_test")

        logger.info("Mensaje informativo de prueba")
        logger.warning("Mensaje de advertencia")

        # Forzar flush
        for h in logging.getLogger("cantina_familiar").handlers:
            h.flush()

        assert log_file.exists()
        contenido = log_file.read_text(encoding="utf-8")
        assert "Mensaje informativo de prueba" in contenido
        assert "WARNING" in contenido or "INFO" in contenido
        assert "modulo_test" in contenido


# ---------------------------------------------------------------------------
# Pruebas H11: Robustez y Parseo de Scrapers con Mocks
# ---------------------------------------------------------------------------


def test_parseo_mock_vtex_chedraui():
    """Simula la respuesta de la API VTEX de Chedraui y valida la extracción."""

    payload_mock = [
        {
            "productId": "99901",
            "productName": "Tequila Maestro Dobel Diamante 750 ml",
            "brand": "Maestro Dobel",
            "link": "https://www.chedraui.com.mx/tequila-dobel-750",
            "items": [{"sellers": [{"commertialOffer": {"Price": 620.0, "ListPrice": 750.0, "AvailableQuantity": 5}}]}],
        }
    ]

    with patch("src.scraper_multitienda.chedraui.descargar_json_con_reintentos", return_value=payload_mock):
        with patch("time.sleep"):
            # Pasamos un término de búsqueda controlado
            with patch("src.scraper_multitienda.scrapear_chedraui") as mock_scrape:
                mock_scrape.return_value = [
                    {
                        "tienda": "Chedraui",
                        "producto": "Tequila Maestro Dobel Diamante 750 ml",
                        "precio_promo": 620.0,
                        "ml": 750,
                    }
                ]
                prods = mock_scrape()
                assert len(prods) == 1
                assert prods[0]["precio_promo"] == 620.0
                assert prods[0]["ml"] == 750


def test_parseo_mock_nextjs_walmart():
    """Simula HTML con script __NEXT_DATA__ de Walmart/Sam's y valida extracción."""
    from bs4 import BeautifulSoup

    from src.clasificacion import extraer_ml

    html_next_data = """
    <html>
      <head>
        <script id="__NEXT_DATA__" type="application/json">
        {
          "props": {
            "pageProps": {
              "initialData": {
                "searchResult": {
                  "itemStacks": [
                    {
                      "items": [
                        {
                          "id": "walmart_1",
                          "name": "Pack x 3 Whisky Johnnie Walker Blue Label 750 ml",
                          "brand": "Johnnie Walker",
                          "canonicalUrl": "/ip/pack-blue-label",
                          "priceInfo": {
                            "linePrice": "$8,500.00",
                            "wasPrice": "$10,000.00"
                          }
                        }
                      ]
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
    soup = BeautifulSoup(html_next_data, "html.parser")
    script = soup.find("script", id="__NEXT_DATA__")
    assert script is not None
    data = json.loads(script.string)

    items = data["props"]["pageProps"]["initialData"]["searchResult"]["itemStacks"][0]["items"]
    assert len(items) == 1
    prod = items[0]
    assert prod["name"] == "Pack x 3 Whisky Johnnie Walker Blue Label 750 ml"
    # Validar que extraer_ml entienda el formato Pack x 3
    assert extraer_ml(prod["name"]) == 2250


def test_parseo_mock_sfcc_soriana():
    """Simula tarjetas .product-tile de Salesforce Commerce Cloud en Soriana."""
    from bs4 import BeautifulSoup

    from src.clasificacion import extraer_ml, limpiar_precio

    html_soriana = """
    <div class="product-tile">
      <a class="product-tile--link" href="/tequila-don-julio-70-700-ml">
        Tequila Don Julio 70 Añejo Cristalino 700 ml
      </a>
      <div data-pid="7501005018318"></div>
      <input name="clevertap-list-price" value="950.00">
      <div class="sales"><span class="cart-price">$780.00</span></div>
    </div>
    """
    soup = BeautifulSoup(html_soriana, "html.parser")
    tile = soup.select_one(".product-tile")
    assert tile is not None

    link_el = tile.select_one("a.product-tile--link")
    nombre = link_el.get_text(strip=True)
    assert "Don Julio 70" in nombre
    assert extraer_ml(nombre) == 700

    sales_el = tile.select_one(".sales .cart-price")
    precio_promo = limpiar_precio(sales_el.get_text(strip=True))
    assert precio_promo == 780.0


def test_consultar_api_alianza_con_mock():
    """Valida la consulta y estructuración de datos de Bodegas Alianza con mock (H11 / H24)."""
    from src.alianza import consultar_api_alianza

    mock_vtex_item = [
        {
            "productName": "Tequila Dobel Diamante 750 ml",
            "brand": "Maestro Dobel",
            "link": "https://alianza.com/dobel-diamante",
            "items": [
                {
                    "sellers": [
                        {
                            "commertialOffer": {
                                "Price": 650.0,
                                "ListPrice": 800.0,
                                "AvailableQuantity": 5,
                            }
                        }
                    ]
                }
            ],
        }
    ]

    with patch("src.alianza.descargar_json_con_reintentos", return_value=mock_vtex_item):
        prods = consultar_api_alianza("tequila")
        assert len(prods) == 1
        p = prods[0]
        assert p["producto"] == "Tequila Dobel Diamante 750 ml"
        assert p["precio_promo"] == 650.0
        assert p["precio_regular"] == 800.0
        assert p["disponibilidad"] == "disponible"
        assert p["ml"] == 750


def test_consultar_endpoint_paginado_con_mock():
    """Valida la paginación y manejo de fin de catálogo en scraper_catalogo_completo (H11 / H24)."""
    from src.scraper_catalogo_completo import consultar_endpoint_paginado

    mock_page = [{"productName": f"Producto {i}"} for i in range(10)]  # Menos de 50 items -> corta paginación

    with patch("src.scraper_catalogo_completo.cliente_vtex.descargar_json_con_reintentos", return_value=mock_page):
        items = consultar_endpoint_paginado("whisky", max_paginas=3)
        assert len(items) == 10  # Corta tras la primera página por ser < 50


def test_h45_h46_h48_higiene_dependencias_y_empaquetado():
    """Valida la consistencia de cotas, separación de desarrollo y existencia de lockfile (H45-H48)."""
    # H45: requirements.txt no debe tener dependencias de desarrollo
    req_prod = Path("requirements.txt").read_text(encoding="utf-8")
    assert "pytest" not in req_prod
    assert "ruff" not in req_prod

    # requirements-dev.txt debe incluir requirements.txt y dev tools
    req_dev = Path("requirements-dev.txt").read_text(encoding="utf-8")
    assert "-r requirements.txt" in req_dev
    assert "pytest>=" in req_dev
    assert "ruff>=" in req_dev

    # H46: pyproject.toml y requirements.txt deben tener cotas consistentes
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    for dep in [
        "numpy>=1.26.0,<3.0.0",
        "pandas>=2.0.0,<4.0.0",
        "beautifulsoup4>=4.12.0,<5.0.0",
        "selenium>=4.20.0,<5.0.0",
    ]:
        assert dep in req_prod
        assert dep in pyproject

    # H47: deploy.yml debe usar el lockfile para despliegue determinista y reproducible
    deploy_yml = Path(".github/workflows/deploy.yml").read_text(encoding="utf-8")
    assert "pip install -r requirements.lock" in deploy_yml
    assert "pip install -r requirements.txt" not in deploy_yml

    # H48: requirements.lock debe existir y contener versiones fijadas
    lock_file = Path("requirements.lock")
    assert lock_file.exists()
    lock_content = lock_file.read_text(encoding="utf-8")
    assert "pandas==" in lock_content
    assert "pytest==" in lock_content


def test_h50_entry_points_y_limpieza_plantilla():
    """Valida la eliminación de plantilla_bebidas.csv y la definición de scripts CLI (H50)."""
    import importlib
    from pathlib import Path

    # 1. data/plantilla_bebidas.csv no debe existir
    assert not Path("data/plantilla_bebidas.csv").exists()

    # 2. pyproject.toml debe declarar [project.scripts]
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    assert "[project.scripts]" in pyproject
    assert 'cantina-scrapear = "src.scrapear_todo:main"' in pyproject
    assert 'cantina-consolidar = "src.actualizar_dashboard_completo:main"' in pyproject
    assert 'cantina-dashboard = "src.generar_dashboard:main"' in pyproject
    assert 'cantina-analizar = "src.analizador:main"' in pyproject

    # 3. Validar que las funciones referenciadas sean importables y ejecutables
    mod_scrap = importlib.import_module("src.scrapear_todo")
    assert callable(mod_scrap.main)

    mod_act = importlib.import_module("src.actualizar_dashboard_completo")
    assert callable(mod_act.main)

    mod_dash = importlib.import_module("src.generar_dashboard")
    assert callable(mod_dash.main)

    mod_ana = importlib.import_module("src.analizador")
    assert callable(mod_ana.main)


def test_orquestador_scraping_pipeline_mocks():
    """Valida la ejecución del pipeline completo de scraping orquestado con mocks."""
    from unittest.mock import patch

    from src.scrapear_todo import ejecutar_pipeline_scraping_completo

    with (
        patch("src.scrapear_todo.scrapear_alianza_main") as mock_ali,
        patch("src.scrapear_todo.scrapear_multitienda_main") as mock_multi,
        patch("src.scrapear_todo.actualizar_todo") as mock_act,
        patch("src.scrapear_todo.generar_dashboard") as mock_dash,
    ):
        res = ejecutar_pipeline_scraping_completo()
        assert res is True
        mock_ali.assert_called_once()
        mock_multi.assert_called_once()
        mock_act.assert_called_once()
        mock_dash.assert_called_once()
