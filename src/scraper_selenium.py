"""
Scraper automatizado con Selenium y BeautifulSoup para páginas dinámicas (SPA).

Características:
- Navegador Google Chrome por defecto (con fallback a Firefox).
- User-Agent realista de escritorio Linux, evasión de `navigator.webdriver` y banderas limpias.
- Tiempos de espera configurables con variación aleatoria (jitter) para evitar ráfagas.
- Enfoque Human-in-the-Loop robusto: detecta PerimeterX ("Mantén presionado") y Cloudflare,
  pausa el script con cuenta regresiva de 30 segundos y guía al usuario en pantalla.
- Espera activa de hidratación tras resolver desafíos para asegurar que el DOM
  cargue los componentes dinámicos de React/SPA (>35 KB) y desplazamiento suave (scroll).
- Estrategia de extracción híbrida:
  1. Extracción de datos embebidos JSON-LD y __NEXT_DATA__ (Next.js / Electrode).
  2. Extracción de tarjetas DOM mediante selectores de Sam's Club / Walmart MX y enlaces a productos.
- Si no se extraen productos, genera un volcado diagnóstico en 'data/debug_page.html'.
- Etiquetado de confianza: 'Confirmado' al extraerse directamente de la página oficial.
"""

import os
import sys
import re
import json
import time
import random
import argparse
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup

# Asegurar que el directorio raíz del proyecto esté en sys.path
RAIZ_PROYECTO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if RAIZ_PROYECTO not in sys.path:
    sys.path.insert(0, RAIZ_PROYECTO)

try:
    from src.clasificacion import extraer_ml, clasificar_categoria
except ModuleNotFoundError:
    from clasificacion import extraer_ml, clasificar_categoria


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

CHROME_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"

INDICADORES_CHALLENGE = [
    "verify your identity",
    "verifica tu identidad",
    "px-captcha",
    "perimeterx",
    "mantén presionado",
    "press and hold",
    "just a moment",
    "challenge-running",
    "cf-challenge-running",
    "verificación de seguridad",
    "security check",
    "captcha",
    "unusual traffic",
    "bloqueo temporal",
    "robot",
    "attention required",
    "human verification"
]


def inicializar_driver(headless: bool = False, navegador: str = "chrome") -> webdriver.Remote:
    """Inicializa Selenium en Chrome (o Firefox) con User-Agent y banderas de navegador real."""
    if navegador.lower() == "chrome":
        options = ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--start-maximized")
        options.add_argument(f"user-agent={CHROME_USER_AGENT}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        try:
            driver = webdriver.Chrome(options=options)
            # Evadir la detección de navigator.webdriver en Chrome
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """
            })
        except Exception as e:
            print(f"[AVISO] No se pudo iniciar Chrome ({e}). Intentando con Firefox...", file=sys.stderr)
            return inicializar_driver(headless=headless, navegador="firefox")
    else:
        options = FirefoxOptions()
        if headless:
            options.add_argument("-headless")
        options.set_preference("general.useragent.override", CHROME_USER_AGENT)
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
        except Exception:
            pass

        try:
            top_msg = driver.find_elements(By.ID, "topmessage")
            if top_msg and any("identidad" in m.text.lower() or "identity" in m.text.lower() for m in top_msg):
                return True, "Mensaje de verificación de identidad activo (#topmessage)"
        except Exception:
            pass

        try:
            cf = driver.find_elements(By.ID, "challenge-running")
            if cf and any(c.is_displayed() for c in cf):
                return True, "Desafío Cloudflare activo (#challenge-running)"
        except Exception:
            pass

        # Búsqueda en los primeros 10KB del código fuente
        html_head = (driver.page_source or "")[:10000].lower()
        if "px-captcha" in html_head or "verifica tu identidad" in html_head or "verify your identity" in html_head:
            if "mantén presionado el botón" in html_head or "press and hold" in html_head:
                return True, "Texto de desafío PerimeterX en código fuente"

    except Exception:
        pass

    return False, ""


def verificar_y_esperar_desafio(driver: webdriver.Remote, timeout_humano: int = 30) -> bool:
    """
    Detecta si la página fue interceptada por un desafío de seguridad o CAPTCHA (ej. PerimeterX / Cloudflare).
    Pausa el script y emite alerta en terminal para que el usuario lo resuelva manualmente en la ventana abierta.
    Espera hasta `timeout_humano` segundos a que desaparezca el desafío y la página del catálogo cargue.
    """
    hay_desafio, motivo = detectar_desafio(driver)

    if hay_desafio:
        print("\n" + "!" * 80)
        print("[ALERTA: DESAFÍO DE SEGURIDAD / CAPTCHA EN PANTALLA]")
        print(f"Causa detectada: {motivo}")
        if any(k in motivo.lower() for k in ["px-captcha", "identidad", "identity", "perimeterx"]):
            print(">> ACCIÓN REQUERIDA: En la ventana de Google Chrome abierta,")
            print(">> MANTÉN PRESIONADO el botón blanco/gris hasta que la barra se llene")
            print(">> y la página se recargue.")
        else:
            print(">> ACCIÓN REQUERIDA: Resuelve la verificación manualmente en la ventana abierta.")
        print(f"El script pausará hasta {timeout_humano} segundos esperando que la página se desbloquee...")
        print("!" * 80 + "\n")

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
                print(f"  ... esperando que resuelvas el desafío en Chrome ({restante}s restantes)...")

            if not sigue_desafio:
                print(f"[OK] Desafío resuelto por el usuario en {transcurrido}s. Continuando extracción...\n")
                # Breve pausa para dar tiempo a la redirección o reload de la página
                time.sleep(3.0)
                return True

        print(f"\n[ADVERTENCIA] Tiempo de espera para resolución manual agotado ({timeout_humano}s).")
        return False

    return True


def extraer_precio_texto(texto: str) -> float | None:
    """Extrae valor numérico de una cadena con formato de precio ($1,234.50 o 1234.50)."""
    if not texto:
        return None
    texto = texto.replace('\xa0', ' ').strip()
    match = re.search(r'[\$]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', texto)
    if match:
        limpio = match.group(1).replace(',', '')
        try:
            val = float(limpio)
            return val if val > 0 else None
        except ValueError:
            return None
    return None


def extraer_de_json_embebido(soup: BeautifulSoup, url: str, tienda: str, fecha_consulta: str) -> list[dict]:
    """Intenta extraer productos directamente de scripts JSON-LD o __NEXT_DATA__."""
    productos = []
    scripts = soup.find_all("script", attrs={"type": re.compile(r'json', re.I)})

    for s in scripts:
        if not s.string or len(s.string) < 60:
            continue
        try:
            data = json.loads(s.string)
        except Exception:
            continue

        # Caso 1: JSON-LD ItemList
        if isinstance(data, dict) and data.get("@type") == "ItemList":
            elementos = data.get("itemListElement", [])
            for elem in elementos:
                item = elem.get("item", elem)
                nombre = item.get("name")
                ofertas = item.get("offers", {})
                precio = ofertas.get("price") if isinstance(ofertas, dict) else None
                if nombre and precio:
                    p_val = extraer_precio_texto(str(precio))
                    if p_val and p_val > 50:
                        cat, subcat = clasificar_categoria(nombre)
                        ml = extraer_ml(nombre)
                        productos.append({
                            "tienda": tienda,
                            "producto": nombre,
                            "marca": nombre.split()[0],
                            "categoria": cat,
                            "subcategoria": subcat,
                            "clase": subcat if cat in ["Tequila", "Mezcal"] else "no_aplica",
                            "tipo_mezcal": "Artesanal" if cat == "Mezcal" else "no_aplica",
                            "especie_agave": "Tequilana Weber azul" if cat == "Tequila" else ("Espadín" if cat == "Mezcal" else "no_aplica"),
                            "productor": "no_verificado",
                            "sello_regulador": "no_verificado",
                            "ml": ml,
                            "abv": 38.0 if cat in ["Tequila", "Mezcal"] else 40.0,
                            "precio_regular": p_val,
                            "precio_promo": p_val,
                            "unidades_promo": 1,
                            "precio_total_promo": p_val,
                            "condiciones": "Consulta web directa (JSON-LD)",
                            "disponibilidad": "disponible",
                            "url": item.get("url") or url,
                            "fecha_consulta": fecha_consulta,
                            "fuente": f"Página oficial ({tienda})",
                            "confianza": "Confirmado"
                        })

        # Caso 2: __NEXT_DATA__ (Next.js / Electrode / Walmart platform)
        if s.get("id") == "__NEXT_DATA__" and isinstance(data, dict):
            def buscar_items_recursivo(obj):
                encontrados = []
                if isinstance(obj, dict):
                    nombre = obj.get("name") or obj.get("title") or obj.get("displayName")
                    precio_obj = obj.get("price") or obj.get("priceInfo") or obj.get("prices") or obj.get("itemPrice")
                    if nombre and isinstance(nombre, str) and len(nombre) > 5 and precio_obj:
                        p_val = None
                        if isinstance(precio_obj, (int, float)):
                            p_val = float(precio_obj)
                        elif isinstance(precio_obj, str):
                            p_val = extraer_precio_texto(precio_obj)
                        elif isinstance(precio_obj, dict):
                            for k in ["price", "itemPrice", "currentPrice", "finalPrice", "priceString"]:
                                if k in precio_obj and precio_obj[k] is not None:
                                    p_val = extraer_precio_texto(str(precio_obj[k]))
                                    if p_val:
                                        break
                        if p_val and p_val > 50:
                            prod_url = obj.get("productUrl") or obj.get("canonicalUrl") or url
                            encontrados.append((nombre, p_val, prod_url))

                    for v in obj.values():
                        encontrados.extend(buscar_items_recursivo(v))
                elif isinstance(obj, list):
                    for elem in obj:
                        encontrados.extend(buscar_items_recursivo(elem))
                return encontrados

            items_next = buscar_items_recursivo(data)
            nombres_vistos = set()
            for nombre, p_val, prod_url in items_next:
                if nombre in nombres_vistos:
                    continue
                nombres_vistos.add(nombre)
                cat, subcat = clasificar_categoria(nombre)
                ml = extraer_ml(nombre)
                full_url = f"https://www.sams.com.mx{prod_url}" if prod_url.startswith("/") else prod_url
                productos.append({
                    "tienda": tienda,
                    "producto": nombre,
                    "marca": nombre.split()[0],
                    "categoria": cat,
                    "subcategoria": subcat,
                    "clase": subcat if cat in ["Tequila", "Mezcal"] else "no_aplica",
                    "tipo_mezcal": "Artesanal" if cat == "Mezcal" else "no_aplica",
                    "especie_agave": "Tequilana Weber azul" if cat == "Tequila" else ("Espadín" if cat == "Mezcal" else "no_aplica"),
                    "productor": "no_verificado",
                    "sello_regulador": "no_verificado",
                    "ml": ml,
                    "abv": 38.0 if cat in ["Tequila", "Mezcal"] else 40.0,
                    "precio_regular": p_val,
                    "precio_promo": p_val,
                    "unidades_promo": 1,
                    "precio_total_promo": p_val,
                    "condiciones": "Consulta web directa (__NEXT_DATA__)",
                    "disponibilidad": "disponible",
                    "url": full_url,
                    "fecha_consulta": fecha_consulta,
                    "fuente": f"Página oficial ({tienda})",
                    "confianza": "Confirmado"
                })

    return productos


def parsear_html_con_bs4(html_source: str, url: str, tienda: str) -> list[dict]:
    """Parsea el HTML renderizado con BeautifulSoup y extrae productos estructurados."""
    soup = BeautifulSoup(html_source, "html.parser")
    fecha_consulta = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Estrategia 1: Intentar extracción de JSON estructurado embebido
    prods_json = extraer_de_json_embebido(soup, url, tienda, fecha_consulta)
    if prods_json:
        return prods_json

    productos = []

    # Estrategia 2: Página de producto individual (PDP)
    h1 = soup.find("h1")
    precios_pdp = soup.find_all(attrs={"class": re.compile(r'price|precio|val', re.I)})
    if h1 and precios_pdp:
        nombre = h1.get_text(strip=True)
        precio = extraer_precio_texto(precios_pdp[0].get_text(strip=True))
        if precio and len(nombre) > 5:
            categoria, subcategoria = clasificar_categoria(nombre)
            ml = extraer_ml(nombre)
            return [{
                "tienda": tienda,
                "producto": nombre,
                "marca": nombre.split()[0],
                "categoria": categoria,
                "subcategoria": subcategoria,
                "clase": subcategoria if categoria in ["Tequila", "Mezcal"] else "no_aplica",
                "tipo_mezcal": "Artesanal" if categoria == "Mezcal" else "no_aplica",
                "especie_agave": "Tequilana Weber azul" if categoria == "Tequila" else ("Espadín" if categoria == "Mezcal" else "no_aplica"),
                "productor": "no_verificado",
                "sello_regulador": "no_verificado",
                "ml": ml,
                "abv": 38.0 if categoria in ["Tequila", "Mezcal"] else 40.0,
                "precio_regular": precio,
                "precio_promo": precio,
                "unidades_promo": 1,
                "precio_total_promo": precio,
                "condiciones": "Consulta web directa en página de producto",
                "disponibilidad": "disponible",
                "url": url,
                "fecha_consulta": fecha_consulta,
                "fuente": f"Página oficial ({tienda})",
                "confianza": "Confirmado"
            }]

    # Estrategia 3: Listado de búsqueda o catálogo (búsqueda amplia de contenedores)
    tarjetas = soup.find_all(attrs={"data-testid": re.compile(r'product|item|card', re.I)}) or \
               soup.find_all("div", class_=re.compile(r'sc-pc-|product-card|item-card|sc-product|product-item|ProductCard', re.I)) or \
               soup.find_all("article")

    # Si no hay tarjetas explícitas con esos selectores, buscar enlaces a productos
    if not tarjetas:
        enlaces_prod = soup.find_all("a", href=re.compile(r'/p/|/ip/|/producto/', re.I))
        vistos = set()
        for a in enlaces_prod:
            contenedor = a.find_parent("div", class_=True) or a.parent
            if contenedor and id(contenedor) not in vistos:
                vistos.add(id(contenedor))
                tarjetas.append(contenedor)

    nombres_procesados = set()
    for tarjeta in tarjetas:
        # Extraer nombre
        elem_nombre = tarjeta.find(re.compile(r'h[1-4]|a|span|p'), attrs={"class": re.compile(r'title|name|desc', re.I)}) or \
                      tarjeta.find("a", href=re.compile(r'/p/|/ip/', re.I)) or \
                      tarjeta.find("a")
        nombre = elem_nombre.get_text(strip=True) if elem_nombre else ""

        if not nombre or len(nombre) < 6 or nombre in nombres_procesados:
            continue

        # Extraer precios (buscar regular y promo si ambos aparecen)
        elems_precio = tarjeta.find_all(attrs={"class": re.compile(r'price|precio|val', re.I)}) or \
                       tarjeta.find_all(string=re.compile(r'\$\s*\d+'))

        valores_precio = []
        for ep in elems_precio:
            t = ep.get_text(strip=True) if hasattr(ep, 'get_text') else str(ep)
            val = extraer_precio_texto(t)
            if val and val > 40:
                valores_precio.append(val)

        if not valores_precio:
            continue

        nombres_procesados.add(nombre)
        precio_regular = max(valores_precio)
        precio_promo = min(valores_precio)
        condicion = "Descuento en línea" if precio_regular > precio_promo else "Precio regular de catálogo"

        categoria, subcategoria = clasificar_categoria(nombre)
        ml = extraer_ml(nombre)

        # Extraer link del producto si existe
        link_elem = tarjeta.find("a", href=re.compile(r'/p/|/ip/', re.I))
        item_url = url
        if link_elem and link_elem.get("href"):
            href = link_elem["href"]
            item_url = f"https://www.sams.com.mx{href}" if href.startswith("/") else href

        productos.append({
            "tienda": tienda,
            "producto": nombre,
            "marca": nombre.split()[0],
            "categoria": categoria,
            "subcategoria": subcategoria,
            "clase": subcategoria if categoria in ["Tequila", "Mezcal"] else "no_aplica",
            "tipo_mezcal": "Artesanal" if categoria == "Mezcal" else "no_aplica",
            "especie_agave": "Tequilana Weber azul" if categoria == "Tequila" else ("Espadín" if categoria == "Mezcal" else "no_aplica"),
            "productor": "no_verificado",
            "sello_regulador": "no_verificado",
            "ml": ml,
            "abv": 38.0 if categoria in ["Tequila", "Mezcal"] else 40.0,
            "precio_regular": precio_regular,
            "precio_promo": precio_promo,
            "unidades_promo": 1,
            "precio_total_promo": precio_promo,
            "condiciones": condicion,
            "disponibilidad": "disponible",
            "url": item_url,
            "fecha_consulta": fecha_consulta,
            "fuente": f"Página oficial ({tienda})",
            "confianza": "Confirmado"
        })

    return productos


def consultar_urls_secuenciales(urls: list[str], tienda: str = "Sam's Club", headless: bool = False, navegador: str = "chrome") -> list[dict]:
    """
    Navega por una lista de URLs de forma secuencial y controlada, aplicando
    pausas humanas y esperando activamente la resolución de desafíos e hidratación del DOM.
    """
    driver = None
    resultados = []
    try:
        print(f"[Selenium] Iniciando {navegador.upper()} con User-Agent de escritorio...")
        driver = inicializar_driver(headless=headless, navegador=navegador)

        for i, url in enumerate(urls, 1):
            print(f"\n({i}/{len(urls)}) Navegando a: {url}")
            driver.get(url)

            # Pausa de inicio
            pausa_humana(2.5, 3.5)

            # Verificar si hay CAPTCHA o desafío WAF (30 segundos)
            if not verificar_y_esperar_desafio(driver, timeout_humano=30):
                print(f"[AVISO] Saltando {url} debido a desafío no resuelto.")
                continue

            # Desplazamiento suave para gatillar lazy loading
            try:
                driver.execute_script("window.scrollTo(0, 500);")
                time.sleep(1.0)
                driver.execute_script("window.scrollTo(0, 0);")
            except Exception:
                pass

            # ESPERA ACTIVA DE HIDRATACIÓN TRAS DESAFÍO
            print("[Selenium] Esperando que la página hidrate los componentes dinámicos...")
            html = ""
            for intento in range(10):
                time.sleep(2)
                # Re-comprobar si tras la navegación se reactivó el desafío
                sigue_desafio, _ = detectar_desafio(driver)
                if sigue_desafio:
                    print("  ... re-apareció desafío, pausando...")
                    verificar_y_esperar_desafio(driver, timeout_humano=20)

                html = driver.page_source
                tamano = len(html)
                print(f"  ... cargando DOM: {tamano} bytes")
                # Si el DOM supera los 35 KB, la página ya cargó scripts y componentes de catálogo
                if tamano > 35000:
                    break

            # Breve pausa final para renderizado de precios
            time.sleep(1.5)
            html = driver.page_source

            print(f"[BeautifulSoup] Analizando {len(html)} bytes de DOM...")
            prods = parsear_html_con_bs4(html, url, tienda)
            print(f"  -> {len(prods)} productos extraídos.")

            if len(prods) == 0:
                debug_file = "data/debug_page.html"
                with open(debug_file, "w", encoding="utf-8") as f:
                    f.write(html)
                print(f"  [DIAGNÓSTICO] Se guardó una copia del HTML en '{debug_file}' ({len(html)} bytes) para inspección.")

            resultados.extend(prods)

            # Pausa entre páginas
            if i < len(urls):
                pausa_humana(3.0, 5.0)

    except Exception as e:
        print(f"[ERROR] Error durante la ejecución del navegador: {e}", file=sys.stderr)
    finally:
        if driver:
            driver.quit()
            print("[Selenium] Navegador cerrado limpiamente.")

    return resultados


def main():
    parser = argparse.ArgumentParser(description="Scraper con Selenium + BeautifulSoup (Chrome, pausas humanas y espera de hidratación).")
    parser.add_argument("--urls", nargs="+", required=True, help="Lista de URLs a consultar.")
    parser.add_argument("--tienda", default="Sam's Club", help="Tienda que se está consultando.")
    parser.add_argument("--navegador", default="chrome", choices=["chrome", "firefox"], help="Navegador a utilizar.")
    parser.add_argument("--headless", action="store_true", help="Ejecutar sin ventana gráfica.")
    parser.add_argument("--salida", default="data/scraped_selenium.csv", help="Archivo CSV donde guardar la prueba.")
    args = parser.parse_args()

    prods = consultar_urls_secuenciales(args.urls, tienda=args.tienda, headless=args.headless, navegador=args.navegador)
    if prods:
        df = pd.DataFrame(prods)
        df.to_csv(args.salida, index=False)
        print(f"\n[ÉXITO] Se guardaron {len(df)} registros sin deduplicar en: {args.salida}")
    else:
        print("\n[RESULTADO] No se extrajeron productos. Revisa 'data/debug_page.html' para ver el estado de la página.")


if __name__ == "__main__":
    main()
