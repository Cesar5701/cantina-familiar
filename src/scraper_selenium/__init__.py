"""
Paquete Scraper automatizado con Selenium y BeautifulSoup para páginas dinámicas (SPA).
"""

from selenium import webdriver
from selenium.common.exceptions import (
    JavascriptException,
    NoSuchElementException,
    SessionNotCreatedException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions

from src.scraper_selenium.driver_y_waf import (
    INDICADORES_CHALLENGE,
    detectar_desafio,
    inicializar_driver,
    pausa_humana,
    verificar_y_esperar_desafio,
)
from src.scraper_selenium.navegador_cli import consultar_urls_secuenciales, main
from src.scraper_selenium.parsers_dom import (
    _construir_registro_producto,
    extraer_de_json_embebido,
    parsear_html_con_bs4,
)

__all__ = [
    "By",
    "ChromeOptions",
    "FirefoxOptions",
    "INDICADORES_CHALLENGE",
    "JavascriptException",
    "NoSuchElementException",
    "SessionNotCreatedException",
    "TimeoutException",
    "WebDriverException",
    "_construir_registro_producto",
    "consultar_urls_secuenciales",
    "detectar_desafio",
    "extraer_de_json_embebido",
    "inicializar_driver",
    "main",
    "parsear_html_con_bs4",
    "pausa_humana",
    "verificar_y_esperar_desafio",
    "webdriver",
]
