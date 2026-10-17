# Auditoría Técnica V3 (Final) — Verificación Total y Estado de Cierre

**Proyecto:** Cantina Familiar — Sistema de Apoyo a la Decisión de Compra Navideña 2026
**Fecha:** 17 de octubre de 2026
**Auditorías base:** [`AUDITORIA.md`](./AUDITORIA.md) (H1–H20) y [`AUDITORIA_V2.md`](./AUDITORIA_V2.md) (H21–H31)
**Tipo:** Auditoría de solo lectura. No se modificó ningún archivo del proyecto.

---

## 1. Resumen ejecutivo

Esta es la **auditoría de cierre**. Verifica:

1. Que **los 31 hallazgos acumulados (H1–H31)** están resueltos.
2. La **integridad de las listas y sus precios** (catálogo, ranking y dashboard).
3. El estado general del proyecto para descubrir hallazgos residuales.

### Resultados

> ✅ **H1–H31: los 31 hallazgos están resueltos y verificados.**
> ✅ **Precios y listas: sin inconsistencias** (0 errores de precio detectados).
> 🟢 **Nuevos hallazgos: 6 (H32–H37), ninguno crítico** — todos de mantenibilidad, datos o alcance diferido.

**Métricas actuales del proyecto:**

| Métrica | Valor |
|---|---|
| Líneas `src/*.py` | 3,412 |
| Líneas `tests/*.py` | 1,577 |
| Pruebas | **120 passed** |
| Cobertura | **56.62 %** (umbral `fail_under = 50`) |
| `ruff check` / `ruff format --check` | ✅ limpio |
| `print()` en `src/` | 0 |
| Filas consolidadas / dashboard / ranking | 1,004 / 775 / 866 |
| Outliers de lujo marcados | 138 (0 en ranking) |
| Grupos cross-tienda | 87 |

---

## 2. Metodología

- Relectura de `AUDITORIA.md` y `AUDITORIA_V2.md`; verificación uno por uno con evidencia.
- Ejecución de la suite, cobertura y linters.
- **Auditoría de integridad de precios** sobre `catalogo_completo_consolidado.csv`, `ranking_completo_general.csv` y `dashboard_data.json`.
- Escaneo de datos: cross-tienda, combos, duplicados.
- Revisión de código: excepciones, constantes, cobertura, código muerto.

---

## 3. Verificación de los 31 hallazgos (H1–H31)

### 3.1 Hallazgos de la primera auditoría (H1–H20)

| # | Hallazgo | Estado | Evidencia |
|---|---|---|---|
| H1 | Clasificación NOM duplicada | ✅ | Único `src/clasificacion.py`; nadie reimplementa `clasificar_*`. |
| H2 | `extraer_ml` triplicada | ✅ | Una sola definición en `clasificacion.py`. |
| H3 | Generadores huérfanos | ✅ | Solo `generar_dashboard_v4.py`; `legacy/` eliminado. |
| H4 | Ruta absoluta hardcodeada | ✅ | Sin `/home/` en `src/`. |
| H5 | `index.html` copia manual | ✅ | Generado desde plantilla única. |
| H6 | Multipacks mal normalizados | ✅ | `Pack 6`, `Pack x 3`, `(8 Bot)` cubiertos y probados. |
| H7 | Precio ausente → `$/L = 0` | ✅ | `np.nan`; ranking excluye nulos. |
| H8 | `es_duplicado` no marcado | ✅ | `clave_comparativa` + cross-tienda (87 grupos). |
| H9 | Sin validación de esquema/rangos | ✅ | `validar_esquema_y_rangos()` activo. |
| H10 | Escritura no atómica | ✅ | `io_utils.guardar_csv/json_atomico` en todo el pipeline. |
| H11 | Testing limitado | ✅ | 5 suites + `conftest.py`. |
| H12 | `numpy` fuera de requirements | ✅ | En `requirements.txt`. |
| H13 | Sin linter/CI/paquete | ✅ | `pyproject.toml`, ruff, CI, pre-commit. |
| H14 | README desactualizado | ✅ | README con pipeline, estructura y 120 pruebas. |
| H15 | Artefactos versionados | ✅ | `index.html`/CSV consolidados en `.gitignore`. |
| H16 | `debug_page.html` rastreado | ✅ | No rastreado. |
| H17 | Sin política de scraping | ✅ | `docs/politica_scraping.md`. |
| H18 | CSV huérfano | ✅ | Carpeta `legacy/` eliminada. |
| H19 | `print` en producción | ✅ | 0 `print(` en `src/`. |
| H20 | Sin retries/backoff | ✅ | `http_utils.py` con backoff + jitter. |

### 3.2 Hallazgos de la segunda auditoría (H21–H31)

| # | Hallazgo | Estado | Evidencia |
|---|---|---|---|
| H21 | Clave comparativa rota con `ml` float | ✅ | `analizador.py:138-140` usa `float()` + `round()` con chequeo de `NaN`. |
| H22 | Validación no aplicada / mensaje hardcodeado | ✅ | `actualizar_dashboard_completo.py:130-135` filtra `datos_validos` y muestra el conteo real de anomalías. |
| H23 | Doble normalización de producto | ✅ | Dedup y comparativa usan `normalizar_texto_clave` (`:112`). |
| H24 | Cobertura sin umbral | ✅ | `fail_under = 50`; cobertura actual 56.62 %. |
| H25 | Outliers de lujo | ✅ | `marcar_outliers_lujo` + exclusión en ranking (0/866). |
| H26 | Grupo Mezcal duplicado | ✅ | 1 sola definición de “Mezcal - Silvestre”. |
| H27 | `extraer_precio_texto` duplicada | ✅ | Eliminada; se usa `limpiar_precio`. |
| H28 | Constantes de red duplicadas | ✅ | UA centralizados en `http_utils.py`. |
| H29 | Monolito del dashboard | ✅ | `generar_dashboard_v4.py` = 97 líneas; plantilla en `src/templates/`. |
| H30 | `except Exception: pass` | ✅ | 0 `pass` silenciosos; ahora loguean. |
| H31 | Sin `conftest.py` | ✅ | `tests/conftest.py` con fixtures compartidas. |

---

## 4. Verificación de listas y precios

Auditoría de integridad sobre las tres listas (consolidado, ranking, dashboard):

| Comprobación | Resultado |
|---|---|
| `precio_promo > precio_regular` | **0** |
| `precio_por_litro` inconsistente vs `precio_promo / (ml/1000)` | **0** |
| `ahorro_verificable < 0` | **0** |
| `porcentaje_ahorro` fuera de `[0, 100]` | **0** |
| `precio_promo` nulo o ≤ 0 | **0** |
| Ranking con outliers de lujo | **0** de 866 |
| Coherencia cross-tienda (`precio_promo` vs `precio_minimo_cross`) | **0** errores |
| Duplicados exactos `(tienda, producto)` | **0** |

**Rangos observados:** `precio_promo` 76 – 690,000 MXN (mediana 778); `precio_por_litro` 67 – 985,714 (mediana 993). El máximo es el Royal Salute 51 años, correctamente marcado como outlier y excluido del ranking.

> **Conclusión:** las listas y sus precios son **consistentes y aritméticamente correctos**. No se detectaron precios mal calculados, ahorros negativos ni porcentajes imposibles.

---

## 5. Nuevos hallazgos (H32–H37)

### H32 — Umbrales de precio mágicos y duplicados 🟠

Existen **dos juegos de umbrales hardcodeados y distintos** para clasificar/excluir por precio:

- `marcar_outliers_lujo` (`analizador.py:281-286`): Tequila 3500, Mezcal 3000, Whisky 4000, Vino 1000, Licor 1600 ($/L).
- Filtro del dashboard (`actualizar_dashboard_completo.py:151-155`): Tequila 1950, Mezcal 1500, Whisky 1750, Licor 950, Vino 350/$L o 260.

No hay una fuente única de configuración; un ajuste en uno no se refleja en el otro.

**Recomendación:** extraer a un `CONFIG_UMBRALES` compartido.

### H33 — `except Exception` genéricos 🟡

Persisten ~18 bloqueos genéricos (8 en `scraper_selenium.py`, 3 en `scraper_multitienda.py`, etc.). Ya registran con `logger`, pero siguen ocultando errores inesperados.

**Recomendación:** acotar a excepciones concretas (`TimeoutException`, `ValueError`, `requests.RequestException`).

### H34 — `scraper_selenium.py` excluido de cobertura 🟡

`pyproject.toml` omite `src/scraper_selenium.py` (551 líneas, el módulo más complejo) de la cobertura. Es el componente con mayor riesgo sin red de pruebas.

**Recomendación:** al menos cubrir la lógica de parseo pura (sin navegador).

### H35 — Mismo nombre en 2+ tiendas con `ml` distinto 🟠 (datos)

**26 grupos** tienen el mismo producto (nombre normalizado sin la medida) en 2 o más tiendas pero con **`ml` diferente**, por lo que **no se marcan como comparables**. Puede ser correcto (SKUs de 700 vs 750 ml) o **matches perdidos**.

**Recomendación:** revisar esos 26 casos y, si son el mismo producto, comparar por `$/L` o permitir equivalencia de volumen.

### H36 — Combos de dos medidas (alcance diferido) 🟡

**43 productos** son paquetes con dos medidas (ej. `… 700 ml C/Ultra 375 ml`) y siguen registrando **una sola medida** con el precio del combo → su `$/L` está distorsionado. Documentado y fuera de alcance de las fases previas.

**Recomendación:** decidir política (marcar `es_bundle` y excluir del `$/L` comparativo, o dejarlo explícito).

### H37 — El dashboard no excluye outliers explícitamente 🟡 (latente)

`df_dash = df[cond]` (`actualizar_dashboard_completo.py:157`) filtra por **precio**, no por `es_outlier_lujo`. Hoy **0 outliers entran** (los techos de categoría los cubren), pero el acoplamiento es frágil: una botella pequeña con `$/L` altísimo o un cambio de umbrales podría colarse.

**Recomendación:** `df_dash = df[cond & ~df["es_outlier_lujo"]]`.

---

## 6. Roadmap final

### Prioridad 1 — Datos
| Acción | Hallazgo |
|---|---|
| Revisar los 26 grupos con mismo nombre y `ml` distinto | H35 |
| Excluir outliers explícitamente en el dashboard | H37 |

### Prioridad 2 — Mantenibilidad
| Acción | Hallazgo |
|---|---|
| Centralizar umbrales de precio en configuración única | H32 |
| Acotar excepciones genéricas | H33 |
| Cubrir el parseo de `scraper_selenium.py` | H34 |

### Prioridad 3 — Alcance diferido
| Acción | Hallazgo |
|---|---|
| Política para combos de dos medidas | H36 |

---

## 7. Conclusión

El proyecto está en un **estado sólido y verificable**:

- **31 hallazgos resueltos** (H1–H31), con evidencia en código y datos.
- **Precios y listas sin inconsistencias** (0 errores aritméticos en consolidado, ranking y dashboard).
- **120 pruebas**, cobertura 56.62 %, linters limpios, `print` eliminados y artefactos bien gestionados.

Los 6 hallazgos nuevos (H32–H37) son **menores y no bloqueantes**: dos son de calidad de datos (H35, H37), tres de mantenibilidad (H32–H34) y uno de alcance diferido (H36). **Ninguno impide el uso del sistema.**

---

*Auditoría V3 (final) realizada en modo solo lectura. Reportes previos archivados en `docs/archivo/`.*
