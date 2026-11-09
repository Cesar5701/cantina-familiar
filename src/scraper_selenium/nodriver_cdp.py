"""
Módulo de Automatización Indetectable mediante CDP Nativo (nodriver).
Ruta C: Permite la interacción directa con páginas protegidas por PerimeterX
sin binario chromedriver ni variables globales cdc_*.
"""

import asyncio
import json
import os
import random
import time
from typing import Any, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup

from src.clasificacion import limpiar_precio
from src.io_utils import ResumenScraping
from src.logger import get_logger

logger = get_logger("nodriver_cdp")

try:
    import nodriver as uc
except (ImportError, OSError):
    uc = None


def obtener_binario_chrome_disponible() -> Optional[str]:
    """
    Localiza un ejecutable de Google Chrome o Chromium en el sistema o en cachés conocidas.
    """
    rutas_candidatas = [
        os.path.expanduser("~/.cache/selenium/chrome/linux64/142.0.7444.175/chrome"),
        os.path.expanduser("~/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome"),
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
) -> Optional[Dict[str, Any]]:
    """
    Procesa una PDP individual en su propia pestaña concurrente, gobernado por un semáforo.
    """
    async with semaphore:
        tab = None
        try:
            logger.info(f"[{idx}/{total}] Consultando PDP con nodriver: {url}")
            tab = await browser.get(url, new_tab=True)
            pausa = random.uniform(delay_min, delay_max)
            await tab.sleep(pausa)

            content = await tab.get_content()
            if not content:
                logger.warning(f"  Respuesta vacía en {url}")
                return None

            if "__NEXT_DATA__" not in content:
                tab_url = getattr(tab, "url", "")
                if "/blocked" in tab_url or "verifica tu identidad" in content.lower():
                    logger.warning(f"  [Desafío PX] Bloqueo detectado en {url}")
                else:
                    logger.warning(f"  Sin __NEXT_DATA__ en {url}")
                return None

            soup = BeautifulSoup(content, "html.parser")
            script = soup.find("script", id="__NEXT_DATA__")
            if not script or not script.string:
                return None

            data = json.loads(script.string)
            prod = (
                data.get("props", {})
                .get("pageProps", {})
                .get("initialData", {})
                .get("data", {})
                .get("product", {})
            )
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

            current_p = (
                cur_obj.get("price")
                or cur_obj.get("priceDisplay")
                or list_obj.get("price")
            )
            was_p = (
                was_obj.get("price")
                or was_obj.get("priceString")
                or list_obj.get("price")
            )

            p_promo = limpiar_precio(current_p)
            p_reg = limpiar_precio(was_p) or p_promo

            item_raw = {
                "producto": nombre,
                "marca": brand,
                "precio_promo": p_promo,
                "precio_regular": p_reg,
                "disponibilidad": disp_norm,
                "url": url,
                "condiciones": "Portal oficial Walmart (nodriver CDP)",
                "fuente": "Walmart México (nodriver CDP)",
            }
            logger.info(f"  ✓ Extraído: {nombre} | Promo: ${p_promo} | Reg: ${p_reg} | Disp: {disp_norm}")
            return item_raw

        except (json.JSONDecodeError, KeyError, ValueError, OSError, RuntimeError) as e:
            logger.warning(f"  Error procesando {url}: {e}")
            return None
        finally:
            if tab:
                try:
                    await tab.close()
                except (OSError, RuntimeError, TimeoutError, ValueError):
                    pass



async def _extraer_datos_pdp_async(
    urls: List[str],
    headless: bool = False,
    delay_min: float = 2.5,
    delay_max: float = 4.0,
    concurrencia: int = 3,
) -> List[Dict[str, Any]]:
    """
    Navega concurrentemente por una lista de páginas de producto (PDP) con control de semáforo
    y calentamiento de sesión en la página de inicio.
    """
    if uc is None:
        logger.warning("nodriver no está disponible en este entorno.")
        return []

    chrome_bin = obtener_binario_chrome_disponible()
    if not chrome_bin:
        logger.warning("No se localizó un binario ejecutable de Chrome para nodriver.")
        return []

    logger.info(f"Iniciando navegador CDP nodriver (binario: {chrome_bin}, headless: {headless}, workers: {concurrencia})...")
    browser = await uc.start(
        browser_executable_path=chrome_bin,
        headless=headless,
        browser_args=["--no-sandbox", "--disable-dev-shm-usage"],
    )

    resultados: List[Dict[str, Any]] = []

    try:
        # Calentar sesión en la página principal para establecer contexto residencial orgánico
        logger.info("Estableciendo sesión orgánica en Walmart...")
        home_tab = await browser.get("https://www.walmart.com.mx")
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
            )
            for i, url in enumerate(urls, 1)
        ]

        respuestas = await asyncio.gather(*tasks, return_exceptions=True)
        for r in respuestas:
            if isinstance(r, dict):
                resultados.append(r)

    finally:
        try:
            browser.stop()
            logger.info("Navegador nodriver detenido.")
        except (OSError, RuntimeError, TimeoutError, ValueError):
            pass

    return resultados


def consultar_pdps_con_nodriver(
    urls: List[str],
    headless: bool = False,
    delay_min: float = 2.5,
    delay_max: float = 4.0,
    concurrencia: int = 3,
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
        )
    )

