# Cantina Familiar — Sistema de Decisión de Compra y Arbitraje Multitienda

Herramienta de optimización, comparativa multitienda y auditoría de precios por litro para compras de vinos y destilados en seis cadenas comerciales de México.

---

## Estructura del Proyecto

```
Cantina Familiar/
├── data/
│   ├── bebidas_verificadas.csv     # Dataset auditado con 32 etiquetas confirmadas
│   ├── campanas_activas.json       # Metadatos, vigencias y campañas activas detectadas por cadena
│   ├── historial_precios.csv       # Registro cronológico forense para semáforo anti-inflación
│   ├── scraped_*.csv               # Catálogos fuente por tienda (Alianza, Chedraui, Costco, Sam's, Soriana, Walmart)
│   ├── catalogo_completo_consolidado.csv # Catálogo unificado y normalizado
│   ├── ranking_completo_general.csv# Ranking filtrado libre de outliers de lujo
│   ├── dashboard_data.json         # JSON optimizado para el dashboard interactivo (1,018 registros)
│   └── reporte_ranking.csv         # Salida generada con métricas por litro y rankings
├── docs/
│   ├── politica_scraping.md        # Política de Scraping Ético y Gobernanza de Datos (H17)
│   └── archivo/                    # Archivo histórico de auditorías técnicas (V1 a V4)
├── logs/
│   └── cantina_familiar.log        # Registro estructurado rotativo (H19)
├── src/
│   ├── __init__.py
│   ├── clasificacion/              # Paquete de reglas NOM-006 / NOM-070, volumen, precios y sincronización
│   │   ├── __init__.py
│   │   ├── constantes.py           # Vocabularios normativos y umbrales centralizados (H32)
│   │   ├── volumen_y_precios.py    # Extracción de ml/L, multipacks y parseo de precios (H2, H6)
│   │   ├── reglas_nom.py           # Clasificación estricta NOM-006 / NOM-070 y especies de agave
│   │   └── filtros_y_catalogo.py   # Exclusión de mercancía y sincronización de catálogo (H41)
│   ├── analizador/                 # Paquete de análisis en pandas, arbitraje y rankings
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── campanas.py             # Detección automática de campañas comerciales y vigencias
│   │   ├── normalizacion.py        # Reglas declarativas de normalización y detección de paquetes (H38)
│   │   ├── esquema_y_auditoria.py  # Validación de esquema, rangos y datos faltantes (H9)
│   │   ├── metricas_y_outliers.py  # Cálculo vectorial $/L, outliers de lujo y filtro de presupuesto
│   │   ├── cross_tienda.py         # Deduplicación y arbitraje cross-tienda (H8, H35, H40)
│   │   └── rankings_y_cli.py       # Rankings por categoría comparable y CLI ad-hoc
│   ├── scraper_multitienda/        # Paquete de adquisición multitienda (Sam's, Costco, Walmart, Chedraui, Soriana)
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── normalizador.py         # Normalización y filtrado estricto multitienda
│   │   ├── costco.py               # Scraper API REST OCC v2 Costco México
│   │   ├── chedraui.py             # Scraper API VTEX Chedraui
│   │   ├── walmart_sams.py         # Scraper SSR __NEXT_DATA__ Sam's Club y Walmart
│   │   ├── soriana.py              # Scraper SFCC Soriana
│   │   └── cli.py                  # Orquestador de extracción por lote
│   ├── scraper_selenium/           # Paquete de scraping SPA asistido (Human-in-the-Loop) y nodriver CDP
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── driver_y_waf.py         # Inicialización Chrome/Firefox y detección de retos WAF/CAPTCHA
│   │   ├── nodriver_cdp.py         # Conector asíncrono CDP indetectable con abort flag y rate limiting
│   │   ├── parsers_dom.py          # Extracción híbrida JSON-LD, __NEXT_DATA__ y tarjetas DOM
│   │   └── navegador_cli.py        # Navegación secuencial con hidratación y CLI
│   ├── scraper_catalogo_completo/  # Paquete de extracción exhaustiva paginada para Bodegas Alianza
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── clasificador_alianza.py # Clasificación de ítems VTEX Alianza
│   │   └── cliente_vtex.py         # Cliente paginado y orquestador
│   ├── alianza.py                  # Scraper API pública VTEX de Bodegas Alianza por término
│   ├── scrapear_todo.py            # Orquestador general del ciclo completo de scraping multitienda
│   ├── historial.py                # Gestor y consultor forense del historial de precios y semáforo
│   ├── red_http.py                 # Cliente HTTP resiliente con reintentos exponenciales y jitter (H20)
│   ├── io_archivos.py              # Guardado atómico de CSV/JSON y métricas de scraping (H10)
│   ├── logger.py                   # Sistema centralizado de logging con consola y archivo rotativo (H19)
│   ├── actualizar_dashboard_completo.py # Pipeline de consolidación, validación de esquema y orquestador (H41)
│   ├── generar_dashboard.py        # Ensamblador y generador del dashboard BI (Diseño Stitch Archival)
│   └── templates/                  # Arquitectura frontend modular (ensamblada en index.html)
│       ├── dashboard_template.html # Layout maestro con directivas @include y @datauri
│       ├── assets/                 # Emblemas SVG, favicon y logos del sistema de diseño
│       │   ├── agave_emblema.svg
│       │   ├── apple-touch-icon.png
│       │   ├── favicon.svg
│       │   └── logo_sello.svg
│       ├── css/
│       │   └── styles.css          # Variables y utilidades semánticas del sistema de diseño Stitch
│       ├── partials/               # Vistas modulares HTML por sección y pestaña
│       │   ├── header_y_nav.html
│       │   ├── tab_rankings.html
│       │   ├── tab_versus.html
│       │   ├── tab_carrito.html
│       │   ├── tab_matriz.html
│       │   └── footer_y_modales.html
│       └── js/                     # Módulos JavaScript desacoplados por responsabilidad
│           ├── estado_y_utilidades.js
│           ├── modales_y_subtipos.js
│           ├── carrito_y_canastas.js
│           ├── navegacion_y_catalogo.js
│           └── versus_y_arranque.js
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Fixtures y generadores de DataFrames sintéticos
│   ├── fixtures/                   # Respuestas congeladas JSON/HTML para tests de regresión
│   ├── test_analizador.py          # Pruebas de métricas, rankings, cross-tienda y CLI ad-hoc (50 pruebas)
│   ├── test_arbitraje_y_archivos.py# Pruebas de comparativas cross-tienda, esquema y guardado atómico (14 pruebas)
│   ├── test_clasificacion.py       # Pruebas de clasificación NOM, extracción de volumen y sincronización (91 pruebas)
│   ├── test_dashboard_smoke.py     # Smoke tests de estructura de index.html, módulos y accesibilidad (12 pruebas)
│   ├── test_dashboard_y_consolidador.py # Pruebas del generador y consolidador maestro (19 pruebas)
│   ├── test_historial.py           # Pruebas de registro, deduplicación y semáforo histórico (9 pruebas)
│   ├── test_red_http_y_empaquetado.py # Pruebas de HTTP backoff, mocks, empaquetado y entry points (22 pruebas)
│   ├── test_regression_fixtures.py # Pruebas de parseo con fixtures congelados contra regresiones (6 pruebas)
│   ├── test_scraper_selenium.py    # Pruebas del scraper asistido Selenium y detección de retos (23 pruebas)
│   ├── test_scrapers_adquisicion.py# Pruebas de scrapers de adquisición y normalización multi-tienda (20 pruebas)
│   └── test_walmart_sams_fixtures.py # Pruebas exhaustivas de Walmart/Sam's con fixtures congelados (9 pruebas)
├── pyproject.toml                  # Empaquetado estándar pip, entry points CLI y metadatos (H13, H50)
├── requirements.txt                # Dependencias base de producción con cotas fijadas
├── requirements-dev.txt            # Dependencias de desarrollo y testing (pytest, ruff)
├── requirements.lock               # Lockfile determinista con dependencias exactas y hashes (H48)
├── index.html                      # Dashboard interactivo autocontenido desplegado para GitHub Pages
└── README.md                       # Documentación y guía de ejecución
```

---

## Requisitos e Instalación

Entorno probado: **Linux Fedora 44 (Plasma) / Python 3.12+ / Google Chrome o Firefox**.

1. **Crear y activar el entorno virtual:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Instalación determinista (recomendada con lockfile):**
   ```bash
   pip install -r requirements.lock
   pip install -e . --no-build-isolation --no-deps
   ```

3. **Instalación flexible (producción o desarrollo):**
   ```bash
   # Solo producción
   pip install -r requirements.txt
   pip install -e . --no-build-isolation --no-deps

   # Con herramientas de desarrollo (pytest, ruff)
   pip install -e ".[dev]"
   ```

---

## Pipeline de Datos y Ejecución

El flujo completo del proyecto consta de 3 fases desacopladas y observables:

```
[1. Recolección] Scrapers multitienda (Alianza, Sam's, Costco, Walmart, Chedraui, Soriana)
       ↓ (HTTP con reintentos exponenciales y jitter en red_http.py)
[2. Consolidación] Clasificación estricta NOM, validación de esquema y cross-tienda
       ↓ (Escritura atómica en io_archivos.py y logging estructurado)
[3. Dashboard BI] Ensamblado modular y generación reactiva de index.html (publicado en GitHub Pages)
```

### 1. Ejecutar el Pipeline Completo

El proyecto expone comandos de consola estándar mediante `[project.scripts]` (H50):

```bash
# Paso 0 (Opcional): Ejecutar ciclo completo de adquisición multitienda (Scraping 6 tiendas + ETL + Dashboard)
cantina-scrapear
# (o alternativamente: python src/scrapear_todo.py)

# Paso A: Consolidar y clasificar datasets de las 6 tiendas (ETL principal para dashboard)
cantina-consolidar
# (o alternativamente: python src/actualizar_dashboard_completo.py)

# Paso B: Ensamblar plantillas modulares y sincronizar el Dashboard interactivo web
cantina-dashboard
# (o alternativamente: python src/generar_dashboard.py)

# Paso C: Auditoría ad-hoc y reporte de rankings en terminal para cualquier archivo CSV
cantina-analizar --entrada data/bebidas_verificadas.csv --salida data/reporte_ranking.csv
# (o alternativamente: python -m src.analizador --entrada <ruta_csv>)

# Paso D: Consulta y gestión del historial de precios y semáforo anti-inflación
cantina-historial --resumen
# (o consultar una botella: cantina-historial --producto "Don Julio 70")
```

> **Diferencia entre comandos:**
> - `cantina-scrapear` orquesta la extracción automática de catálogos en las 6 tiendas en vivo (Bodegas Alianza, Chedraui, Sam's, Walmart, Soriana, Costco), ejecuta la normalización y consolida el dashboard en una sola invocación.
> - `cantina-consolidar` ejecuta el flujo integral de ETL multi-tienda sobre los CSVs ya descargados: une los 6 catálogos fuente, aplica clasificación estricta NOM, detecta duplicados, enriquece con comparativas cross-tienda y genera `data/dashboard_data.json` junto a los catálogos unificados.
> - `cantina-dashboard` compila la plantilla modular HTML y módulos JS reactivos con los datos auditados en `index.html`.
> - `cantina-analizar` es una herramienta CLI de inspección ad-hoc para evaluar cualquier dataset tabular de forma independiente: audita datos faltantes y duplicados, calcula métricas unitarias e imprime una tabla de rankings por categoría directamente en la terminal.
> - `cantina-historial` consulta la evolución de precios a lo largo del tiempo, reconstruye snapshots históricos y clasifica el semáforo anti-inflación (`minimo_historico`, `descuento_inflado`, etc.).

### 2. Ejecutar la Suite de Pruebas Unitarias
El proyecto cuenta con **275 pruebas automatizadas** organizadas en módulos de testing con una cobertura del **83%** (`tests/`), que cubren clasificación NOM, normalización de multipacks (`Pack 6`, `Pack x 3`, `(8 Bot)`, etc.), normalización de medidas (`ml` y `L`), métricas por litro, exclusión explícita de outliers de lujo, umbrales centralizados de presupuesto, arbitraje cross-tienda no-stale, validación de esquema y cordura (volumen, ABV, precios), selectores interactivos en cascada, escritura atómica, cliente HTTP con backoff y Retry-After, detección y aborto de retos WAF en nodriver CDP, parseo con mocks/fixtures congelados, entry points CLI, arquitectura modular de plantillas, accesibilidad WCAG y persistencia de estado:

```bash
pytest
```

### 3. Ejecutar Scrapers Específicos

- **Scraper Multitienda por Lote (Sam's Club, Costco, Walmart, Chedraui, Soriana):**
  Motor de adquisición bajo demanda que consulta APIs y SSR de las cadenas comerciales para actualizar los CSVs fuente de entrada con soporte para parametrización granular:
  ```bash
  # Ejecutar todas las tiendas (por defecto)
  python -m src.scraper_multitienda

  # Filtrar tiendas específicas mediante argumento CLI
  python -m src.scraper_multitienda --tiendas chedraui,sams
  python -m src.scraper_multitienda --tiendas walmart --walmart-cdp
  python -m src.scraper_multitienda --tiendas sams --forzar-selenium --headless
  ```
  *(Parámetros soportados: `--tiendas`, `--forzar-selenium`, `--sin-fallback-selenium`, `--headless`, `--walmart-cdp`, `--pausa`).*

- **Bodegas Alianza (Catálogo exhaustivo o búsqueda por términos):**
  ```bash
  python -m src.scraper_catalogo_completo
  python src/alianza.py --terminos "1800" "Herradura" "Amarás" "Red Label" "Jack Daniel" --salida data/scraped_alianza.csv
  ```

- **Scraper Asistido con Selenium y nodriver CDP (Sam's Club / Walmart / SPAs):**
  Permite navegación secuencial con hidratación de JavaScript o recolección CDP ultra-rápida con detección de retos:
  ```bash
  python -m src.scraper_selenium --urls "https://www.sams.com.mx" --tienda "Sam's Club" --salida data/scraped_selenium.csv
  ```
  *(Para aislar perfiles de Chrome se puede configurar la variable de entorno `CHROME_USER_DATA_DIR` o pasar un directorio dedicado).*

---

## Robustez, Observabilidad y Gobernanza de Datos

- **Cliente HTTP Resiliente y Anti-WAF (`src/red_http.py`):** Todas las descargas gestionan errores transitorios de red y límites de tasa (`HTTP 429`, `500`, `502`, `503`, `504`) mediante reintentos con retraso exponencial, fluctuación estocástica (*full jitter*) y respeto estricto del encabezado `Retry-After`. Se incluye sanitización de parámetros sensibles y secretos en URLs para evitar fugas en logs de CI/CD.
- **Detección de Retos WAF y Abort Flag en CDP (`src/scraper_selenium/nodriver_cdp.py`):** Monitoreo activo de URLs bloqueadas (`/blocked`, captchas, challenges de PerimeterX/Cloudflare). Ante un bloqueo, se levanta la excepción `BloqueoWAF` y se activa un `asyncio.Event` de aborto que cancela de inmediato la recolección en paralelo, evitando quemar IPs o proxies. Cada pestaña opera bajo un timeout estricto de 20s.
- **Integridad de Datos y Arbitraje Anti-Phantom (`src/analizador/`):**
  - **Filtros de cordura:** validación de rangos biológicos y comerciales ($100 \le \text{ml} \le 10,000$, $0 < \text{ABV} \le 100\%$, precios entre $\$50.00$ y $\$1,000,000.00$). Anomalías de ABV o precios absurdos son excluidas de `datos_validos`.
  - **Fail-closed freshness:** registros con fecha nula o no parseable reciben $9999.0$ días de antigüedad y son marcados como `es_stale = True`.
  - **Arbitraje Real:** el cálculo de ahorro cross-tienda descarta automáticamente ofertas stale y requiere un mínimo de 2 tiendas frescas y activas para publicar recomendaciones de ahorro, evitando ahorros fantasma.
  - **URLs Seguras:** validación estricta de dominios permitidos por tienda (`_url_segura`) con rechazo por omisión (fail-closed) para prevenir SSRF o inyecciones de enlaces arbitrarios.
- **Logging Estructurado Centralizado (`src/logger.py`):** Los registros emiten formato limpio y legible con emojis a consola (`sys.stdout`) y bitácora rotativa persistente de hasta 2 MB en `logs/cantina_familiar.log`.
- **Escritura Atómica (`src/io_archivos.py`):** La persistencia de CSV y JSON se realiza en archivos temporales con reemplazo atómico atado al sistema de archivos, impidiendo corrupción ante interrupciones.
- **Política de Scraping Ético (`docs/politica_scraping.md`):** Regula el cumplimiento de `robots.txt`, la tasa de peticiones y el carácter educativo no comercial del proyecto.

---

## Columnas del Esquema CSV

| Columna | Descripción |
| :--- | :--- |
| `tienda` | Comercio donde se cotiza (Bodegas Alianza, Sam's Club, Costco, Walmart, Chedraui, Soriana). |
| `producto` | Nombre comercial completo de la etiqueta. |
| `marca` | Marca de la bebida. |
| `categoria` | Tequila, Mezcal, Whisky, Licor de Whisky, Vino. |
| `subcategoria` | Añejo Tradicional, Añejo Cristalino, Reposado, Blended Scotch, Silvestre, etc. |
| `clase` | Clase normativa (Añejo, Reposado, Joven, no_aplica). |
| `tipo_mezcal` | Artesanal, Ancestral, Industrial, no_aplica. |
| `especie_agave` | Tequilana Weber, Espadín, Tobalá, Cupreata, Ensamble, no_aplica. |
| `productor` | Razón social o destilería / palenque productor con NOM. |
| `sello_regulador`| `sí`, `no`, o `no verificado`. |
| `ml` | Volumen numérico en mililitros (ej. 700, 750, 1000, 1750, 4200). |
| `abv` | Graduación alcohólica en porcentaje en volumen (ej. 35.0, 38.0, 40.0, 41.0). |
| `precio_regular` | Precio de lista o regular en moneda nacional ($ MXN). |
| `precio_promo` | Precio con descuento directo o precio de socio ($ MXN). |
| `unidades_promo` | Cantidad de unidades de la oferta (ej. 1 para unitario, 3 para un 3x2). |
| `precio_total_promo` | Costo total pagado por el paquete multiunidad. |
| `condiciones` | Tipo de oferta (ej. Descuento directo Aniversario Web, Precio regular). |
| `disponibilidad` | `disponible`, `agotado`, o `stock_limitado`. |
| `url` | Enlace directo a la página de consulta. |
| `fecha_consulta` | Fecha y hora de verificación (YYYY-MM-DD HH:MM). |
| `fuente` | API oficial Bodegas Alianza, portal sams.com.mx, etc. |
| `confianza` | `Confirmado`, `Estimado`, o `Hipótesis` (según Regla de Rigor 2). |
