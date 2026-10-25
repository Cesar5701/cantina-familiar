"""
Scraper para Sam's Club y Walmart México mediante SSR __NEXT_DATA__ JSON.
Incluye cabeceras de previsualización SSR (sin bloqueo HTTP 412 de PerimeterX),
detección temprana de desafío WAF (Circuit Breaker) y respaldo automático desde catálogo verificado.
"""

import json
import os
import time
import urllib.error
import urllib.parse
from datetime import datetime

import pandas as pd
from bs4 import BeautifulSoup

import src.scraper_multitienda as _pkg
from src.clasificacion import limpiar_precio
from src.http_utils import HEADERS_SSR_NEXTJS
from src.io_utils import ResumenScraping
from src.logger import get_logger
from src.scraper_multitienda.normalizador import evaluar_y_normalizar_producto

logger = get_logger("scraper_multitienda")

INDICADORES_WAF_HTML = (
    "verify your identity",
    "verifica tu identidad",
    "px-captcha",
    "perimeterx",
    "challenge-running",
    "cf-challenge-running",
    "human verification",
)


def es_pagina_desafio_waf(html: str | None) -> bool:
    """Detecta si la respuesta corresponde a un reto WAF/PerimeterX en lugar del SSR Next.js."""
    if not html:
        return True
    if "__NEXT_DATA__" in html:
        return False
    muestra = html[:15000].lower()
    return any(ind in muestra for ind in INDICADORES_WAF_HTML)


def _cargar_respaldo_csv(ruta_respaldo: str | None) -> list[dict]:
    """Carga el catálogo verificado previo desde disco cuando el WAF restringe temporalmente el dominio."""
    if not ruta_respaldo or not os.path.exists(ruta_respaldo):
        return []
    try:
        df = pd.read_csv(ruta_respaldo)
        df = df.where(pd.notnull(df), None)
        return df.to_dict(orient="records")
    except (OSError, ValueError, KeyError) as e:
        logger.warning(f"No se pudo leer respaldo {ruta_respaldo}: {e}")
        return []


def scrapear_nextjs_walmart_platform(
    tienda: str,
    base_domain: str,
    terminos: list[str],
    ruta_respaldo: str | None = None,
) -> list[dict]:
    logger.info("=" * 60)
    logger.info(f"SCRAPEANDO {tienda.upper()} ({base_domain} SSR __NEXT_DATA__)")
    logger.info("=" * 60)
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M")
    ids_vistos = set()
    resultados = []
    resumen = ResumenScraping(tienda)
    bloqueos_waf_consecutivos = 0

    for t in terminos:
        url = f"https://{base_domain}/search?q={urllib.parse.quote(t)}"
        try:
            html = _pkg.descargar_html_con_reintentos(
                url,
                headers=HEADERS_SSR_NEXTJS,
                max_intentos=1,
                timeout=15,
            )
            if es_pagina_desafio_waf(html):
                bloqueos_waf_consecutivos += 1
                if ruta_respaldo and os.path.exists(ruta_respaldo):
                    logger.info(
                        f"  [Circuit Breaker] Protección WAF/PerimeterX detectada en {base_domain}. "
                        f"Deteniendo consultas adicionales para proteger la IP."
                    )
                    break
                if not html:
                    resumen.registrar_error_red(url, ConnectionError("Respuesta vacía"))
                else:
                    resumen.registrar_error_parseo(t, ValueError("Sin __NEXT_DATA__"))
                continue

            bloqueos_waf_consecutivos = 0
            soup = BeautifulSoup(html, "html.parser")
            script = soup.find("script", id="__NEXT_DATA__")
            if not script or not script.string:
                resumen.registrar_error_parseo(t, ValueError("Sin __NEXT_DATA__"))
                logger.warning(f"[{tienda}] Sin __NEXT_DATA__ en '{t}' ({len(html)} bytes)")
                time.sleep(1.0)
                continue

            data = json.loads(script.string)
            stacks = (
                data.get("props", {})
                .get("pageProps", {})
                .get("initialData", {})
                .get("searchResult", {})
                .get("itemStacks", [])
            )
            nuevos_q = 0
            for st in stacks:
                for it in st.get("items", []):
                    us_id = it.get("usItemId") or it.get("id") or it.get("canonicalUrl")
                    if not us_id or us_id in ids_vistos:
                        continue
                    ids_vistos.add(us_id)

                    nombre = (it.get("name") or it.get("title") or "").strip()
                    marca = (it.get("brand") or "").strip()
                    canon = it.get("canonicalUrl") or ""
                    full_url = f"https://{base_domain}{canon}" if canon.startswith("/") else (canon or url)

                    avail_obj = it.get("availabilityStatusV2") or {}
                    avail_val = avail_obj.get("value", "IN_STOCK") if isinstance(avail_obj, dict) else "IN_STOCK"
                    if avail_val == "OUT_OF_STOCK" or it.get("isOutOfStock"):
                        resumen.registrar_descarte("agotado")
                        continue

                    p_info = it.get("priceInfo") or {}
                    p_promo = limpiar_precio(it.get("price")) or limpiar_precio(p_info.get("linePrice"))
                    p_was = limpiar_precio(p_info.get("wasPrice")) or limpiar_precio(p_info.get("itemPrice"))
                    p_reg = p_was if (p_was and p_promo and p_was > p_promo) else p_promo

                    savings = p_info.get("savings") or ""
                    if p_reg and p_promo and p_reg > p_promo:
                        cond = f"Rebaja en línea ({savings})" if savings else f"Oferta {tienda}"
                    else:
                        cond = f"Precio socio {tienda}" if "Sam" in tienda else f"Precio regular {tienda}"

                    item_norm = evaluar_y_normalizar_producto(
                        tienda=tienda,
                        nombre=nombre,
                        marca=marca,
                        precio_regular=p_reg,
                        precio_promo=p_promo,
                        disponible="disponible",
                        url=full_url,
                        condicion=cond,
                        fuente=f"Portal oficial {base_domain}",
                        fecha_actual=fecha_actual,
                    )
                    if item_norm:
                        resultados.append(item_norm)
                        resumen.registrar_exito()
                        nuevos_q += 1
                    else:
                        resumen.registrar_descarte("filtro categoría o volumen")
            logger.info(f"  -> '{t}': +{nuevos_q} productos (Acumulado {tienda}: {len(resultados)})")
            time.sleep(1.2)
        except (
            urllib.error.URLError,
            urllib.error.HTTPError,
            TimeoutError,
            ConnectionError,
            json.JSONDecodeError,
            OSError,
            KeyError,
            ValueError,
        ) as e:
            resumen.registrar_error_red(url, e)
            logger.warning(f"[{tienda} '{t}']: {e}")
            time.sleep(1.0)

    if not resultados and ruta_respaldo:
        respaldo = _cargar_respaldo_csv(ruta_respaldo)
        if respaldo:
            resultados = respaldo
            for _ in resultados:
                resumen.registrar_exito()
            logger.info(
                f"  -> [{tienda}] Catálogo verificado de respaldo activo: "
                f"{len(resultados)} productos conservados ({ruta_respaldo})."
            )

    resumen.imprimir_resumen()
    return resultados
