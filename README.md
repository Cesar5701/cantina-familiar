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
│   ├── infraestructura/            # Utilidades transversales desacopladas de dominio
│   │   ├── __init__.py
│   │   ├── cliente_http.py         # Cliente HTTP resiliente con reintentos exponenciales y jitter (H20)
│   │   ├── almacenamiento_csv.py   # Guardado atómico de CSV/JSON y métricas de scraping (H10)
│   │   └── registro_eventos.py     # Sistema centralizado de logging con consola y archivo rotativo (H19)
│   ├── catalogo/                   # Reglas de negocio, normalización NOM, arbitraje y series históricas
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── constantes.py           # Vocabularios normativos y umbrales centralizados (H32)
│   │   ├── denominacion_nom.py     # Clasificación estricta NOM-006 / NOM-070 y especies de agave
│   │   ├── detector_volumen.py     # Extracción de ml/L, multipacks y parseo de precios (H2, H6)
│   │   ├── filtros_mercancia.py    # Exclusión de mercancía y sincronización de catálogo (H41)
│   │   ├── normalizacion_texto.py  # Reglas declarativas de normalización y detección de paquetes (H38)
│   │   ├── esquema_y_auditoria.py  # Validación de esquema, rangos y datos faltantes (H9)
│   │   ├── deteccion_anomalias.py  # Cálculo vectorial $/L, outliers de lujo y filtro de presupuesto
│   │   ├── arbitraje_precios.py    # Deduplicación y arbitraje cross-tienda (H8, H35, H40)
│   │   ├── campanas_promocionales.py # Detección automática de campañas comerciales y vigencias
│   │   ├── rankings_cli.py         # Rankings por categoría comparable y CLI ad-hoc
│   │   └── series_historicas.py    # Gestor y consultor forense del historial de precios y semáforo
│   ├── adquisicion/                # Conectores y clientes de extracción unificados por fuente
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── walmart.py              # Scraper SSR __NEXT_DATA__ Walmart y Sam's Club
│   │   ├── costco.py               # Scraper API REST OCC v2 Costco México
│   │   ├── chedraui.py             # Scraper API VTEX Chedraui
│   │   ├── soriana.py              # Scraper SFCC Soriana
│   │   ├── alianza_vtex.py         # Scraper API pública VTEX de Bodegas Alianza por término
│   │   ├── alianza_paginado.py     # Cliente paginado exhaustivo VTEX Bodegas Alianza
│   │   ├── clasificador_alianza.py # Clasificación de ítems VTEX Alianza
│   │   ├── normalizador_tiendas.py # Normalización y validación de dominios permitidos
│   │   ├── despachador_cli.py      # Despachador de extracción por lote y CLI
│   │   ├── navegador_cdp.py        # Conector asíncrono CDP indetectable con abort flag y rate limiting
│   │   ├── controlador_waf.py      # Inicialización de navegador y detección de retos WAF/CAPTCHA
│   │   ├── selectores_dom.py       # Extracción híbrida JSON-LD, __NEXT_DATA__ y tarjetas DOM
│   │   └── hidratacion_spa.py      # Navegación secuencial con hidratación de JavaScript
│   ├── interfaz/                   # Compilador y plantillas modulares del Dashboard BI
│   │   ├── __init__.py
│   │   ├── compilador_web.py       # Ensamblador y generador del dashboard BI (Diseño Stitch Archival)
│   │   └── plantillas/             # Arquitectura frontend modular (ensamblada en index.html)
│   │       ├── layout_principal.html # Layout maestro con directivas @include y @datauri
│   │       ├── assets/             # Emblemas SVG, favicon y logos del sistema de diseño
│   │       │   ├── agave_emblema.svg
│   │       │   ├── apple-touch-icon.png
│   │       │   ├── favicon.svg
│   │       │   └── logo_sello.svg
│   │       ├── css/
│   │       │   └── estilos.css     # Variables y utilidades semánticas del sistema de diseño Stitch
│   │       ├── secciones/          # Vistas modulares HTML por sección y pestaña
│   │       │   ├── cabecera_y_navegacion.html
│   │       │   ├── vista_rankings.html
│   │       │   ├── vista_versus.html
│   │       │   ├── vista_carrito.html
│   │       │   ├── vista_matriz.html
│   │       │   └── pie_y_modales.html
│   │       └── js/                 # Módulos JavaScript desacoplados por responsabilidad
│   │           ├── estado_y_utilidades.js
│   │           ├── modales_y_subtipos.js
│   │           ├── carrito_y_canastas.js
│   │           ├── navegacion_y_catalogo.js
│   │           └── versus_y_arranque.js
│   ├── orquestador.py              # Punto de entrada del ciclo completo de adquisición multitienda
│   └── sincronizador.py            # Punto de entrada de consolidación ETL y validación NOM (H41)
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Fixtures y generadores de DataFrames sintéticos
│   ├── fixtures/                   # Respuestas congeladas JSON/HTML para tests de regresión
│   ├── test_denominacion_y_volumen.py # Pruebas de denominación NOM, detector de volumen y sincronización (91 pruebas)
│   ├── test_motor_catalogo.py      # Pruebas de métricas, rankings, normalización y CLI de catálogo (50 pruebas)
│   ├── test_arbitraje_y_almacenamiento.py # Pruebas de arbitraje cross-tienda, esquema y guardado atómico (14 pruebas)
│   ├── test_series_historicas.py   # Pruebas de registro, deduplicación y semáforo histórico (9 pruebas)
│   ├── test_cliente_http_y_empaquetado.py # Pruebas de cliente HTTP, mocks, empaquetado y entry points (22 pruebas)
│   ├── test_adquisicion_tiendas.py # Pruebas de adquisición y normalización por tienda (20 pruebas)
│   ├── test_adquisicion_walmart.py # Pruebas exhaustivas de Walmart/Sam's con fixtures congelados (9 pruebas)
│   ├── test_adquisicion_navegador.py # Pruebas de navegación CDP/WAF y selectores DOM (23 pruebas)
│   ├── test_regresion_fixtures.py  # Pruebas de parseo con fixtures congelados contra regresiones (6 pruebas)
│   ├── test_interfaz_web.py        # Smoke tests de estructura de index.html, módulos y accesibilidad (12 pruebas)
│   └── test_compilador_y_sincronizador.py # Pruebas del compilador web y sincronizador ETL (19 pruebas)
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
[1. Adquisición] Conectores de tiendas (src/adquisicion/)
       ↓ (HTTP con reintentos exponenciales y jitter en src/infraestructura/cliente_http.py)
[2. Sincronización] Clasificación estricta NOM, validación de esquema y arbitraje (src/catalogo/)
       ↓ (Escritura atómica en src/infraestructura/almacenamiento_csv.py y logging estructurado)
[3. Interfaz Web] Compilación modular y generación reactiva de index.html (src/interfaz/compilador_web.py)
```

### 1. Ejecutar el Pipeline Completo

El proyecto expone comandos de consola estándar mediante `[project.scripts]` (H50):

```bash
# Paso 0 (Opcional): Ejecutar ciclo completo de adquisición (Scraping 6 tiendas + ETL + Dashboard)
cantina-scrapear
# (o alternativamente: python src/orquestador.py)

# Paso A: Consolidar y clasificar datasets de las 6 tiendas (ETL principal para dashboard)
cantina-consolidar
# (o alternativamente: python src/sincronizador.py)

# Paso B: Ensamblar plantillas modulares y sincronizar el Dashboard interactivo web
cantina-dashboard
# (o alternativamente: python src/interfaz/compilador_web.py)

# Paso C: Auditoría ad-hoc y reporte de rankings en terminal para cualquier archivo CSV
cantina-analizar --entrada data/bebidas_verificadas.csv --salida data/reporte_ranking.csv
# (o alternativamente: python -m src.catalogo --entrada <ruta_csv>)

# Paso D: Consulta y gestión del historial de precios y semáforo anti-inflación
cantina-historial --resumen
# (o consultar una botella: cantina-historial --producto "Don Julio 70")
```

> **Diferencia entre comandos:**
> - `cantina-scrapear` (`src/orquestador.py`) orquesta la extracción automática de catálogos en las 6 tiendas en vivo (Bodegas Alianza, Chedraui, Sam's, Walmart, Soriana, Costco), ejecuta la normalización y consolida el dashboard en una sola invocación.
> - `cantina-consolidar` (`src/sincronizador.py`) ejecuta el flujo integral de ETL sobre los CSVs ya descargados: une los 6 catálogos fuente, aplica clasificación estricta NOM, detecta duplicados, enriquece con comparativas cross-tienda y genera `data/dashboard_data.json` junto a los catálogos unificados.
> - `cantina-dashboard` (`src/interfaz/compilador_web.py`) compila la plantilla modular HTML y módulos JS reactivos con los datos auditados en `index.html`.
> - `cantina-analizar` (`src/catalogo/`) es una herramienta CLI de inspección ad-hoc para evaluar cualquier dataset tabular de forma independiente: audita datos faltantes y duplicados, calcula métricas unitarias e imprime una tabla de rankings por categoría directamente en la terminal.
> - `cantina-historial` (`src/catalogo/series_historicas.py`) consulta la evolución de precios a lo largo del tiempo, reconstruye snapshots históricos y clasifica el semáforo anti-inflación (`minimo_historico`, `descuento_inflado`, etc.).

### 2. Ejecutar la Suite de Pruebas Unitarias
El proyecto cuenta con **275 pruebas automatizadas** organizadas en módulos de testing espejo con una cobertura del **83%** (`tests/`), que cubren clasificación NOM, normalización de multipacks (`Pack 6`, `Pack x 3`, `(8 Bot)`, etc.), normalización de medidas (`ml` y `L`), métricas por litro, exclusión explícita de outliers de lujo, umbrales centralizados de presupuesto, arbitraje cross-tienda no-stale, validación de esquema y cordura (volumen, ABV, precios), selectores interactivos en cascada, escritura atómica, cliente HTTP con backoff y Retry-After, detección y aborto de retos WAF en nodriver CDP, parseo con mocks/fixtures congelados, entry points CLI, arquitectura modular de plantillas, accesibilidad WCAG y persistencia de estado:

```bash
pytest
```

### 3. Ejecutar Conectores de Adquisición Específicos

- **Despachador de Adquisición por Lote (Sam's Club, Costco, Walmart, Chedraui, Soriana):**
  Motor de adquisición bajo demanda que consulta APIs y SSR de las cadenas comerciales para actualizar los CSVs fuente de entrada con soporte para parametrización granular:
  ```bash
  # Ejecutar todas las tiendas (por defecto)
  python -m src.adquisicion

  # Filtrar tiendas específicas mediante argumento CLI
  python -m src.adquisicion --tiendas chedraui,sams
  python -m src.adquisicion --tiendas walmart --walmart-cdp
  python -m src.adquisicion --tiendas sams --forzar-selenium --headless
  ```
  *(Parámetros soportados: `--tiendas`, `--forzar-selenium`, `--sin-fallback-selenium`, `--headless`, `--walmart-cdp`, `--pausa`).*

- **Bodegas Alianza (Catálogo exhaustivo o búsqueda por términos):**
  ```bash
  python -m src.adquisicion.alianza_paginado
  python -m src.adquisicion.alianza_vtex --terminos "1800" "Herradura" "Amarás" "Red Label" "Jack Daniel" --salida data/scraped_alianza.csv
  ```

- **Navegación Asistida e Hidratación SPA / CDP (Sam's Club / Walmart / SPAs):**
  Permite navegación secuencial con hidratación de JavaScript o recolección CDP ultra-rápida con detección de retos:
  ```bash
  python -m src.adquisicion.hidratacion_spa --urls "https://www.sams.com.mx" --tienda "Sam's Club" --salida data/scraped_selenium.csv
  ```
  *(Para aislar perfiles de Chrome se puede configurar la variable de entorno `CHROME_USER_DATA_DIR` o pasar un directorio dedicado).*

---

## Robustez, Observabilidad y Gobernanza de Datos

- **Cliente HTTP Resiliente y Anti-WAF (`src/infraestructura/cliente_http.py`):** Todas las descargas gestionan errores transitorios de red y límites de tasa (`HTTP 429`, `500`, `502`, `503`, `504`) mediante reintentos con retraso exponencial, fluctuación estocástica (*full jitter*) y respeto estricto del encabezado `Retry-After`. Se incluye sanitización de parámetros sensibles y secretos en URLs para evitar fugas en logs de CI/CD.
- **Detección de Retos WAF y Abort Flag en CDP (`src/adquisicion/navegador_cdp.py`):** Monitoreo activo de URLs bloqueadas (`/blocked`, captchas, challenges de PerimeterX/Cloudflare). Ante un bloqueo, se levanta la excepción `BloqueoWAF` y se activa un `asyncio.Event` de aborto que cancela de inmediato la recolección en paralelo, evitando quemar IPs o proxies. Cada pestaña opera bajo un timeout estricto de 20s.
- **Integridad de Datos y Arbitraje Anti-Phantom (`src/catalogo/`):**
  - **Filtros de cordura:** validación de rangos biológicos y comerciales ($100 \le \text{ml} \le 10,000$, $0 < \text{ABV} \le 100\%$, precios entre $\$50.00$ y $\$1,000,000.00$). Anomalías de ABV o precios absurdos son excluidas de `datos_validos`.
  - **Fail-closed freshness:** registros con fecha nula o no parseable reciben $9999.0$ días de antigüedad y son marcados como `es_stale = True`.
  - **Arbitraje Real:** el cálculo de ahorro cross-tienda descarta automáticamente ofertas stale y requiere un mínimo de 2 tiendas frescas y activas para publicar recomendaciones de ahorro, evitando ahorros fantasma.
  - **URLs Seguras:** validación estricta de dominios permitidos por tienda (`_url_segura`) con rechazo por omisión (fail-closed) para prevenir SSRF o inyecciones de enlaces arbitrarios.
- **Logging Estructurado Centralizado (`src/infraestructura/registro_eventos.py`):** Los registros emiten formato limpio y legible con emojis a consola (`sys.stdout`) y bitácora rotativa persistente de hasta 2 MB en `logs/cantina_familiar.log`.
- **Escritura Atómica (`src/infraestructura/almacenamiento_csv.py`):** La persistencia de CSV y JSON se realiza en archivos temporales con reemplazo atómico atado al sistema de archivos, impidiendo corrupción ante interrupciones.
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
