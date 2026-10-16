# Auditoría Técnica y de Oportunidades de Mejora

**Proyecto:** Cantina Familiar — Sistema de Apoyo a la Decisión de Compra Navideña 2026
**Fecha de auditoría:** 16 de octubre de 2026
**Alcance:** Código Python (`src/`, `tests/`), datos (`data/`), documentación (`README.md`), empaquetado, y artefactos versionados.
**Tipo:** Auditoría de solo lectura (no se modificó ningún archivo del proyecto).

---

## 1. Resumen ejecutivo

El proyecto es funcional y cumple su objetivo: existe una cadena completa de **recolección → consolidación → análisis → visualización**. La suite de pruebas pasa (**14/14**) y el pipeline genera `dashboard_data.json` e `index.html` correctamente.

Sin embargo, el código presenta **deuda técnica significativa** concentrada en cuatro frentes:

1. **Duplicación de la lógica de negocio** (clasificación NOM y extracción de volumen repetidas en 4–5 módulos con reglas divergentes).
2. **Código huérfano y rutas absolutas hardcodeadas** que rompen la portabilidad.
3. **Calidad y trazabilidad de datos** (inconsistencias en multipacks, outliers, columnas de auditoría que nunca se llenan).
4. **Ausencia de infraestructura de calidad** (sin linter, sin CI, sin `pyproject.toml`, sin validación de esquema).

La buena noticia: **las mejoras de mayor impacto son de bajo esfuerzo** y se pueden atacar en el corto plazo (ver §10, Roadmap priorizado).

### Tabla resumen de hallazgos

| # | Hallazgo | Severidad | Esfuerzo |
|---|---|---|---|
| H1 | Lógica de clasificación duplicada y divergente en 5 módulos | 🔴 Alta | Medio |
| H2 | `extraer_ml` implementada 3 veces con comportamiento distinto | 🔴 Alta | Bajo |
| H3 | 3 generadores de dashboard (4,479 líneas); solo 1 en uso | 🔴 Alta | Bajo |
| H4 | Ruta absoluta `/home/cesar/.gemini/...` hardcodeada | 🔴 Alta | Bajo |
| H5 | `index.html` duplicado manual de `data/dashboard_bi.html` | 🟠 Media-Alta | Bajo |
| H6 | Multipacks mal normalizados (`Pack 6 … 700ml` → ml=700) | 🔴 Alta | Medio |
| H7 | Precios ausentes → `precio_por_litro = 0` → aparecen como "los más baratos" | 🔴 Alta | Bajo |
| H8 | `es_duplicado` nunca se marca (siempre 0) en la salida | 🟠 Media-Alta | Bajo |
| H9 | Sin validación de esquema ni de rangos antes de procesar | 🟠 Media-Alta | Medio |
| H10 | 13 `except Exception` silenciosos; scrapers sobreescriben CSV de forma no atómica | 🟠 Media | Medio |
| H11 | Testing limitado a `analizador.py`; sin pruebas de scrapers/consolidación | 🟠 Media-Alta | Alto |
| H12 | Sin `numpy` en `requirements.txt` (se importa directamente) | 🟠 Media | Bajo |
| H13 | Sin empaquetado (`pyproject.toml`), versiones sin fijar, sin linter/CI | 🟠 Media | Medio |
| H14 | Documentación desactualizada (comando `--url`, "13 pruebas", estructura incompleta) | 🟠 Media | Bajo |
| H15 | Artefactos generados y pesados versionados en git (+~1.4 MB duplicados) | 🟠 Media | Bajo |
| H16 | `data/debug_page.html` rastreado pese a estar en `.gitignore` | 🟡 Baja | Bajo |
| H17 | Ética/ToS: Selenium evade `navigator.webdriver` y resuelve CAPTCHA | 🟠 Media | Medio |
| H18 | `precios_bebidas_verificados.csv` huérfano con esquema legacy | 🟡 Baja | Bajo |
| H19 | Logging por `print`, sin niveles, sin registro persistente | 🟡 Baja | Medio |
| H20 | Sin retries/backoff en las peticiones HTTP | 🟡 Baja | Bajo |

---

## 2. Metodología

- Lectura completa de los 11 módulos de `src/` y del módulo de pruebas.
- Inventario de datasets (`data/*.csv`) y verificación de encabezados/esquema.
- Ejecución de la suite: `pytest -v tests/test_analizador.py` → **14 passed**.
- Análisis de calidad de datos con pandas sobre `data/catalogo_completo_consolidado.csv` (865 filas).
- Revisión de historia git (`git log`, `git ls-files`) y de `.gitignore`.

---

## 3. Arquitectura y estructura del código

### 3.1 Inventario

| Módulo | Líneas | Rol | ¿En uso? |
|---|---:|---|---|
| `src/analizador.py` | 180 | Motor de métricas y rankings | ✅ |
| `src/scraper_alianza.py` | 159 | Scraper API VTEX Alianza | ✅ |
| `src/scraper_catalogo_completo.py` | 368 | Scraper exhaustivo Alianza | ✅ |
| `src/scraper_multitienda.py` | 670 | Scraper Sam's/Walmart/Chedraui/Soriana | ✅ |
| `src/scraper_selenium.py` | 562 | Scraper SPA con Selenium (HITL) | ⚠️ Aislado |
| `src/actualizar_dashboard_completo.py` | 253 | Consolidación + clasificación NOM | ✅ |
| `src/actualizar_dashboard_categorias.py` | 72 | Re-clasificación + escritura JSON | ⚠️ Duplica/compite |
| `src/generar_dashboard.py` | 1,035 | Dashboard v1 | ❌ Obsoleto |
| `src/generar_dashboard_v3.py` | 1,255 | Dashboard v3 | ❌ Obsoleto |
| `src/generar_dashboard_v4.py` | 2,189 | Dashboard v6.0 (MD3) | ✅ |
| `tests/test_analizador.py` | 260 | Pruebas unitarias | ✅ |

> **Observación:** 4,479 líneas (63 % del código de `src/`) corresponden a tres generadores de dashboard que producen el mismo artefacto. Solo `generar_dashboard_v4.py` está vigente.

### 3.2 Hallazgo H1 — Clasificación NOM duplicada y divergente 🔴

La clasificación de categorías/subcategorías (la lógica más sensible del proyecto) está implementada **cinco veces** con reglas que ya divergen:

- `src/scraper_alianza.py:35` — `clasificar_categoria()`
- `src/scraper_catalogo_completo.py:92` — inline en `procesar_catalogo_completo()`
- `src/scraper_multitienda.py:122` — `evaluar_y_normalizar_producto()`
- `src/actualizar_dashboard_completo.py:76` — `clasificar_estricto()`
- `src/actualizar_dashboard_categorias.py:13` — `asignar_categoria_comparable()`

**Evidencia de divergencia:**
- `clasificar_agave_mezcal` devuelve `"Tobalá"` en `scraper_catalogo_completo.py:81` pero `"Tobalá silvestre (A. potatorum)"` en `scraper_multitienda.py:99`.
- `analizador.py:115` usa el grupo `"Mezcal - Silvestres (Tobalá/Cupreata/Cuishe)"` y `"Vino - Tinto Clericot"`, mientras el dashboard usa `"Mezcal - Silvestre"` y `"Vino - Tinto Clericot"` (`actualizar_dashboard_completo.py:139,156`). Los nombres no coinciden.
- `scraper_alianza.py:45` clasifica `"plata"` como subcategoría `"Blanco"`, mientras `scraper_multitienda.py:178` **descarta** los blancos.

**Impacto:** un mismo producto puede recibir categorías distintas según la ruta de entrada; cualquier corrección de reglas debe replicarse en 5 sitios (alto riesgo de regresión).

**Recomendación:** extraer un único módulo `src/clasificacion.py` (o `dominio/nom.py`) con `clasificar_estricto()`, `clasificar_agave_mezcal()`, `extraer_ml()` y `limpiar_precio()`, y que todos los scrapers/consolidadores lo importen. Añadir pruebas de tabla (ver H11).

### 3.3 Hallazgo H2 — `extraer_ml` triplicada con lógica distinta 🔴

- `src/scraper_alianza.py:20` — sin validación de rango (acepta cualquier `litros * 1000`).
- `src/scraper_catalogo_completo.py:42` — idéntica a la anterior (copia).
- `src/scraper_multitienda.py:60` — **con** validaciones adicionales (`0.3 ≤ L ≤ 6.0`, detección de multipacks, `cc`).

**Impacto:** el mismo nombre de producto puede producir `ml` distintos según el scraper; como `precio_por_litro = precio / (ml/1000)`, el ranking cambia.

**Recomendación:** consolidar en una sola función con pruebas parametrizadas de casos límite (`1.75 L`, `946 ml`, `187.5 ml`, `Pack de 6`, `6 pzas`).

### 3.4 Hallazgo H3 — Código huérfano / artefactos obsoletos 🔴

- `generar_dashboard.py` y `generar_dashboard_v3.py` no se referencian en ningún flujo ni en el README.
- `actualizar_dashboard_categorias.py` escribe `data/dashboard_data.json` con **filtros de precio distintos** a `actualizar_dashboard_completo.py` (líneas 53–59 vs 219–226), creando un conflicto "último en escribir gana".

**Recomendación:** mover los generadores obsoletos a `legacy/` o eliminarlos; definir un único entrypoint de pipeline documentado.

---

## 4. Portabilidad y configuración

### 4.1 Hallazgo H4 — Ruta absoluta hardcodeada 🔴

```
src/generar_dashboard.py:19
src/generar_dashboard_v3.py:14
src/generar_dashboard_v4.py:12
ARTIFACT_DIR = "/home/cesar/.gemini/antigravity/brain/cf5b6fe1-c31f-46a0-a350-06d6d2e984ca"
```

**Impacto:** los tres generadores fallan (o escriben en un lugar inexistente) en cualquier máquina distinta. Además acoplan el proyecto a una herramienta externa (Antigravity/Gemini).

**Recomendación:** eliminar la escritura al directorio de artefactos; escribir solo en rutas relativas a la raíz del proyecto (usando `pathlib.Path(__file__).resolve().parent`). Hacer el `ARTIFACT_DIR` opcional vía variable de entorno.

### 4.2 Hallazgo H5 — `index.html` es una copia manual 🟠

`index.html` (505 KB) es **byte a byte idéntico** a `data/dashboard_bi.html` (496 KB). Sin embargo, `generar_dashboard_v4.py` escribe solo en `data/dashboard_bi.html` y en el directorio de artefactos; **nunca** en `index.html`.

**Impacto:** `index.html` se desincroniza del generador en cuanto alguien regenera el dashboard; es un duplicado sin fuente de verdad.

**Recomendación:** que el generador produzca `index.html` (o que `index.html` sea un enlace/copia automática); versionar solo una de las dos copias.

---

## 5. Calidad de datos

Análisis sobre `data/catalogo_completo_consolidado.csv` (865 filas).

### 5.1 Hallazgo H6 — Multipacks mal normalizados 🔴

Ejemplos detectados:

| Producto | ml almacenado | ml real esperado |
|---|---:|---:|
| `Pack 6 Tequila Cuervo 1800 Milenio … 700ml` (Walmart) | 700 | 4,200 |
| `Pack de 12 Tequila Cuervo 1800 Milenio … 700ml` | 8,400 | correcto ✅ |

`corregir_ml_producto()` (`actualizar_dashboard_completo.py:40`) sí entiende `"Pack de N"` pero **no** `"Pack 6"`. El resultado es un `precio_por_litro` inflado por 6× en esos registros.

### 5.2 Hallazgo H7 — Precios ausentes rankean como los más baratos 🔴

`calcular_costo_efectivo()` (`src/analizador.py:46`) devuelve `0.0` cuando no hay ningún precio. Luego `precio_por_litro = 0 / litros = 0`, y los rankings ordenan **ascendentemente** (`analizador.py:125`), por lo que un registro sin precio aparece como **el más económico del grupo**. Aunque hoy el consolidado no tiene precios nulos, es una bomba de tiempo y ya se ve en `precios_bebidas_verificados.csv` (esquema distinto).

**Recomendación:** devolver `NaN` (no `0.0`) y excluir del ranking o marcarlos explícitamente.

### 5.3 Hallazgo H8 — `es_duplicado` nunca se activa 🟠

- `detectar_duplicados()` (`analizador.py:40`) usa la clave `(tienda, producto, ml)`.
- En el consolidado: **0 filas** marcadas como duplicadas.
- Pero hay **40 grupos de `producto + ml` presentes en más de una tienda** que nunca se señalan como "duplicado" ni como "comparativa".

**Impacto:** la columna de auditoría no aporta valor y da falsa sensación de limpieza. Para comparar precios entre tiendas, la clave relevante es `(producto, ml)` **sin** tienda.

### 5.4 Hallazgo H9 — Sin validación de esquema/rangos 🟠

`analizador.cargar_datos()` (`analizador.py:22`) solo verifica presencia de columnas, no tipos ni rangos. Datos con `ml` no numérico se corrigen silenciosamente a 750 (`analizador.py:84`), lo que sesga métricas sin avisar. Tampoco se validan `abv ∈ (0,100)`, precios positivos, ni fechas.

### 5.5 Otros datos

- **Outliers**: `precio_por_litro` máximo = **985,714 $/L** (Royal Salute 51 años, 690,000 MXN). La media del dataset (4,742 $/L) está dominada por ultra-lujo. El dashboard filtra (>2,000 MXN), pero el CSV consolidado no.
- **`precio_regular` rellenado con `precio_efectivo`** (`analizador.py:89`) hace que `ahorro_verificable` sea siempre 0 en esos casos, ocultando datos faltantes.
- **Datos de contacto ausentes** en todos los registros provenientes de scrapers (`productor` = marca, `sello_regulador` = `"no_verificado"`), lo que impide auditar la Regla de Rigor sobre NOM.

---

## 6. Robustez y observabilidad

### 6.1 Hallazgo H10 — Excepciones silenciadas y escritura no atómica 🟠

- **13** bloques `except Exception` en `src/` que tragan el error y continúan (`scraper_multitienda.py`, `scraper_selenium.py`, etc.). Una caída de red a mitad de un scraper produce un CSV **parcial**, sin resumen de fallos.
- Los scrapers hacen `df.to_csv(ruta, index=False)` **sobre el mismo archivo** (`scraper_multitienda.py:643,648,653,658`). Una ejecución fallida **sobreescribe** los datos buenos previos.

**Recomendación:** escribir a archivo temporal y renombrar al terminar; registrar al final un resumen `éxitos/fallos/omitidos`; distinguir `except` esperados (red, parseo) de los inesperados.

### 6.2 Hallazgo H19 — Logging por `print` 🟡

Todo el proyecto usa `print()` con emojis, sin `logging`, sin niveles ni archivo persistente. Dificulta diagnosticar ejecuciones largas desatendidas.

### 6.3 Hallazgo H20 — Sin reintentos/backoff 🟡

Las peticiones `urllib` usan `time.sleep` fijo sin reintentos ni backoff exponencial ante `429/5xx`.

---

## 7. Pruebas

### 7.1 Hallazgo H11 — Cobertura concentrada en un módulo 🟠

- 14 pruebas, todas sobre `analizador.py` y una función de `actualizar_dashboard_completo.py:76`.
- **Sin pruebas** para: `extraer_ml` (en ninguna de sus 3 versiones), `limpiar_precio` / `extraer_precio_texto`, `evaluar_y_normalizar_producto` (la clasificación más compleja, 260 líneas), `corregir_ml_producto` (multipacks), parseo de HTML/JSON de scrapers, consolidación y generación de JSON.
- Sin `conftest.py`, sin configuración de cobertura, sin fixtures para HTML de ejemplo.

**Recomendación:** priorizar pruebas de tabla para `corregir_ml_producto` y `evaluar_y_normalizar_producto` (alta densidad de reglas y cero cobertura) y una prueba por cada formato de precio/volumen.

---

## 8. Empaquetado y configuración del proyecto

### 8.1 Hallazgo H12 — Dependencia implícita de `numpy` 🟠

`src/analizador.py:10` hace `import numpy as np`, pero `requirements.txt` **no incluye `numpy`**. Funciona solo porque `pandas` lo arrastra transitivamente; una actualización de pandas que lo haga opcional rompería el análisis.

### 8.2 Hallazgo H13 — Sin infraestructura de calidad 🟠

- No existe `pyproject.toml` / `setup.cfg` / `setup.py`: el proyecto no es instalable ni hay metadatos.
- Versiones sin fijar (`pandas>=2.0.0`, etc.) → builds no reproducibles.
- Sin linter/formatter (ruff, black), sin `pre-commit`, sin CI (`.github/workflows`).

---

## 9. Documentación y repositorio

### 9.1 Hallazgo H14 — README desactualizado 🟠

| Ubicación | Problema |
|---|---|
| `README.md:73` | El ejemplo usa `--url` pero el script exige `--urls` (`scraper_selenium.py:545`) → el comando **falla**. |
| `README.md:22` | Dice "13 pruebas"; en realidad son **14**. |
| `README.md:9-25` | La estructura omite `scraper_multitienda.py`, `scraper_catalogo_completo.py`, las 3 variantes de dashboard, `actualizar_dashboard_*.py`, `index.html`, `precios_bebidas_verificados.csv`. |
| `README.md:31,70` | Dice "Firefox por defecto"; el scraper Selenium por defecto usa **Chrome** (`scraper_selenium.py:70`). |
| — | No documenta el **orden del pipeline** (scrape → consolidar → dashboard). |

### 9.2 Hallazgo H15 — Artefactos generados versionados 🟠

Rastreados en git y **generados en runtime**:

| Archivo | Tamaño |
|---|---:|
| `index.html` | 505 KB |
| `data/dashboard_bi.html` | 496 KB |
| `data/dashboard_data.json` | 384 KB |
| `data/catalogo_completo_consolidado.csv` + `ranking_completo_general.csv` | ~720 KB |

Además, `index.html` y `data/dashboard_bi.html` son **duplicados idénticos** (~1 MB redundante).

**Recomendación:** excluir los artefactos derivados del control de versiones (o moverlos a un branch/release); versionar solo insumos y código.

### 9.3 Hallazgo H16 — `.gitignore` ineficaz para archivo ya rastreado 🟡

`data/debug_page.html` está listado en `.gitignore` (línea 18) **pero sigue rastreado** (aparece en `git ls-files`). Un `.gitignore` no destrackea archivos; el volcado de HTML scrapeado no debería versionarse.

### 9.4 Hallazgo H18 — CSV huérfano con esquema legacy 🟡

`precios_bebidas_verificados.csv` está en la raíz, usa un esquema antiguo y distinto (`presentacion_ml`, `comercio`, `precio_promocion`, `precio_litro`…) que **ningún módulo consume** ni el README documenta. Es candidato a archivar o eliminar.

### 9.5 Otros repositorio

- Historia git mínima (2 commits); mensajes en español correctos, pero sin convención (`feat:`/`fix:`).
- `.venv/` correctamente ignorado ✅.

---

## 10. Ética y cumplimiento (scraping)

### 10.1 Hallazgo H17 — Tensiones con los ToS de los sitios 🟠

- `scraper_alianza.py` y `scraper_catalogo_completo.py` se apoyan en la API pública y citan `robots.txt` ✅.
- `scraper_selenium.py` explicita **evasión de `navigator.webdriver`**, `--disable-blink-features=AutomationControlled`, y resolución humana de CAPTCHA (líneas 76–90, 155–198). Esto puede contravenir los términos de uso de Sam's Club / Walmart.
- No hay documentación de un límite de tasa, ventana horaria ni política de caché.

**Recomendación:** documentar el fundamento ético/legal, priorizar APIs públicas, limitar frecuencia y volumen, y señalar los scrapers "frágiles" que dependen de evasión como no-oficiales.

---

## 11. Roadmap priorizado

### Sprint 1 — Quick wins de alto impacto (≈1–2 días)

| Acción | Hallazgos | Impacto |
|---|---|---|
| Crear `src/clasificacion.py` y migrar todos los módulos a él | H1, H2 | Elimina 4 copias y divergencias |
| Quitar la ruta absoluta `/home/cesar/.gemini/...` | H4 | Portabilidad |
| Devolver `NaN` (no `0.0`) sin precio y excluir del ranking | H7 | Evita falsos "más baratos" |
| Añadir `numpy` a `requirements.txt` | H12 | Build correcto |
| Corregir README (`--urls`, 14 pruebas, estructura, Chrome) | H14 | Docs fiables |
| `.gitignore` + `git rm --cached` de artefactos y `debug_page.html` | H15, H16 | Repo limpio |

### Sprint 2 — Consolidación y datos (≈1 semana)

| Acción | Hallazgos | Impacto |
|---|---|---|
| Arreglar `corregir_ml_producto` para `Pack N` y validar contra multipacks | H6 | Métricas correctas |
| Unificar clave de deduplicación cross-tienda | H8 | Comparativas reales |
| Validación de esquema/rangos de entrada | H9 | Datos fiables |
| Eliminar generadores v1/v3 y `actualizar_dashboard_categorias.py` | H3 | −63 % de código |
| Único generador → escribe `index.html` | H5 | Fuente de verdad única |
| Escritura atómica + resumen de fallos en scrapers | H10 | No perder datos |

### Sprint 3 — Calidad sostenible (≈1–2 semanas)

| Acción | Hallazgos | Impacto |
|---|---|---|
| `pyproject.toml`, versiones fijadas, ruff + pytest-cov | H13 | Reproducibilidad |
| Pruebas de tabla para clasificación y `extraer_ml`/`corregir_ml_producto` | H11 | Red de seguridad |
| Migrar `print` → `logging` con niveles y archivo | H19 | Diagnóstico |
| Reintentos con backoff en HTTP | H20 | Robusto ante red |
| Documentar política ética de scraping y pipeline | H17 | Cumplimiento |

---

## 12. Conclusión

El proyecto **funciona y resuelve el problema**, con una base de pruebas inicial valiosa. Las oportunidades de mejora no son sobre "reescribir", sino sobre **eliminar duplicación y divergencia** (H1–H3), **restaurar la confiabilidad de los datos** (H6–H9) y **añadir la infraestructura mínima de calidad** (H11–H13). Atacando el Sprint 1, el proyecto recupera portabilidad, elimina ~63 % de código muerto y previene decisiones de compra basadas en métricas erróneas; el Sprint 2 consolida la lógica de negocio en un único punto de verdad.

---

*Auditoría realizada en modo solo lectura. No se modificó ningún archivo del proyecto.*
