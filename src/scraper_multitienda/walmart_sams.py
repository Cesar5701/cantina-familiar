"""
Scraper para Sam's Club y Walmart México mediante SSR __NEXT_DATA__ JSON.
Incluye cabeceras de previsualización SSR (sin bloqueo HTTP 412 de PerimeterX),
detección temprana de desafío WAF (Circuit Breaker) y respaldo automático desde catálogo verificado.
"""

import json
import os
import random
import time
import urllib.error
import urllib.parse
from datetime import datetime

import pandas as pd
from bs4 import BeautifulSoup

import src.scraper_multitienda as _pkg
import src.scraper_selenium as _sel_pkg
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


def es_respuesta_prerender_falsa(data: dict, termino: str) -> tuple[bool, str]:
    """
    Detecta si el proxy Akamai/Prerender de Walmart ignoró el query string
    y sirvió una página estática en caché no relacionada (ej. 'leche' o 'Quaker').
    """
    if not isinstance(data, dict):
        return False, ""
    q_obj = data.get("query")
    q_real = str(q_obj.get("q") or "").strip().lower() if isinstance(q_obj, dict) else ""
    sr = data.get("props", {}).get("pageProps", {}).get("initialData", {}).get("searchResult", {})
    titulo_sr = str(sr.get("title") or "").strip().lower() if isinstance(sr, dict) else ""

    tokens_busqueda = [tok for tok in termino.lower().split() if len(tok) >= 3]
    if not tokens_busqueda:
        return False, ""

    if q_real and not any(tok in q_real or q_real in tok for tok in tokens_busqueda):
        return True, q_real
    if "resultados para" in titulo_sr and not any(tok in titulo_sr for tok in tokens_busqueda):
        return True, titulo_sr
    return False, ""


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


def _generar_clave_producto(item: dict) -> str:
    """Genera una clave única determinista para deduplicación y merge incremental."""
    tienda = str(item.get("tienda") or "").strip().lower()
    producto = str(item.get("producto") or "").strip().lower()
    ml = str(item.get("ml") or "").strip().lower()
    if tienda and producto:
        return f"{tienda}|{producto}|{ml}"
    url = str(item.get("url") or "").strip().lower()
    url = url.replace("https://", "").replace("http://", "")
    if url.startswith("www."):
        url = url[4:]
    return url.rstrip("/")


def _ejecutar_contingencia_navegador(
    tienda: str,
    base_domain: str,
    terminos: list[str],
    catalogo_acumulado: dict[str, dict],
    resumen: ResumenScraping,
    fecha_actual: str,
    headless: bool = False,
) -> tuple[int, int]:
    """
    Ejecuta la extracción de contingencia mediante navegador indetectable (Ruta C: nodriver CDP)
    o Selenium como respaldo secundario cuando las peticiones HTTP son bloqueadas.
    Prioriza consultar directamente URLs de producto (PDP) ya conocidas para Walmart.
    """
    actualizados_sel = 0
    insertados_sel = 0
    prods_raw: list[dict] = []


    # Ruta C: Si es Walmart y tenemos productos conocidos con URL /ip/, consultar directamente via CDP por lotes categóricos
    items_walmart = [
        item for item in catalogo_acumulado.values()
        if item.get("url") and "/ip/" in item["url"] and base_domain in item["url"]
    ]

    if "walmart" in tienda.lower() and items_walmart and getattr(_sel_pkg, "consultar_pdps_con_nodriver", None):
        # Agrupar URLs por categoría para procesar en lotes seguros con pausas de enfriamiento
        categorias_orden = ["Tequila", "Whisky", "Mezcal", "Licor de Whisky", "Vino"]
        grupos_categoria: dict[str, list[str]] = {cat: [] for cat in categorias_orden}
        grupos_categoria["Otros"] = []

        for it in items_walmart:
            c = str(it.get("categoria") or "").strip()
            if c in grupos_categoria:
                grupos_categoria[c].append(it["url"])
            else:
                grupos_categoria["Otros"].append(it["url"])

        logger.info(
            f"  🌐 [{tienda}] Activando Ruta C por Lotes Categóricos con nodriver CDP "
            f"({len(items_walmart)} productos en catálogo)..."
        )

        for cat, urls_cat in grupos_categoria.items():
            if not urls_cat:
                continue

            # Muestra representativa de alta prioridad por categoría (ej. 15 productos por lote en ejecuciones interactivas)
            limite_cat = 25 if os.environ.get("WALMART_SCRAPE_ALL") else min(len(urls_cat), 10)
            urls_lote = urls_cat[:limite_cat]

            logger.info(f"  👉 [Lote {cat.upper()}] Consultando {len(urls_lote)} PDPs prioritarias...")
            try:
                lote_extraido = _sel_pkg.consultar_pdps_con_nodriver(
                    urls=urls_lote,
                    headless=headless,
                    delay_min=2.0,
                    delay_max=3.5,
                    concurrencia=3,
                )
                if lote_extraido:
                    prods_raw.extend(lote_extraido)
                    logger.info(f"     ✓ {len(lote_extraido)}/{len(urls_lote)} productos extraídos en categoría {cat}.")

                # Pausa humana de enfriamiento entre categorías (cool-off period para resetear contadores WAF)
                if len(grupos_categoria) > 1 and not os.environ.get("PYTEST_CURRENT_TEST"):
                    logger.info("     ☕ Pausa de enfriamiento entre categorías (5 segundos)...")
                    time.sleep(5.0)

            except (OSError, RuntimeError, TimeoutError, ValueError) as e:
                logger.warning(f"  ⚠️ [{tienda}] Error en lote de {cat}: {e}")


    # Fallback si nodriver no obtuvo resultados o si es Sam's Club / búsqueda general
    if not prods_raw:
        urls = [f"https://{base_domain}/search?q={urllib.parse.quote(t)}" for t in terminos]
        logger.info(
            f"  🌐 [{tienda}] Ejecutando navegación por búsquedas ({len(urls)} consultas en {base_domain})..."
        )
        try:
            prods_raw = _sel_pkg.consultar_urls_secuenciales(
                urls=urls,
                tienda=tienda,
                headless=headless,
                navegador="chrome",
            )
        except (OSError, RuntimeError, TimeoutError, ValueError, _sel_pkg.WebDriverException) as e:
            logger.warning(f"  ⚠️ [{tienda}] Navegador no disponible ({e}).")
            return 0, 0


    for raw in prods_raw:
        nombre = str(raw.get("producto") or raw.get("name") or "").strip()
        marca = str(raw.get("marca") or raw.get("brand") or "").strip()
        p_promo = limpiar_precio(raw.get("precio_promo"))
        p_reg = limpiar_precio(raw.get("precio_regular"))
        if p_promo and (not p_reg or p_reg < p_promo):
            p_reg = p_promo
        url_prod = str(raw.get("url") or f"https://{base_domain}").strip()
        cond = str(raw.get("condiciones") or f"Portal oficial {base_domain} (Selenium)")

        item_norm = evaluar_y_normalizar_producto(
            tienda=tienda,
            nombre=nombre,
            marca=marca,
            precio_regular=p_reg,
            precio_promo=p_promo,
            disponible=str(raw.get("disponibilidad") or "disponible"),
            url=url_prod,
            condicion=cond,
            fuente=f"Portal oficial {base_domain} (Selenium)",
            fecha_actual=fecha_actual,
        )
        if item_norm:
            clave = _generar_clave_producto(item_norm)
            if clave in catalogo_acumulado:
                actualizados_sel += 1
            else:
                insertados_sel += 1
            catalogo_acumulado[clave] = item_norm
            resumen.registrar_exito()
        else:
            resumen.registrar_descarte("filtro categoría o volumen (Selenium)")

    logger.info(
        f"  -> [{tienda} Selenium] +{actualizados_sel} actualizados, +{insertados_sel} nuevos "
        f"(Catálogo acumulado: {len(catalogo_acumulado)})"
    )
    return actualizados_sel, insertados_sel


def scrapear_nextjs_walmart_platform(
    tienda: str,
    base_domain: str,
    terminos: list[str],
    ruta_respaldo: str | None = None,
    delay_min: float = 3.5,
    delay_max: float = 6.5,
    usar_fallback_selenium: bool | None = None,
    forzar_selenium: bool = False,
    headless_selenium: bool = False,
) -> list[dict]:
    logger.info("=" * 60)
    logger.info(f"SCRAPEANDO {tienda.upper()} ({base_domain} SSR __NEXT_DATA__)")
    logger.info("=" * 60)
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M")
    ids_vistos = set()
    resumen = ResumenScraping(tienda)
    bloqueos_waf_consecutivos = 0

    if usar_fallback_selenium is None:
        usar_fallback_selenium = not bool(os.environ.get("PYTEST_CURRENT_TEST"))

    # 1. Cargar catálogo previo para merge incremental (evita pérdida de productos previos por WAF/IP)
    catalogo_acumulado: dict[str, dict] = {}
    if ruta_respaldo and os.path.exists(ruta_respaldo):
        respaldo_inicial = _cargar_respaldo_csv(ruta_respaldo)
        for item in respaldo_inicial:
            clave = _generar_clave_producto(item)
            catalogo_acumulado[clave] = item
        if catalogo_acumulado:
            logger.info(
                f"  [{tienda}] Catálogo base cargado: {len(catalogo_acumulado)} productos existentes para actualización incremental."
            )

    actualizados_count = 0
    insertados_count = 0

    for idx, t in enumerate([] if forzar_selenium else terminos):
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
                    logger.warning(
                        f"  [Circuit Breaker] Protección WAF/PerimeterX detectada en {base_domain} para '{t}'. "
                        f"Deteniendo consultas adicionales para proteger la IP (se conservan {len(catalogo_acumulado)} productos previos/actualizados)."
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
            es_prerender_falso, q_falsa = es_respuesta_prerender_falsa(data, t)
            if es_prerender_falso:
                bloqueos_waf_consecutivos += 1
                logger.warning(
                    f"  [Circuit Breaker] Caché señuelo Akamai/Prerender detectada en {base_domain} "
                    f"(devolvió '{q_falsa}' en lugar de '{t}'). Deteniendo consultas HTTP para proteger IP."
                )
                break

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
                    avail_val = avail_obj.get("value", "") if isinstance(avail_obj, dict) else str(avail_obj)
                    avail_disp = str(avail_obj.get("display", "")).lower() if isinstance(avail_obj, dict) else ""
                    status = str(it.get("availabilityStatus", "")).upper()
                    show_atc = it.get("showAtc")
                    can_atc = it.get("canAddToCart")

                    is_out_of_stock = (
                        it.get("isOutOfStock") is True
                        or avail_val in ["OUT_OF_STOCK", "NOT_AVAILABLE", "UNAVAILABLE"]
                        or status in ["OUT_OF_STOCK", "NOT_AVAILABLE", "UNAVAILABLE"]
                        or avail_disp in ["out of stock", "agotado", "no disponible"]
                        or show_atc is False
                        or can_atc is False
                    )
                    if is_out_of_stock:
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
                        clave = _generar_clave_producto(item_norm)
                        if clave in catalogo_acumulado:
                            actualizados_count += 1
                        else:
                            insertados_count += 1
                        catalogo_acumulado[clave] = item_norm
                        resumen.registrar_exito()
                        nuevos_q += 1
                    else:
                        resumen.registrar_descarte("filtro categoría o volumen")

            logger.info(
                f"  -> '{t}': +{nuevos_q} productos en consulta "
                f"(Catálogo acumulado {tienda}: {len(catalogo_acumulado)})"
            )

            # Pausa de cortesía humanizada con jitter entre términos para evitar rate limiting
            if idx < len(terminos) - 1:
                espera = 0.0 if os.environ.get("PYTEST_CURRENT_TEST") else random.uniform(delay_min, delay_max)
                if espera > 0:
                    time.sleep(espera)

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
            if idx < len(terminos) - 1:
                espera = 0.0 if os.environ.get("PYTEST_CURRENT_TEST") else random.uniform(2.0, 4.0)
                if espera > 0:
                    time.sleep(espera)

    # 2. Contingencia automática con navegador indetectable (Ruta C: nodriver) / Selenium si HTTP fue bloqueado
    requiere_navegador = forzar_selenium or (
        usar_fallback_selenium and (actualizados_count + insertados_count) == 0 and len(terminos) > 0
    )
    if requiere_navegador:
        u_nav, i_nav = _ejecutar_contingencia_navegador(
            tienda=tienda,
            base_domain=base_domain,
            terminos=terminos,
            catalogo_acumulado=catalogo_acumulado,
            resumen=resumen,
            fecha_actual=fecha_actual,
            headless=headless_selenium,
        )
        actualizados_count += u_nav
        insertados_count += i_nav


    resultados = list(catalogo_acumulado.values())

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

    logger.info(
        f"  -> [{tienda}] Total consolidado: {len(resultados)} productos "
        f"({actualizados_count} actualizados en sesión, {insertados_count} nuevos agregados)."
    )

    resumen.imprimir_resumen()
    return resultados
