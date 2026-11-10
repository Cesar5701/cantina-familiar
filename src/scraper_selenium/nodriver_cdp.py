"""
Módulo de Automatización Indetectable mediante CDP Nativo (nodriver).
Ruta C: Permite la interacción directa con páginas protegidas por PerimeterX
sin binario chromedriver ni variables globales cdc_*.
"""

import asyncio
import glob
import json
import os
import random
import shutil
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from src.clasificacion import limpiar_precio
from src.logger import get_logger

logger = get_logger("nodriver_cdp")

try:
    import nodriver as uc
except (ImportError, OSError):
    uc = None


class BloqueoWAF(Exception):
    """Excepción alzada cuando el WAF (PerimeterX, Cloudflare, Akamai) bloquea la navegación."""

    pass


def es_url_tienda_valida(url: str, base_domain: str = "www.walmart.com.mx") -> bool:
    """Valida que una URL pertenezca al dominio seguro de la tienda y use HTTPS (anti-SSRF)."""
    try:
        parsed = urlparse(url)
        return parsed.scheme == "https" and bool(parsed.hostname) and parsed.hostname.lower() == base_domain.lower()
    except (ValueError, AttributeError):
        return False


def obtener_binario_chrome_disponible() -> Optional[str]:
    """
    Localiza un ejecutable de Google Chrome o Chromium en el sistema o en cachés conocidas.
    Permite anular la ruta mediante la variable de entorno CHROME_BIN.
    """
    env_bin = os.environ.get("CHROME_BIN")
    if env_bin and os.path.isfile(env_bin) and os.access(env_bin, os.X_OK):
        return env_bin

    # 1. Búsqueda en PATH del sistema
    for cmd in ["google-chrome", "google-chrome-stable", "chromium-browser", "chromium"]:
        ruta = shutil.which(cmd)
        if ruta and os.access(ruta, os.X_OK):
            return ruta

    # 2. Búsqueda dinámica en caché de selenium (~/.cache/selenium/chrome/linux64/*/chrome)
    patron_selenium = os.path.expanduser("~/.cache/selenium/chrome/linux64/*/chrome")
    coincidencias = sorted(glob.glob(patron_selenium), reverse=True)
    for c in coincidencias:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c

    # 3. Búsqueda dinámica en caché de playwright
    patron_playwright = os.path.expanduser("~/.cache/ms-playwright/chromium-*/chrome-linux64/chrome")
    coincidencias_pw = sorted(glob.glob(patron_playwright), reverse=True)
    for c in coincidencias_pw:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c

    # 4. Rutas fijas estándar
    rutas_candidatas = [
        "/usr/bin/google-chrome-stable",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
    ]
    for r in rutas_candidatas:
        if os.path.isfile(r) and os.access(r, os.X_OK):
            return r
    return None


async def _procesar_pdp_tab(
    browser: Any,
    url: str,
    idx: int,
    total: int,
    semaphore: asyncio.Semaphore,
    delay_min: float,
    delay_max: float,
    tienda: str = "Walmart",
    base_domain: str = "www.walmart.com.mx",
    timeout_tab: float = 20.0,
    event_abort: Optional[asyncio.Event] = None,
) -> Optional[Dict[str, Any]]:
    """
    Procesa una PDP individual en su propia pestaña concurrente, gobernado por un semáforo,
    timeout estricto por pestaña y aborto temprano ante desafío WAF.
    """
    if event_abort is not None and event_abort.is_set():
        logger.info(f"Omitiendo PDP [{idx}/{total}]: sesión abortada previamente por bloqueo WAF.")
        return None

    async with semaphore:
        if event_abort is not None and event_abort.is_set():
            return None

        if not es_url_tienda_valida(url, base_domain):
            logger.warning(f"URL de PDP rechazada por seguridad (no coincide con https://{base_domain}): {url}")
            return None

        tab = None
        try:
            logger.info(f"[{idx}/{total}] Consultando PDP con nodriver: {url}")
            tab = await asyncio.wait_for(browser.get(url, new_tab=True), timeout=timeout_tab)
            pausa = random.uniform(delay_min, delay_max)
            await tab.sleep(pausa)

            content = await asyncio.wait_for(tab.get_content(), timeout=timeout_tab)
            if not content:
                logger.warning(f"  Respuesta vacía en {url}")
                return None

            if "__NEXT_DATA__" not in content:
                tab_url = getattr(tab, "url", "")
                if "/blocked" in tab_url or "verifica tu identidad" in content.lower():
                    logger.warning(f"  [Desafío PX] Bloqueo detectado en {url}. Activando aborto de sesión.")
                    if event_abort is not None:
                        event_abort.set()
                    raise BloqueoWAF(f"Bloqueo PerimeterX detectado en {url}")
                else:
                    logger.warning(f"  Sin __NEXT_DATA__ en {url}")
                return None

            soup = BeautifulSoup(content, "html.parser")
            script = soup.find("script", id="__NEXT_DATA__")
            if not script or not script.string:
                return None

            data = json.loads(script.string)
            prod = data.get("props", {}).get("pageProps", {}).get("initialData", {}).get("data", {}).get("product", {})
            if not prod:
                return None

            nombre = prod.get("name") or ""
            brand = prod.get("brand") or ""
            disp = prod.get("availabilityStatus") or "UNKNOWN"
            disp_norm = "disponible" if disp in {"IN_STOCK", "AVAILABLE"} else "agotado"

            price_info = prod.get("priceInfo") or {}
            cur_obj = price_info.get("currentPrice") or {}
            was_obj = price_info.get("wasPrice") or {}
            list_obj = price_info.get("listPrice") or {}

            current_p = cur_obj.get("price") or cur_obj.get("priceDisplay") or list_obj.get("price")
            was_p = was_obj.get("price") or was_obj.get("priceString") or list_obj.get("price")

            p_promo = limpiar_precio(current_p)
            p_reg = limpiar_precio(was_p) or p_promo

            item_raw = {
                "producto": nombre,
                "marca": brand,
                "precio_promo": p_promo,
                "precio_regular": p_reg,
                "disponibilidad": disp_norm,
                "url": url,
                "condiciones": f"Portal oficial {tienda} (nodriver CDP)",
                "fuente": f"{tienda} (nodriver CDP)",
            }
            logger.info(f"  ✓ Extraído: {nombre} | Promo: ${p_promo} | Reg: ${p_reg} | Disp: {disp_norm}")
            return item_raw

        except asyncio.TimeoutError:
            logger.warning(f"  Timeout ({timeout_tab}s) esperando respuesta de PDP en {url}")
            return None
        except BloqueoWAF:
            raise
        except (json.JSONDecodeError, KeyError, ValueError, OSError, RuntimeError) as e:
            logger.warning(f"  Error procesando {url}: {e}")
            return None
        finally:
            if tab:
                try:
                    await tab.close()
                except (OSError, RuntimeError, TimeoutError, ValueError, AttributeError) as err_tab:
                    logger.debug(f"Aviso al cerrar pestaña nodriver: {err_tab}")


async def _extraer_datos_pdp_async(
    urls: List[str],
    headless: bool = False,
    delay_min: float = 2.5,
    delay_max: float = 4.0,
    concurrencia: int = 3,
    tienda: str = "Walmart",
    base_domain: str = "www.walmart.com.mx",
    timeout_tab: float = 20.0,
) -> List[Dict[str, Any]]:
    """
    Navega concurrentemente por una lista de páginas de producto (PDP) con control de semáforo,
    timeout por pestaña, aborto temprano ante WAF y calentamiento de sesión en la página de inicio.
    """
    if uc is None:
        logger.warning("nodriver no está disponible en este entorno.")
        return []

    chrome_bin = obtener_binario_chrome_disponible()
    if not chrome_bin:
        logger.warning("No se localizó un binario ejecutable de Chrome para nodriver.")
        return []

    logger.info(
        f"Iniciando navegador CDP nodriver (binario: {chrome_bin}, headless: {headless}, workers: {concurrencia})..."
    )
    # Solo agregar --no-sandbox si corre dentro de contenedores o si está explícitamente configurado
    args_navegador = ["--disable-dev-shm-usage"]
    if os.environ.get("DOCKER_CONTAINER") or os.environ.get("CI") or os.path.exists("/.dockerenv"):
        args_navegador.append("--no-sandbox")

    browser = await uc.start(
        browser_executable_path=chrome_bin,
        headless=headless,
        browser_args=args_navegador,
    )

    resultados: List[Dict[str, Any]] = []
    event_abort = asyncio.Event()

    try:
        # Calentar sesión en la página principal correspondiente para establecer contexto residencial orgánico
        url_home = f"https://{base_domain}"
        logger.info(f"Estableciendo sesión orgánica en {tienda} ({url_home})...")
        home_tab = await asyncio.wait_for(browser.get(url_home), timeout=timeout_tab)
        await home_tab.sleep(random.uniform(2.5, 3.5))

        sem = asyncio.Semaphore(concurrencia)
        total = len(urls)
        tasks = [
            _procesar_pdp_tab(
                browser=browser,
                url=url,
                idx=i,
                total=total,
                semaphore=sem,
                delay_min=delay_min,
                delay_max=delay_max,
                tienda=tienda,
                base_domain=base_domain,
                timeout_tab=timeout_tab,
                event_abort=event_abort,
            )
            for i, url in enumerate(urls, 1)
        ]

        respuestas = await asyncio.gather(*tasks, return_exceptions=True)
        for r in respuestas:
            if isinstance(r, dict):
                resultados.append(r)
            elif isinstance(r, BloqueoWAF):
                logger.warning(f"Aborto temprano por bloqueo WAF en nodriver: {r}")
            elif isinstance(r, Exception):
                logger.warning(f"Excepción en tarea concurrente de PDP: {r}")

    finally:
        try:
            browser.stop()
            logger.info("Navegador nodriver detenido.")
        except (OSError, RuntimeError, TimeoutError, ValueError, AttributeError) as e:
            logger.debug(f"Error deteniendo navegador nodriver: {e}")

    return resultados


def consultar_pdps_con_nodriver(
    urls: List[str],
    headless: bool = False,
    delay_min: float = 2.5,
    delay_max: float = 4.0,
    concurrencia: int = 3,
    tienda: str = "Walmart",
    base_domain: str = "www.walmart.com.mx",
    timeout_tab: float = 20.0,
) -> List[Dict[str, Any]]:
    """
    Función sincrónica para consultar URLs de productos (PDPs) mediante nodriver con concurrencia.
    """
    return asyncio.run(
        _extraer_datos_pdp_async(
            urls=urls,
            headless=headless,
            delay_min=delay_min,
            delay_max=delay_max,
            concurrencia=concurrencia,
            tienda=tienda,
            base_domain=base_domain,
            timeout_tab=timeout_tab,
        )
    )
