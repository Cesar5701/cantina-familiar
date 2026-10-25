# Cantina Familiar — Sistema de Decisión de Compra y Arbitraje Multitienda

Herramienta de optimización, comparativa multitienda y auditoría de precios por litro para compras de vinos y destilados en seis cadenas comerciales de México.

---

## Estructura del Proyecto

```
Cantina Familiar/
├── data/
│   ├── bebidas_verificadas.csv     # Dataset auditado con 32 etiquetas confirmadas
│   ├── scraped_*.csv               # Catálogos fuente por tienda (Alianza, Chedraui, Costco, Sam's, Soriana, Walmart)
│   ├── catalogo_completo_consolidado.csv # Catálogo unificado y normalizado
│   ├── ranking_completo_general.csv# Ranking filtrado libre de outliers de lujo
│   ├── dashboard_data.json         # JSON optimizado para el dashboard interactivo (827 registros)
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
│   ├── scraper_selenium/           # Paquete de scraping SPA asistido (Human-in-the-Loop)
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── driver_y_waf.py         # Inicialización Chrome/Firefox y detección de retos WAF/CAPTCHA
│   │   ├── parsers_dom.py          # Extracción híbrida JSON-LD, __NEXT_DATA__ y tarjetas DOM
│   │   └── navegador_cli.py        # Navegación secuencial con hidratación y CLI
│   ├── scraper_catalogo_completo/  # Paquete de extracción exhaustiva paginada para Bodegas Alianza
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── clasificador_alianza.py # Clasificación de ítems VTEX Alianza
│   │   └── cliente_vtex.py         # Cliente paginado y orquestador
│   ├── scraper_alianza.py          # Scraper API pública VTEX de Bodegas Alianza por término
│   ├── http_utils.py               # Cliente HTTP resiliente con reintentos exponenciales y jitter (H20)
│   ├── io_utils.py                 # Guardado atómico de CSV/JSON y métricas de scraping (H10)
│   ├── logger.py                   # Sistema centralizado de logging con consola y archivo rotativo (H19)
│   ├── actualizar_dashboard_completo.py # Pipeline de consolidación, validación de esquema y orquestador (H41)
│   ├── generar_dashboard_v4.py     # Ensamblador y generador del dashboard BI (Diseño Stitch Archival)
│   └── templates/                  # Arquitectura frontend modular (ensamblada en index.html)
│       ├── dashboard_template.html # Layout maestro con directivas @include
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
│           ├── 01_estado_y_utilidades.js
│           ├── 02_modales_y_subtipos.js
│           ├── 03_carrito_y_canastas.js
│           ├── 04_navegacion_y_catalogo.js
│           └── 05_versus_y_arranque.js
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Fixtures y generadores de DataFrames sintéticos
│   ├── test_analizador.py          # Pruebas de métricas, rankings, cross-tienda y CLI ad-hoc (45 pruebas)
│   ├── test_clasificacion.py       # Pruebas de clasificación NOM, extracción de volumen y sincronización (79 pruebas)
│   ├── test_dashboard_smoke.py     # Smoke tests de estructura de index.html, módulos y accesibilidad (6 pruebas)
│   ├── test_dashboard_y_consolidador.py # Pruebas del generador y consolidador maestro (16 pruebas)
│   ├── test_scraper_selenium.py    # Pruebas del scraper asistido Selenium y detección de retos (19 pruebas)
│   ├── test_scrapers_adquisicion.py# Pruebas de scrapers de adquisición y normalización multi-tienda (10 pruebas)
│   ├── test_sprint2.py             # Pruebas de comparativas cross-tienda, esquema y guardado atómico (11 pruebas)
│   └── test_sprint3.py             # Pruebas de HTTP backoff, mocks, empaquetado y entry points (13 pruebas)
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
       ↓ (HTTP con reintentos exponenciales y jitter en http_utils.py)
[2. Consolidación] Clasificación estricta NOM, validación de esquema y cross-tienda
       ↓ (Escritura atómica en io_utils.py y logging estructurado)
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
# (o alternativamente: python src/generar_dashboard_v4.py)

# Paso C: Auditoría ad-hoc y reporte de rankings en terminal para cualquier archivo CSV
cantina-analizar --entrada data/bebidas_verificadas.csv --salida data/reporte_ranking.csv
# (o alternativamente: python -m src.analizador --entrada <ruta_csv>)
```

> **Diferencia entre comandos:**
> - `cantina-scrapear` orquesta la extracción automática de catálogos en las 6 tiendas en vivo (Bodegas Alianza, Chedraui, Sam's, Walmart, Soriana, Costco), ejecuta la normalización y consolida el dashboard en una sola invocación.
> - `cantina-consolidar` ejecuta el flujo integral de ETL multi-tienda sobre los CSVs ya descargados: une los 6 catálogos fuente, aplica clasificación estricta NOM, detecta duplicados, enriquece con comparativas cross-tienda y genera `data/dashboard_data.json` junto a los catálogos unificados.
> - `cantina-analizar` es una herramienta CLI de inspección ad-hoc para evaluar cualquier dataset tabular de forma independiente: audita datos faltantes y duplicados, calcula métricas unitarias e imprime una tabla de rankings por categoría directamente en la terminal.

### 2. Ejecutar la Suite de Pruebas Unitarias
El proyecto cuenta con **200 pruebas automatizadas** organizadas en 8 módulos con una cobertura superior al **83%** (`tests/`), que cubren clasificación NOM, normalización de multipacks (`Pack 6`, `Pack x 3`, `(8 Bot)`, etc.), normalización de medidas (`ml` y `L`), métricas por litro, exclusión explícita de outliers de lujo, umbrales centralizados de presupuesto, arbitraje cross-tienda, validación de esquema, selectores interactivos en cascada, escritura atómica, cliente HTTP con backoff, parseo con mocks, entry points CLI, arquitectura modular de plantillas, accesibilidad WCAG y persistencia de estado:

```bash
pytest
```

### 3. Ejecutar Scrapers Específicos

- **Scraper Multitienda por Lote (Sam's Club, Costco, Walmart, Chedraui, Soriana):**
  Motor de adquisición bajo demanda que consulta APIs y SSR de las cadenas comerciales para actualizar los CSVs fuente de entrada:
  ```bash
  python -m src.scraper_multitienda
  ```
  *(Genera `data/scraped_chedraui.csv`, `data/scraped_sams.csv`, `data/scraped_walmart.csv`, `data/scraped_soriana.csv` y `data/scraped_costco.csv`).*

- **Bodegas Alianza (Catálogo exhaustivo o búsqueda por términos):**
  ```bash
  python -m src.scraper_catalogo_completo
  python src/scraper_alianza.py --terminos "1800" "Herradura" "Amarás" "Red Label" "Jack Daniel" --salida data/scraped_alianza.csv
  ```

- **Scraper Asistido con Selenium (Sam's Club / SPAs):**
  Abre un navegador real (Chrome por defecto, o `--navegador firefox`) para permitir que el JavaScript hidrate precios y existencias en modo Human-in-the-Loop:
  ```bash
  python -m src.scraper_selenium --urls "https://www.sams.com.mx" --tienda "Sam's Club" --salida data/scraped_selenium.csv
  ```
  *(Para ejecutar en modo sin cabeza usar la bandera `--headless`).*

---

## Robustez, Observabilidad y Ética

- **Cliente HTTP Resiliente (`src/http_utils.py`):** Todas las descargas gestionan errores transitorios de red y límites de tasa (`HTTP 429`, `500`, `502`, `503`, `504`) mediante reintentos con retraso exponencial y fluctuación estocástica (*full jitter*).
- **Logging Estructurado Centralizado (`src/logger.py`):** Los registros emiten formato limpio y legible con emojis a consola (`sys.stdout`) y bitácora rotativa persistente de hasta 2 MB en `logs/cantina_familiar.log`.
- **Escritura Atómica (`src/io_utils.py`):** La persistencia de CSV y JSON se realiza en archivos temporales con reemplazo atómico atado al sistema de archivos, impidiendo corrupción ante interrupciones.
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
