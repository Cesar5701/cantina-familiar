# Auditoría Completa V4 — Cantina Familiar

**Fecha:** 17 de octubre de 2026
**Alcance:** auditoría integral del repositorio (arquitectura, datos, pruebas, dependencias, build/CI, documentación y limpieza), verificando además el cierre de todas las auditorías previas (H1–H37).
**Método:** inspección estática del código (`src/`, `tests/`, `pyproject.toml`, CI), re-ejecución de la suite de calidad y análisis del dataset consolidado. Todo hallazgo se respalda con evidencia reproducible.

---

## 1. Resumen ejecutivo

El proyecto se encuentra en **muy buen estado**: las 37 observaciones de las auditorías V1–V3 están resueltas y verificadas con evidencia, la suite creció a **153 pruebas (cobertura 64.51 %)**, `ruff` pasa limpio y el dataset está **libre de nulos y de inconsistencias de precio**.

Esta auditoría abre **13 observaciones nuevas (H38–H50)**, **ninguna crítica ni alta**. Se concentran en:

1. **Una regresión** (H39): volvió a generarse la copia duplicada `data/dashboard_bi.html` (1.06 MB idéntica a `index.html`).
2. **Deuda de mantenibilidad** (H38, H40, H41): reglas de normalización por marca acumuladas a mano y lógica cross-tienda duplicada.
3. **Cobertura desigual** (H42, H43): scrapers casi sin cubrir y UI/JS sin pruebas.
4. **Higiene de dependencias y build** (H45–H48) y **documentación desactualizada** (H44).

**Veredicto: apto para producción**, con un roadmap de mejoras opcional priorizado en la sección 5.

---

## 2. Estado de calidad actual (re-ejecutado)

| Métrica | Valor | Estado |
|---|---|---|
| Pruebas | **153 passed** | ✅ |
| Cobertura total | **64.51 %** (mínimo exigido 50 %) | ✅ |
| `ruff check .` | All checks passed | ✅ |
| `ruff format --check .` | 26 archivos ya formateados | ✅ |
| `except Exception` en `src/` | **0** | ✅ |
| `except:` desnudos en `src/` | **0** | ✅ |
| Nulos en el consolidado | **0** (1,004 filas × 35 columnas) | ✅ |
| Working tree | limpio | ✅ |

### Cobertura por módulo (extremos)

| Módulo | Cob. |
|---|---|
| `actualizar_dashboard_completo.py` | 95 % |
| `generar_dashboard_v4.py` | 93 % |
| `logger.py` | 90 % |
| `clasificacion.py` | 87 % |
| `io_utils.py` | 84 % |
| `http_utils.py` | 81 % |
| `analizador.py` | 80 % |
| `scraper_alianza.py` | 56 % |
| `scraper_catalogo_completo.py` | 19 % |
| `scraper_multitienda.py` | **7 %** |

---

## 3. Verificación de auditorías previas (H1–H37)

Todas las observaciones previas quedan **resueltas y confirmadas con evidencia en el código actual**, no solo declaradas en commits:

| Bloque | Estado |
|---|---|
| **H1–H20** (Auditoría V1) | ✅ Resueltas |
| **H21–H31** (Auditoría V2) | ✅ Resueltas |
| **H32** Umbrales centralizados | ✅ `TECHOS_LITRO_OUTLIERS` y `LIMITES_PRESUPUESTO_DASHBOARD` en `clasificacion.py` |
| **H33** Excepciones genéricas acotadas | ✅ 0 `except Exception` + prueba AST |
| **H34** `scraper_selenium.py` en cobertura | ✅ `omit = []` + 19 pruebas |
| **H35** Unificar formatos 700/750 ml | ✅ Volumen estándar (650–800 ml) unificado y **blindaje**: formatos no estándar (`<650` o `>800 ml`) conservan su tamaño |
| **H36** Combos de dos medidas | ✅ Columna `es_paquete` (95 marcados) + filtro reactivo en el dashboard |
| **H37** Exclusión explícita de outliers | ✅ `df[cond_presupuesto & ~df["es_outlier_lujo"]]` |

---

## 4. Hallazgos nuevos (H38–H50)

### 4.1 Arquitectura y mantenibilidad

**H38 — Reglas de normalización por marca acumuladas a mano · Media**
`normalizar_texto_clave` (`analizador.py:47-96`) encadena ~13 regex específicas de marca/etiqueta (Mc Harrison, Patrón Cristalino, Dobel Diamante, Mayorazgo/Ollitas/Viuda de Romero/Contraluz, "Tennessee", posesivos ingleses, etc.). Es frágil ante nuevas etiquetas y difícil de testear de forma exhaustiva.
→ Migrar a una **tabla de mapeo declarativa** (datos, no código) con pruebas por entrada.

**H39 — Regresión: se vuelve a generar `data/dashboard_bi.html` · Media**
El commit `a35d4b8` (Fase 1) reintrodujo `LOCAL_HTML_PATH` en `generar_dashboard_v4.py:17`, deshaciendo la limpieza del commit `4b8759f` ("publicar solo `index.html`"). Hoy el generador escribe **dos** artefactos: `index.html` y `data/dashboard_bi.html`, ambos de **1,061,871 bytes e idénticos**. Duplica tiempo de escritura y tamaño de salida sin aportar valor.
→ Dejar un **único destino** (`index.html`) y eliminar `LOCAL_HTML_PATH` / el destino en `artifact_dir`.

**H40 — Lógica cross-tienda duplicada · Media**
`obtener_comparativa_cross_tienda()` (`analizador.py:197`) **solo se usa en pruebas**; el consolidador reimplementa su propia lógica inline (`actualizar_dashboard_completo.py:217-334`, `grupos_cross`). Dos rutas para el mismo cálculo → riesgo de divergencia silenciosa.
→ Unificar en una sola función de dominio, consumida por el consolidador.

**H41 — Lógica de dominio inline en el consolidador · Baja–Media**
`actualizar_dashboard_completo.py` contiene filtros de presupuesto, máscaras de exclusión, sincronización de categorías y armado cross dentro del script de orquestación. Mezcla orquestación con reglas de negocio.
→ Extraer la lógica de negocio a `analizador.py`/`clasificacion.py`.

### 4.2 Datos

**H42 — Verificación de integridad de datos · Informativa (sin hallazgo)**
El consolidado (1,004 filas) no tiene nulos, `confianza` es "Confirmado" en el 100 %, y no se detectan grupos cross-tienda que mezclen tamaños muy distintos (0 grupos con `max ml > 1.5× min ml`). El blindaje H35 funciona. **Sin acción requerida.**

### 4.3 Pruebas y cobertura

**H43 — Cobertura desigual en scrapers · Media**
`scraper_multitienda.py` (7 %), `scraper_catalogo_completo.py` (19 %) y `scraper_alianza.py` (56 %) apenas están cubiertos. El rigor aplicado a la lógica de análisis no llega a la capa de adquisición.
→ Añadir pruebas de parseo con HTML/JSON de muestra (patrón ya usado en `test_scraper_selenium.py`).

**H44 — UI/JS del dashboard sin pruebas · Baja–Media**
`dashboard_template.html` tiene **2,643 líneas (~141 KB)** y toda la lógica de UI (filtros en cascada, orden, canastas, versus, toggle "solo mejor precio") vive en JS embebido **sin red de seguridad automatizada**.
→ Al menos pruebas de "smoke" del HTML renderizado (presencia de elementos y de campos `data-*`).

### 4.4 Dependencias y build

**H45 — `pytest` en `requirements.txt` (runtime) · Baja**
`requirements.txt:6` incluye `pytest`, una dependencia de desarrollo, en el archivo de producción.
→ Mover a `requirements-dev.txt`.

**H46 — Cotas inconsistentes entre `pyproject.toml` y `requirements.txt` · Baja**
`pyproject.toml` declara dependencias **sin cota superior** (`numpy>=1.26.0`, `pandas>=2.0.0`, …) mientras `requirements.txt` las acota (`<3.0.0`). Dos fuentes de verdad divergentes.
→ Fuente única (idealmente `pyproject.toml`).

**H47 — CI instala dependencias duplicadas · Baja**
`.github/workflows/deploy.yml` ejecuta `pip install -r requirements.txt` **y** `pip install -e ".[dev]"`, con solapamiento (ambos traen `pytest`).
→ Instalar solo una vía.

**H48 — Sin lockfile · Baja**
No existe `uv.lock`, `requirements.lock` ni `poetry.lock`. La reproducibilidad exacta depende de las cotas.
→ Adoptar `uv`/`pip-tools` para congelar versiones.

### 4.5 Documentación

**H49 — README desactualizado e internamente inconsistente · Baja–Media**
El conteo de pruebas aparece como **122** (línea 100) pero el desglose por archivo suma **100** (líneas 41–45); el número real es **153**. La sección "Estructura" no lista `test_scraper_selenium.py` ni `docs/archivo/`.
→ Regenerar la tabla de estructura y unificar el conteo.

### 4.6 Limpieza

**H50 — Residuos y ausencia de entry points · Baja**
`data/plantilla_bebidas.csv` está rastreado pero **no se usa** en el código (candidato a eliminar); `data/bebidas_verificadas.csv` solo sirve como default de demo del analizador. No hay `console_scripts`/entry points: todo se ejecuta con `python src/...`.
→ Depurar datos muertos y, opcionalmente, exponer un CLI instalable.

---

## 5. Áreas de mejora priorizadas (roadmap sugerido)

| Prioridad | Hallazgos | Impacto |
|---|---|---|
| **P1** | H39 (regresión del duplicado) | Bajo esfuerzo, recupera una mejora ya hecha. |
| **P2** | H40, H38 | Elimina duplicación y fragilidad en el núcleo de match. |
| **P3** | H43, H44 | Sube la red de seguridad donde hoy es débil (scrapers y UI). |
| **P4** | H45, H46, H47, H48 | Higiene de dependencias y reproducibilidad. |
| **P5** | H41, H49, H50 | Limpieza y documentación. |

---

## 6. Fortalezas confirmadas

- **Integridad de datos sobresaliente:** 0 nulos, 100 % "Confirmado", 0 inconsistencias de precio (`$/L`, promos, ahorros, duplicados).
- **Ética y trazabilidad:** `fuente`, `fecha_consulta` y política de scraping documentada (`docs/politica_scraping.md`).
- **Calidad automatizada real:** 153 pruebas, cobertura 64.51 %, `ruff` limpio, 0 excepciones genéricas ni `except:` desnudos.
- **Cálculo de outliers centralizado y actualizado** (H32/H37), con exclusión explícita en el dashboard.
- **Cross-tienda robusto:** 90 grupos comparables, sin mezcla de tamaños distintos.

---

## 7. Conclusión

La base del proyecto es **sólida y auditable**. Las 37 observaciones históricas están cerradas con evidencia y las 13 nuevas (H38–H50) son de **deuda técnica y limpieza**, sin riesgo funcional inmediato. Con excepción de la regresión H39 (trivial de corregir), el resto puede atenderse de forma incremental sin bloquear la operación.

> **Recomendación:** actuar primero sobre H39 por ser una regresión de bajo costo y alto valor simbólico (recupera una limpieza previa), y planificar H38/H40 como un pequeño refactor del núcleo de comparación.
