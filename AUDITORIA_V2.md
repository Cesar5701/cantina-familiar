# Auditoría Técnica V2 — Verificación de Hallazgos y Nuevas Oportunidades

**Proyecto:** Cantina Familiar — Sistema de Apoyo a la Decisión de Compra Navideña 2026
**Fecha:** 16 de octubre de 2026
**Auditoría anterior (base):** [`AUDITORIA.md`](./AUDITORIA.md) — 20 hallazgos (H1–H20)
**Tipo:** Auditoría de solo lectura. No se modificó ningún archivo del proyecto.

---

## 1. Resumen ejecutivo

Esta segunda auditoría tiene dos objetivos:

1. **Verificar** que los 20 hallazgos de la primera auditoría quedaron realmente resueltos (no solo "declarados" en un commit).
2. **Auditar de nuevo** el estado actual para descubrir oportunidades de mejora surgidas tras las refactorizaciones.

### Resultado de la verificación

> ✅ **Los 20 hallazgos (H1–H20) de `AUDITORIA.md` están resueltos y verificados con evidencia en código y datos.**

El proyecto pasó de 2,824 → **5,845 líneas** en `src/` y de 14 → **85 pruebas**, con una arquitectura notoriamente más limpia (módulos de dominio, I/O, HTTP y logging separados).

### Resultado de la nueva auditoría

Se identificaron **11 oportunidades de mejora nuevas (H21–H31)**, ninguna crítica. Las más relevantes:

| # | Hallazgo nuevo | Severidad |
|---|---|---|
| H21 | `detectar_duplicados` corrompe las claves comparativas si `ml` es `float` | 🟠 Media-Alta |
| H22 | Validación de rangos es solo reporte: no filtra, y el mensaje está hardcodeado | 🟠 Media-Alta |
| H23 | Doble criterio de normalización de producto (`prod_key` vs `clave_comparativa`) | 🟠 Media |
| H24 | Cobertura de pruebas 38 % sin umbral (`fail_under`) | 🟠 Media |
| H25 | Outliers de ultra-lujo contaminan el CSV consolidado | 🟡 Baja-Media |
| H26 | Residuo H1: grupo `Mezcal - Silvestre` duplicado en rankings | 🟡 Baja |
| H27 | Residuo H2: `extraer_precio_texto` duplicada en Selenium | 🟡 Baja |
| H28 | Constantes de red (User-Agent/headers) duplicadas en 5 sitios | 🟡 Baja |
| H29 | Monolito `generar_dashboard_v4.py` (2,588 líneas / 137 KB) | 🟡 Baja-Media |
| H30 | 5 bloques `except Exception: pass` en Selenium | 🟡 Baja |
| H31 | Sin `conftest.py`: fixtures de prueba duplicadas | 🟡 Baja |

---

## 2. Metodología

- Relectura íntegra de `AUDITORIA.md` para extraer los 20 hallazgos y su recomendación.
- Verificación **uno por uno** con evidencia (búsqueda en código, `git ls-files`, ejecución del pipeline).
- Ejecución de la suite completa y de la cobertura: `pytest --cov=src`.
- Ejecución de `ruff check .` y `ruff format --check .`.
- Nueva auditoría de calidad de datos sobre `data/catalogo_completo_consolidado.csv` (863 filas).
- Pruebas de comportamiento para confirmar bugs latentes (p. ej. `ml` float).

---

## 3. Verificación de los 20 hallazgos de `AUDITORIA.md`

| # | Hallazgo original | Estado | Evidencia actual |
|---|---|---|---|
| H1 | Clasificación NOM duplicada en 5 módulos | ✅ Resuelto | Único módulo `src/clasificacion.py` (496 líneas). Ninguna `def clasificar_*` fuera de él; todos los módulos importan de ahí (`scraper_alianza.py:26`, `scraper_catalogo_completo.py:31`, `scraper_multitienda.py:35`, `actualizar_dashboard_completo.py:29`, `scraper_selenium.py:36`). |
| H2 | `extraer_ml` triplicada | ✅ Resuelto | Una sola definición: `clasificacion.py:197`. |
| H3 | 3 generadores de dashboard huérfanos | ✅ Resuelto | Solo queda `src/generar_dashboard_v4.py`; v1/v3 y `actualizar_dashboard_categorias.py` movidos a `legacy/`. |
| H4 | Ruta absoluta `/home/cesar/.gemini/...` | ✅ Resuelto | `grep "/home/" src/*.py` → sin coincidencias. El artefacto externo es opcional vía `ANTIGRAVITY_ARTIFACT_DIR`. |
| H5 | `index.html` copia manual | ✅ Resuelto | El generador escribe ambas salidas desde una fuente única (`generar_dashboard_v4.py:20-21, 2572, 2575`). |
| H6 | Multipacks mal normalizados | ✅ Resuelto | `Pack 6 … 700ml → 4200` y `Pack x 3 … 750ml → 2250` (verificado en vivo y en el dato consolidado). |
| H7 | Precio ausente → `$/L = 0` | ✅ Resuelto | `calcular_costo_efectivo` devuelve `np.nan`; el ranking excluye nulos/≤0 (`analizador.py`). |
| H8 | `es_duplicado` nunca se marca | ✅ Resuelto | `detectar_duplicados` añade `clave_comparativa`, `num_tiendas_disponibles`, `es_comparable_cross_tienda` + `obtener_comparativa_cross_tienda()`. **114 registros comparables cross-tienda** en el consolidado. |
| H9 | Sin validación de esquema/rangos | ✅ Resuelto | `validar_esquema_y_rangos()` (`analizador.py:44`) valida columnas, `ml ∈ [100,10000]`, `abv ∈ (0,100]` y precios. (Ver nuevo H22 sobre su aplicación.) |
| H10 | Excepciones silenciosas + escritura no atómica | ✅ Resuelto | `src/io_utils.py` (`guardar_csv_atomico`/`guardar_json_atomico`) usado en todo el pipeline; `ResumenScraping` integrado en los 5 scrapers. |
| H11 | Testing solo en `analizador.py` | ✅ Resuelto | 4 suites (`test_analizador`, `test_clasificacion`, `test_sprint2`, `test_sprint3`), **85 pruebas**, incluidos mocks de HTTP (VTEX/Next.js/SFCC). |
| H12 | `numpy` fuera de `requirements.txt` | ✅ Resuelto | `requirements.txt:2` → `numpy>=1.26.0,<3.0.0`. |
| H13 | Sin empaquetado/linter/CI | ✅ Resuelto | `pyproject.toml` (build-system, deps, `[tool.ruff]`, `[tool.coverage]`), `ruff` 0.17.1 (checks OK), `.pre-commit-config.yaml` y CI que corre `ruff` + `pytest --cov`. |
| H14 | README desactualizado | ✅ Resuelto | README con `--urls` correcto (línea 108), estructura completa (`clasificacion`, `http_utils`, `io_utils`, `logger`, `politica_scraping`), Chrome y pipeline documentados. |
| H15 | Artefactos generados versionados | ✅ Resuelto | `git ls-files` no lista `index.html`, `dashboard_bi.html`, `dashboard_data.json` ni los CSV consolidados; están en `.gitignore`. |
| H16 | `debug_page.html` rastreado | ✅ Resuelto | Ya no aparece en `git ls-files`. |
| H17 | Sin política ética / pipeline | ✅ Resuelto | `docs/politica_scraping.md` (85 líneas) + sección "Pipeline de Datos" en el README. |
| H18 | CSV huérfano legacy | ✅ Resuelto | `precios_bebidas_verificados.csv` movido a `legacy/`. |
| H19 | Logging por `print` | ✅ Resuelto | `src/logger.py` centralizado; **0 `print(` en `src/`**. |
| H20 | Sin retries/backoff | ✅ Resuelto | `src/http_utils.py` con backoff exponencial + jitter, usado en los 3 scrapers HTTP. |

**Conclusión de la verificación:** los 20 hallazgos fueron resueltos de forma efectiva (no cosmética). Dos de ellos dejan un residuo menor, registrado abajo como H26 y H27.

---

## 4. Nuevos hallazgos (H21–H31)

### H21 — `detectar_duplicados` corrompe la clave comparativa con `ml` float 🟠

`analizador.py`, dentro de `detectar_duplicados()`:

```python
ml_val = int(row.get("ml", 750)) if (pd.notnull(row.get("ml")) and str(row.get("ml")).isdigit()) else 750
```

`str(700.0).isdigit()` es **`False`**, así que un `ml` float cae al valor por defecto **750**. Verificado en vivo:

```
tienda  ml     clave_comparativa               es_comparable_cross_tienda
A       700.0  700 ml tequila x_750            True
B       700.0  700 ml tequila x_750            True
```

La clave termina en `_750` aunque la botella es de 700 ml.

**Impacto:** no se manifiesta hoy porque el consolidado tiene `ml` como `int64`, pero **cualquier dataset con un solo `ml` nulo** convierte la columna a `float` y **corrompe todas las claves comparativas** (agrupa productos de 700 ml junto a los de 750 ml). Es una bomba de tiempo silenciosa.

**Recomendación:** usar `pd.to_numeric(row["ml"], errors="coerce")` y un chequeo de nulo numérico en lugar de `str().isdigit()`.

### H22 — La validación de rangos no se aplica y el mensaje está hardcodeado 🟠

En `actualizar_dashboard_completo.py:104-107`:

```python
df, reporte_val = validar_esquema_y_rangos(df)
logger.info(
    f"Auditoría de datos: {reporte_val['registros_validos']}/{reporte_val['total_registros']} registros válidos (0 anomalías críticas)"
)
```

- El resultado **no filtra**: nunca se hace `df = df[df["datos_validos"]]`, así que los registros inválidos (ml fuera de rango, abv imposible, sin precio) siguen entrando al consolidado y al dashboard.
- El texto **"(0 anomalías críticas)" está hardcodeado** y se imprime aunque el reporte detecte anomalías, dando una falsa sensación de dataset limpio.

**Recomendación:** decidir una política (¿descartar, marcar o solo reportar?) y reflejarla en el log con los conteos reales del reporte.

### H23 — Doble criterio de normalización de producto 🟠

Dos normalizaciones distintas conviven en el pipeline:

- **Deduplicación** (`actualizar_dashboard_completo.py:92`): `prod_key = producto.str.lower().str.replace(r"\s+"," ")` → **conserva acentos y puntuación**.
- **Comparativa cross-tienda** (`analizador.normalizar_texto_clave`, `analizador.py:43`): elimina acentos (`NFKD`) y toda puntuación.

**Impacto:** un mismo producto puede deduplicarse bajo un criterio pero no reconocerse como comparable bajo el otro (p. ej. `"Patrón"` vs `"Patron"`, `"Jack Daniel's"` vs `"Jack Daniels"`). Genera inconsistencias entre la fila conservada y la clave comparativa.

**Recomendación:** una única función de normalización compartida, usada por ambos pasos.

### H24 — Cobertura 38 % sin umbral de calidad 🟠

`pytest --cov=src` → **38 %** (694 de 1,119 líneas sin cubrir); `scraper_selenium.py` está excluido en `[tool.coverage.run]`. No hay `fail_under`.

**Recomendación:** subir cobertura de las rutas de alto riesgo (`evaluar_y_normalizar_producto`, `scraper_catalogo_completo`, parsing del consolidador) y fijar un `fail_under` inicial conservador (p. ej. 40 %) para evitar regresiones.

### H25 — Outliers de ultra-lujo contaminan el consolidado 🟡

`data/catalogo_completo_consolidado.csv`: **82 registros** con `precio_por_litro` > 5× la mediana; máximo **985,714 $/L** (Royal Salute 51 años, 690,000 MXN). El dashboard los filtra (> ~2,000 MXN), pero el CSV consolidado y `ranking_completo_general.csv` los conservan, inflando medias y comparativas.

**Recomendación:** o bien documentar explícitamente que son "fuera de alcance", o excluirlos/marcarlos en una columna para que no contaminen agregados.

### H26 — Residuo de H1: grupo Mezcal duplicado 🟡

`analizador.py:279-280` define dos grupos con **el mismo filtro**:

```python
"Mezcal - Silvestre": validos[(validos["categoria"] == "Mezcal") & (validos["subcategoria"] == "Silvestre")],
"Mezcal - Silvestres (Tobalá/Cupreata/Cuishe)": validos[... mismo filtro ...],
```

Ambos aparecen en la salida de `imprimir_resumen_rankings`, duplicando el bloque. Eliminar el nombre legacy.

### H27 — Residuo de H2: `extraer_precio_texto` duplicada 🟡

`scraper_selenium.py:209` mantiene `extraer_precio_texto()`, que replica `limpiar_precio()` de `clasificacion.py`. Además `scraper_selenium.py` es el único módulo que **no** usa las utilidades compartidas de precio.

### H28 — Constantes de red duplicadas 🟡

El `User-Agent` de navegador y los headers están copiados en 3–5 sitios:

- `http_utils.py:17`, `scraper_multitienda.py:26`, `scraper_selenium.py:49` (UA de Chrome).
- `scraper_alianza.py:15` y `scraper_catalogo_completo.py:24` (UA de bot, con texto divergente).

**Recomendación:** centralizar en `http_utils` (UA de bot + UA de navegador) e importarlos.

### H29 — Monolito del dashboard 🟡

`generar_dashboard_v4.py` = **2,588 líneas / 137 KB** (23 % del código de `src/`), con HTML/CSS/JS embebidos en un `f-string`. Alta dificultad de mantenimiento y sin pruebas (no hay forma de testear la lógica de agrupación/orden sin renderizar).

**Recomendación:** separar la plantilla HTML/JS a un archivo `.html` (con marcadores de sustitución) y dejar Python solo para la preparación de datos.

### H30 — `except Exception: pass` en Selenium 🟡

`scraper_selenium.py` contiene **5** bloques `except Exception: ... pass` que se tragan la excepción sin registrar nada. Con el logger ya disponible, deberían al menos emitir `logger.debug(...)`.

### H31 — Sin `conftest.py` ni fixtures compartidas 🟡

Cada suite redefine su propio constructor de DataFrame (`crear_df_base` en `test_analizador.py`, `crear_df_prueba` en `test_sprint2.py`). Sin `conftest.py` ni fixtures comunes, hay duplicación y riesgo de divergencia entre datasets de prueba.

---

## 5. Roadmap sugerido (V2)

### Prioridad 1 — Corrección de latentes (corto plazo)

| Acción | Hallazgo | Impacto |
|---|---|---|
| Arreglar la conversión de `ml` en `clave_comparativa` | H21 | Evita corrupción masiva de comparativas con `ml` float/NaN |
| Aplicar (o convertir en política) la validación y corregir el mensaje hardcodeado | H22 | Dataset consolidado realmente limpio |
| Unificar normalización de producto | H23 | Dedup y comparativa coherentes |

### Prioridad 2 — Calidad y mantenibilidad (medio plazo)

| Acción | Hallazgo | Impacto |
|---|---|---|
| Extender pruebas + `fail_under` en cobertura | H24 | Red de seguridad y puerta de calidad |
| Marcar/excluir outliers de lujo | H25 | Métricas agregadas fiables |
| Centralizar constantes de red | H28 | Una sola fuente de User-Agent |
| Extraer plantilla del monolito del dashboard | H29 | Mantenibilidad (−2,000 líneas de f-string) |

### Prioridad 3 — Limpieza (bajo esfuerzo)

| Acción | Hallazgo | Impacto |
|---|---|---|
| Eliminar grupo `Mezcal - Silvestre` duplicado | H26 | Salida sin duplicados |
| Eliminar `extraer_precio_texto` y usar `limpiar_precio` | H27 | -1 duplicado |
| `logger.debug` en los `except: pass` de Selenium | H30 | Trazabilidad |
| `conftest.py` con fixtures compartidas | H31 | Tests DRY |

---

## 6. Conclusión

La primera auditoría se ejecutó **de forma completa y verificable**: los 20 hallazgos están resueltos, incluidos los más costosos (unificación de la lógica NOM en `clasificacion.py`, separación de módulos de dominio/I-O/HTTP/logging, CI con lint y cobertura, y política ética).

El proyecto pasó de un script monolítico acoplado a una base mantenible con arquitectura modular, 85 pruebas y controles de calidad automatizados. Los hallazgos nuevos (H21–H31) son de menor severidad y ninguno bloquea el uso actual; se concentran en **casos límite latentes** (H21–H23) y **deuda de mantenibilidad** (H24–H31).

---

*Auditoría V2 realizada en modo solo lectura. No se modificó ningún archivo del proyecto.*
