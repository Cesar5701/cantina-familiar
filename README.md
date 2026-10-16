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
│   ├── scraper_alianza.py          # Scraper ético para API pública VTEX de Bodegas Alianza
│   ├── scraper_selenium.py         # Scraper dinámico con Selenium y BS4 (Human-in-the-Loop)
│   └── analizador.py               # Motor de análisis en pandas (auditoría, métricas, rankings)
├── tests/
│   ├── __init__.py
│   └── test_analizador.py          # Suite de pruebas unitarias (13 pruebas con pytest)
├── requirements.txt                # Dependencias (pandas, pytest, beautifulsoup4, selenium)
└── README.md                       # Documentación y guía de ejecución
```

---

## Requisitos e Instalación

Entorno probado: **Linux Fedora 44 (Plasma) / Python 3.14+ / Firefox**.

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

## Cómo Ejecutar y Verificar

### 1. Ejecutar el Analizador de Precios y Rankings
Lee el archivo de datos, audita datos faltantes y duplicados, calcula el costo efectivo unitario (incluyendo promociones multiunidad como 3x2), calcula precio por litro y genera rankings separados por categoría:

```bash
python src/analizador.py --entrada data/bebidas_verificadas.csv --salida data/reporte_ranking.csv
```

### 2. Ejecutar las Pruebas Unitarias
Valida la conversión de mililitros a litros, cálculo de descuentos, promociones multiunidad, detección de duplicados, datos faltantes y partición estricta de categorías (tequila y mezcal):

```bash
pytest -v tests/test_analizador.py
```

### 3. Ejecutar el Scraper de Bodegas Alianza (API VTEX oficial)
Consulta exclusivamente la API pública oficial permitida en el `robots.txt` de Bodegas Alianza (`/api/catalog_system/pub/products/search/`):

```bash
python src/scraper_alianza.py --terminos "1800" "Herradura" "Amarás" "Red Label" "Jack Daniel" --salida data/scraped_alianza.csv
```

### 4. Ejecutar el Scraper Asistido con Selenium + BeautifulSoup (Sam's Club / SPAs)
Abre un navegador real (Firefox por defecto) para permitir que el JavaScript hidrate precios y existencias. Si el sitio presenta un CAPTCHA o verificación WAF, el script se pausa y te notifica en terminal para resolverlo manualmente en la ventana abierta antes de continuar:

```bash
python src/scraper_selenium.py --url "https://www.sams.com.mx" --tienda "Sam's Club" --salida data/scraped_selenium.csv
```
*(Para ejecutar en modo sin cabeza usar la bandera `--headless`, aunque se recomienda modo visual para resolver desafíos de seguridad si se presentan).*

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
