"""
Inicialización de WebDriver (Chrome/Firefox), pausas humanas y detección/resolución de desafíos WAF/CAPTCHA.
"""

import os
import random
import time

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    SessionNotCreatedException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions

from src.infraestructura.cliente_http import INDICADORES_DESAFIO_WAF, USER_AGENT_CHROME
from src.infraestructura.registro_eventos import get_logger

logger = get_logger("controlador_waf")

INDICADORES_CHALLENGE: list[str] = list(INDICADORES_DESAFIO_WAF)


def _buscar_par_chrome_cache() -> tuple[str | None, str | None]:
    """Busca un par de versión coincidente entre Chrome y ChromeDriver en ~/.cache/selenium."""
    cache_base = os.path.expanduser("~/.cache/selenium")
    chrome_dir = os.path.join(cache_base, "chrome", "linux64")
    driver_dir = os.path.join(cache_base, "chromedriver", "linux64")
    if not (os.path.isdir(chrome_dir) and os.path.isdir(driver_dir)):
        return None, None
    try:
        for ver in sorted(os.listdir(chrome_dir), reverse=True):
            bin_chrome = os.path.join(chrome_dir, ver, "chrome")
            bin_driver = os.path.join(driver_dir, ver, "chromedriver")
            if os.path.isfile(bin_chrome) and os.path.isfile(bin_driver):
                return bin_chrome, bin_driver
    except OSError as err:
        logger.debug(f"Error explorando caché de Selenium: {err}")
    return None, None


def _aplicar_stealth_chrome(driver: webdriver.Remote) -> None:
    """Oculta la propiedad navigator.webdriver mediante Chrome DevTools Protocol."""
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """
        },
    )


def inicializar_driver(
    headless: bool = False,
    navegador: str = "chrome",
    user_data_dir: str | None = None,
) -> webdriver.Remote:
    """Inicializa Selenium en Chrome (o Firefox) con User-Agent y banderas de navegador real."""
    dir_perfil = user_data_dir or os.environ.get("CHROME_USER_DATA_DIR")
    if navegador.lower() == "chrome":
        options = ChromeOptions()
        if dir_perfil:
            options.add_argument(f"--user-data-dir={dir_perfil}")
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--start-maximized")
        options.add_argument(f"user-agent={USER_AGENT_CHROME}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        try:
            driver = webdriver.Chrome(options=options)
            _aplicar_stealth_chrome(driver)
        except (WebDriverException, SessionNotCreatedException, FileNotFoundError, OSError) as e:
            bin_chrome, bin_driver = _buscar_par_chrome_cache()
            if bin_chrome and bin_driver:
                try:
                    options.binary_location = bin_chrome
                    service = ChromeService(executable_path=bin_driver)
                    driver = webdriver.Chrome(service=service, options=options)
                    _aplicar_stealth_chrome(driver)
                    driver.set_page_load_timeout(45)
                    return driver
                except (WebDriverException, SessionNotCreatedException, FileNotFoundError, OSError) as e_sub:
                    logger.debug(f"Fallback con binario de Chrome en caché no tuvo éxito: {e_sub}")
            logger.warning(f"No se pudo iniciar Chrome ({e}). Intentando con Firefox...")
            return inicializar_driver(headless=headless, navegador="firefox")
    else:
        options = FirefoxOptions()
        if headless:
            options.add_argument("-headless")
        options.set_preference("general.useragent.override", USER_AGENT_CHROME)
        options.set_preference("dom.webdriver.enabled", False)
        options.set_preference("useAutomationExtension", False)
        driver = webdriver.Firefox(options=options)

    driver.set_page_load_timeout(45)
    return driver


def pausa_humana(min_seg: float = 2.0, max_seg: float = 4.0):
    """Introduce una pausa aleatoria entre acciones para simular lectura humana."""
    espera = round(random.uniform(min_seg, max_seg), 2)
    time.sleep(espera)


def detectar_desafio(driver: webdriver.Remote) -> tuple[bool, str]:
    """Detecta si hay un desafío WAF/CAPTCHA activo y devuelve (hay_desafio, motivo)."""
    try:
        titulo = (driver.title or "").lower()
        for ind in INDICADORES_CHALLENGE:
            if ind in titulo:
                return True, f"Título de página sospechoso: '{driver.title}'"

        # Verificar presencia de elementos específicos de PerimeterX o Cloudflare
        try:
            px = driver.find_elements(By.ID, "px-captcha")
            if px and any(p.is_displayed() for p in px):
                return True, "Elemento #px-captcha activo en pantalla"
        except (WebDriverException, NoSuchElementException) as e:
            logger.debug(f"Error verificando elemento px-captcha: {e}")

        try:
            top_msg = driver.find_elements(By.ID, "topmessage")
            if top_msg and any("identidad" in m.text.lower() or "identity" in m.text.lower() for m in top_msg):
                return True, "Mensaje de verificación de identidad activo (#topmessage)"
        except (WebDriverException, NoSuchElementException) as e:
            logger.debug(f"Error verificando elemento topmessage: {e}")

        try:
            cf = driver.find_elements(By.ID, "challenge-running")
            if cf and any(c.is_displayed() for c in cf):
                return True, "Desafío Cloudflare activo (#challenge-running)"
        except (WebDriverException, NoSuchElementException) as e:
            logger.debug(f"Error verificando elemento challenge-running: {e}")

        # Búsqueda en los primeros 10KB del código fuente
        html_head = (driver.page_source or "")[:10000].lower()
        if (
            "px-captcha" in html_head or "verifica tu identidad" in html_head or "verify your identity" in html_head
        ) and ("mantén presionado el botón" in html_head or "press and hold" in html_head):
            return True, "Texto de desafío PerimeterX en código fuente"

    except (WebDriverException, NoSuchElementException, TimeoutException) as e:
        logger.debug(f"Error general en detección de desafío: {e}")

    return False, ""


def verificar_y_esperar_desafio(driver: webdriver.Remote, timeout_humano: int = 30) -> bool:
    """
    Detecta si la página fue interceptada por un desafío de seguridad o CAPTCHA (ej. PerimeterX / Cloudflare).
    Pausa el script y emite alerta en terminal para que el usuario lo resuelva manualmente en la ventana abierta.
    Espera hasta `timeout_humano` segundos a que desaparezca el desafío y la página del catálogo cargue.
    """
    hay_desafio, motivo = detectar_desafio(driver)

    if hay_desafio:
        logger.warning("!" * 80)
        logger.warning("[ALERTA: DESAFÍO DE SEGURIDAD / CAPTCHA EN PANTALLA]")
        logger.warning(f"Causa detectada: {motivo}")
        if any(k in motivo.lower() for k in ["px-captcha", "identidad", "identity", "perimeterx"]):
            logger.warning(">> ACCIÓN REQUERIDA: En la ventana de Google Chrome abierta,")
            logger.warning(">> MANTÉN PRESIONADO el botón blanco/gris hasta que la barra se llene")
            logger.warning(">> y la página se recargue.")
        else:
            logger.warning(">> ACCIÓN REQUERIDA: Resuelve la verificación manualmente en la ventana abierta.")
        logger.warning(f"El script pausará hasta {timeout_humano} segundos esperando que la página se desbloquee...")
        logger.warning("!" * 80)

        inicio = time.time()
        ultimo_segundo_reportado = 0
        while time.time() - inicio < timeout_humano:
            time.sleep(1.5)
            sigue_desafio, _ = detectar_desafio(driver)
            transcurrido = int(time.time() - inicio)
            restante = max(0, timeout_humano - transcurrido)

            # Notificar progreso cada 5 segundos
            if transcurrido >= ultimo_segundo_reportado + 5:
                ultimo_segundo_reportado = transcurrido
                logger.info(f"  ... esperando que resuelvas el desafío en Chrome ({restante}s restantes)...")

            if not sigue_desafio:
                logger.info(f"Desafío resuelto por el usuario en {transcurrido}s. Continuando extracción...")
                # Breve pausa para dar tiempo a la redirección o reload de la página
                time.sleep(3.0)
                return True

        logger.warning(f"Tiempo de espera para resolución manual agotado ({timeout_humano}s).")
        return False

    return True
