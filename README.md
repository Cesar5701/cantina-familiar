# Cantina Familiar — Sistema de Apoyo a la Decisión de Compra Navideña

Herramienta de optimización y auditoría de precios para compras familiares de bebidas alcohólicas (Navidad 2026, San Pedro Xalcaltzinco, Tepeyanco, Tlaxcala).

---

## Estructura del Proyecto

```
Cantina Familiar/
├── data/
│   ├── bebidas_verificadas.csv     # Dataset auditado con 32 etiquetas confirmadas
│   ├── scraped_*.csv               # Catálogos fuente por tienda (Alianza, Chedraui, Sam's, Soriana, Walmart)
│   ├── catalogo_completo_consolidado.csv # Catálogo unificado y normalizado (1,004 registros)
│   ├── ranking_completo_general.csv# Ranking filtrado libre de outliers de lujo (866 registros)
│   ├── dashboard_data.json         # JSON optimizado para el dashboard interactivo (775 registros)
│   └── reporte_ranking.csv         # Salida generada con métricas por litro y rankings
├── docs/
│   ├── politica_scraping.md        # Política de Scraping Ético y Gobernanza de Datos (H17)
│   └── archivo/                    # Archivo histórico de auditorías técnicas (V1 a V4)
├── logs/
│   └── cantina_familiar.log        # Registro estructurado rotativo (H19)
├── src/
│   ├── __init__.py
│   ├── clasificacion.py            # Módulo unificado de reglas NOM-006 / NOM-070, volumen, precios y sincronización (H1, H2, H6, H41)
│   ├── http_utils.py               # Cliente HTTP resiliente con reintentos exponenciales y jitter (H20)
│   ├── io_utils.py                 # Guardado atómico de CSV/JSON y métricas de scraping (H10)
│   ├── logger.py                   # Sistema centralizado de logging con consola y archivo rotativo (H19)
│   ├── scraper_alianza.py          # Scraper API pública VTEX de Bodegas Alianza por término
│   ├── scraper_catalogo_completo.py# Scraper exhaustivo paginado para Bodegas Alianza
│   ├── scraper_multitienda.py      # Scraper multitienda (Sam's Club, Walmart, Chedraui, Soriana)
│   ├── scraper_selenium.py         # Scraper SPA asistido (Human-in-the-Loop para retos WAF)
│   ├── analizador.py               # Motor de análisis en pandas (auditoría, métricas, rankings, cross-tienda y filtros H41)
│   ├── actualizar_dashboard_completo.py # Pipeline de consolidación, validación de esquema y orquestador (H41)
│   ├── generar_dashboard_v4.py     # Generador de dashboard BI (Material 3 Expressive)
│   └── templates/
│       └── dashboard_template.html # Plantilla HTML+CSS+JS reactiva del dashboard
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Fixtures y generadores de DataFrames sintéticos
│   ├── test_analizador.py          # Pruebas de métricas, rankings, cross-tienda y filtro de presupuesto (43 pruebas)
│   ├── test_clasificacion.py       # Pruebas de clasificación NOM, extracción de volumen y sincronización (79 pruebas)
│   ├── test_dashboard_smoke.py     # Smoke tests de estructura de index.html y carga de dependencias (4 pruebas)
│   ├── test_dashboard_y_consolidador.py # Pruebas del generador y consolidador maestro (15 pruebas)
│   ├── test_scraper_selenium.py    # Pruebas del scraper asistido Selenium y detección de retos (19 pruebas)
│   ├── test_scrapers_adquisicion.py# Pruebas de scrapers de adquisición y normalización multi-tienda (10 pruebas)
│   ├── test_sprint2.py             # Pruebas de comparativas cross-tienda, esquema y guardado atómico (11 pruebas)
│   └── test_sprint3.py             # Pruebas de HTTP backoff, mocks, empaquetado y entry points (13 pruebas)
├── pyproject.toml                  # Empaquetado estándar pip, entry points CLI y metadatos (H13, H50)
├── requirements.txt                # Dependencias base de producción con cotas fijadas
├── requirements-dev.txt            # Dependencias de desarrollo y testing (pytest, ruff)
├── requirements.lock               # Lockfile determinista con dependencias exactas y hashes (H48)
├── index.html                      # Dashboard interactivo desplegado para GitHub Pages
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
[1. Recolección] Scrapers multitienda (Alianza, Sam's, Walmart, Chedraui, Soriana)
       ↓ (HTTP con reintentos exponenciales y jitter en http_utils.py)
[2. Consolidación] Clasificación estricta NOM, validación de esquema y cross-tienda
       ↓ (Escritura atómica en io_utils.py y logging estructurado)
[3. Dashboard BI] Generación reactiva de index.html (autocontenido y publicado en GitHub Pages)
```

### 1. Ejecutar el Pipeline Completo

El proyecto expone comandos de consola estándar mediante `[project.scripts]` (H50):

```bash
# Paso A: Consolidar y clasificar datasets de las 5 tiendas
cantina-consolidar
# (o alternativamente: python src/actualizar_dashboard_completo.py)

# Paso B: Generar y sincronizar el Dashboard interactivo
cantina-dashboard
# (o alternativamente: python src/generar_dashboard_v4.py)

# Paso C: Ejecutar auditoría y rankings de terminal
cantina-analizar --entrada data/bebidas_verificadas.csv
```

### 2. Ejecutar la Suite de Pruebas Unitarias
El proyecto cuenta con **194 pruebas automatizadas** organizadas en 8 módulos con una cobertura superior al **80%** (`tests/`), que cubren clasificación NOM, normalización de multipacks (`Pack 6`, `Pack x 3`, `(8 Bot)`, etc.), normalización de medidas (`ml` y `L`), métricas por litro, exclusión explícita de outliers de lujo, umbrales centralizados de presupuesto, arbitraje cross-tienda, validación de esquema, selectores interactivos en cascada, escritura atómica, cliente HTTP con backoff, parseo con mocks, entry points CLI e higiene de dependencias:

```bash
pytest
```

### 3. Ejecutar Scrapers Específicos

- **Bodegas Alianza (API VTEX oficial con reintentos y logging):**
  ```bash
  python src/scraper_alianza.py --terminos "1800" "Herradura" "Amarás" "Red Label" "Jack Daniel" --salida data/scraped_alianza.csv
  ```

- **Scraper Asistido con Selenium (Sam's Club / SPAs):**
  Abre un navegador real (Chrome por defecto, o `--navegador firefox`) para permitir que el JavaScript hidrate precios y existencias en modo Human-in-the-Loop:
  ```bash
  python src/scraper_selenium.py --urls "https://www.sams.com.mx" --tienda "Sam's Club" --salida data/scraped_selenium.csv
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
| `tienda` | Comercio donde se cotiza (ej. Bodegas Alianza, Sam's Club, Walmart, Chedraui, Soriana). |
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
