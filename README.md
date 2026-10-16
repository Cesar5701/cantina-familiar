# Cantina Familiar — Sistema de Apoyo a la Decisión de Compra Navideña

Herramienta de optimización y auditoría de precios para compras familiares de bebidas alcohólicas (Navidad 2026, San Pedro Xalcaltzinco, Tepeyanco, Tlaxcala).

---

## Estructura del Proyecto

```
Cantina Familiar/
├── data/
│   ├── plantilla_bebidas.csv       # Esquema oficial con columnas obligatorias y ejemplos
│   ├── bebidas_verificadas.csv     # Dataset auditado con precios de Alianza, Sam's, etc.
│   └── reporte_ranking.csv         # Salida generada con métricas por litro y rankings
├── src/
│   ├── __init__.py
│   ├── clasificacion.py            # Módulo unificado de reglas NOM-006 / NOM-070, volumen y precios
│   ├── io_utils.py                 # Guardado atómico de CSV/JSON y métricas de scraping (H10)
│   ├── scraper_alianza.py          # Scraper ético para API pública VTEX de Bodegas Alianza
│   ├── scraper_catalogo_completo.py# Scraper exhaustivo paginado para Bodegas Alianza
│   ├── scraper_multitienda.py      # Scraper para Sam's Club, Walmart, Chedraui y Soriana
│   ├── scraper_selenium.py         # Scraper dinámico con Selenium y BS4 (Human-in-the-Loop)
│   ├── analizador.py               # Motor de análisis en pandas (auditoría, métricas, rankings, cross-tienda)
│   ├── actualizar_dashboard_completo.py # Consolidación general y pipeline
│   └── generar_dashboard_v4.py     # Generador de dashboard BI (Material 3 Expressive)
├── tests/
│   ├── __init__.py
│   ├── test_analizador.py          # Pruebas de métricas, rankings y deduplicación (15 pruebas)
│   ├── test_clasificacion.py       # Pruebas de clasificación NOM y extracción de volumen (50 pruebas)
│   └── test_sprint2.py             # Pruebas de comparativas cross-tienda, validación y guardado atómico (11 pruebas)
├── requirements.txt                # Dependencias (pandas, numpy, pytest, beautifulsoup4, selenium)
├── index.html                      # Dashboard interactivo para GitHub Pages
└── README.md                       # Documentación y guía de ejecución
```

---

## Requisitos e Instalación

Entorno probado: **Linux Fedora 44 (Plasma) / Python 3.14+ / Google Chrome o Firefox**.

1. **Crear y activar el entorno virtual:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

---

## Pipeline de Datos y Ejecución

El flujo completo del proyecto consta de 3 fases:

```
[1. Recolección] Scrapers multitienda (Alianza, Sam's, Walmart, Chedraui, Soriana)
       ↓
[2. Consolidación] Clasificación estricta NOM-006 / NOM-070 y normalización de volumen
       ↓
[3. Dashboard BI] Generación reactiva de data/dashboard_bi.html e index.html
```

### 1. Ejecutar el Pipeline Completo
```bash
# Paso A: Consolidar y clasificar datasets de las 5 tiendas
python src/actualizar_dashboard_completo.py

# Paso B: Generar y sincronizar el Dashboard interactivo
python src/generar_dashboard_v4.py
```

### 2. Ejecutar las Pruebas Unitarias
Valida la conversión de mililitros a litros, cálculo de descuentos, promociones multiunidad, detección de duplicados, datos faltantes, exclusión de precios nulos y partición estricta de categorías:

```bash
pytest -v
```

### 3. Ejecutar Scrapers Específicos

- **Bodegas Alianza (API VTEX oficial):**
  ```bash
  python src/scraper_alianza.py --terminos "1800" "Herradura" "Amarás" "Red Label" "Jack Daniel" --salida data/scraped_alianza.csv
  ```

- **Scraper Asistido con Selenium (Sam's Club / SPAs):**
  Abre un navegador real (Chrome por defecto, o `--navegador firefox`) para permitir que el JavaScript hidrate precios y existencias:
  ```bash
  python src/scraper_selenium.py --urls "https://www.sams.com.mx" --tienda "Sam's Club" --salida data/scraped_selenium.csv
  ```
  *(Para ejecutar en modo sin cabeza usar la bandera `--headless`).*

---

## Columnas del Esquema CSV

| Columna | Descripción |
| :--- | :--- |
| `tienda` | Comercio donde se cotiza (ej. Bodegas Alianza, Sam's Club). |
| `producto` | Nombre comercial completo de la etiqueta. |
| `marca` | Marca de la bebida. |
| `categoria` | Tequila, Mezcal, Whisky, Licor de Whisky, Vino. |
| `subcategoria` | Añejo Tradicional, Añejo Cristalino, Reposado, Blended Scotch, Silvestre, etc. |
| `clase` | Clase normativa (Añejo, Reposado, Joven, no_aplica). |
| `tipo_mezcal` | Artesanal, Ancestral, Industrial, no_aplica. |
| `especie_agave` | Tequilana Weber, Espadín, Tobalá, Cupreata, Ensamble, no_aplica. |
| `productor` | Razón social o destilería / palenque productor con NOM. |
| `sello_regulador`| `sí`, `no`, o `no verificado`. |
| `ml` | Volumen numérico en mililitros (ej. 700, 750, 1000, 1750, 4000). |
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
