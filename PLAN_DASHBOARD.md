# Plan de Trabajo — Mejoras del Catálogo General Normalizado

**Proyecto:** Cantina Familiar
**Fecha:** 16 de octubre de 2026
**Estado:** ✅ Fases 1, 2, 3 (Opción A) y 4 (Verificación y Cierre) completadas al 100% y verificadas (117 pruebas pasadas, cobertura 56.77%, ruff 100% limpio)
**Archivos objetivo:** `src/templates/dashboard_template.html`, `src/clasificacion.py`, `src/actualizar_dashboard_completo.py`, `tests/`

---

## 1. Objetivo

Resolver tres problemas del bloque **"Catálogo General Normalizado"** del dashboard:

1. **Estado de los botones de orden** — solo uno puede estar activo y su estado debe ser visible.
2. **Redundancia de nombre y enlace** — no repetir la categoría en el nombre ni duplicar el enlace en la última columna.
3. **Normalización de medidas en los nombres** — unificar el espaciado de **todas** las medidas (`ml` y `L`, enteros y decimales) para que productos equivalentes no se traten como distintos.

---

## 2. Diagnóstico (con evidencia)

### Problema 1 — Botones de orden sin estado visible
- `dashboard_template.html:448` → botón *"Menor $/Litro"* con clase `md3-btn-tonal` **fija** (siempre parece activo).
- `dashboard_template.html:451` → botón *"Precio Botella"* con `bg-white border` **fija** (nunca se ve activo).
- `ordenarPor(col)` (`dashboard_template.html:2024`) actualiza el estado interno (`columnaOrden`, `ordenAsc`) pero **no repinta los botones**.
- No hay indicador de dirección (asc/desc).

### Problema 2 — Redundancia de categoría y de enlace
- **800 de 860** productos empiezan con la misma palabra que ya aparece en la columna *"Categoría & Tipo"* (`categoria_comparable`, `dashboard_template.html:2092`). Ej.: `"Tequila Herradura…"` con categoría `Tequila`.
- El enlace a la tienda aparece **dos veces**: en el nombre (`<a>`, líneas 2079-2084) y como botón `↗` en la columna *Acción* (líneas 2104-2108), ambos con `item.url`.
- La línea secundaria ya muestra `item.marca` (línea 2086), que en muchos casos reaparece dentro del nombre.

### Problema 3 — Espaciado de medidas inconsistente
- **167 de 860** nombres traen la medida pegada (`700ml`); el resto viene separada (`700 ml`).
- `normalizar_texto_clave()` (`analizador.py:43`) parte por espacios y ordena tokens: `"700 ml"` → `["700","ml"]`; `"700ml"` → `["700ml"]` ⇒ **claves distintas**.
- Impacto medido al normalizar: **48 claves comparativas se fusionan** (797 → 749). Ejemplos reales:
  - `Mezcal Jurame Joven 100% Salmiana 750 ml` ≠ `Mezcal Júrame - 100% Salmiana Joven 750ml`
  - `Whisky Chivas Regal 12 Años 750 ml` ≠ `Whisky Chivas Regal 12 Años 750ml`
  - `Tequila 1800 Añejo Cristalino 700 ml` ≠ `Tequila 1800 Cristalino Añejo 700ml`

---

## 3. Fase 1 — Normalización de medidas (capa de datos)

> Se resuelve en datos (no en pantalla) porque también corrige el *matching* cross-tienda y la deduplicación.

### Alcance (actualizado)

Aplica a **cualquier medida**, en cualquier unidad y formato:

- **Mililitros:** `500`, `600`, `700`, `750`, `946`, `375`, etc. (y decimales como `187.5`)
- **Litros:** `1`, `1.5`, `1.75`, `4`, `5`, etc.
- **Unidades equivalentes (se unifican):**
  - mililitros → `ml`, `mL`, `ML`, `mls`, `mililitro(s)`, `cc`
  - litros → `l`, `L`, `lt`, `lts`, `litro`, `litros`
- **Pegado o separado:** `700ml`, `700 ml`, `1.75L`, `1.75 l`, `1.75 lt`, `4 litros`.
- **Múltiples medidas en un mismo nombre:** `"Mezcal Jurame Joven 750 ml C/Reposado 375ml"`.

### Reglas de normalización (actualizadas)

1. **Insertar un espacio** entre el número y la unidad cuando estén pegados.
2. **Unificar la unidad y el valor** según el volumen real de la medida:
   - Si el volumen es **< 1000 ml** → se expresa en **`ml`**.
     Ej.: `0.75L` → `750 ml`, `946ml` → `946 ml`, `1.75 l` → *ver siguiente caso (es ≥ 1000)*.
   - Si el volumen es **≥ 1000 ml** → se expresa en **`L`**.
     Ej.: `1000ml` → `1 L`, `1500 ml` → `1.5 L`, `1.75 lt` → `1.75 L`, `5 litros` → `5 L`.
   - Formato de `L`: sin ceros finales (`1 L`, `1.5 L`, `1.75 L`, `4 L`).
3. **Unidad estandarizada:** `ml` en minúsculas; `L` en mayúscula.
4. Colapsar espacios múltiples sobrantes.
5. **Idempotente:** aplicarla dos veces produce el mismo resultado.

> Esta regla sirve para dos fines: "que no se vean diferentes" y que `"1000 ml"` y `"1 L"` (o `"1.75 l"` y `"1.75 L"`) generen la **misma clave comparativa**.

Algoritmo propuesto (variantes más largas primero; `ml` antes que `l` para no partir el "l" de "ml"):

```python
U_ML = r"mililitros|mililitro|mls|ml|cc"
U_L = r"litros|litro|lts|lt|l"
patron = re.compile(rf"(?P<num>\d+(?:[.,]\d+)?)\s*(?P<u>{U_ML}|{U_L})\b", re.I)

# por cada match:
#   ml = float(num)*1000  si u en {"l","lt","lts","litro","litros"}
#   ml = float(num)       si u es de mililitros
#   si ml >= 1000:  f"{ml/1000:.3f}".rstrip('0').rstrip('.') + " L"
#   si ml <  1000:  f"{int(ml)} ml"  (o con decimal si aplica)
```

### Matriz de pruebas (T3)

| Entrada | Salida esperada |
|---|---|
| `Tequila X 700ml` | `Tequila X 700 ml` |
| `Tequila X 700 ml` | `Tequila X 700 ml` (sin cambio) |
| `Mezcal Y 750ML` | `Mezcal Y 750 ml` |
| `Whisky Z 1.75L` | `Whisky Z 1.75 L` |
| `Whisky Z 1.75 lt` | `Whisky Z 1.75 L` |
| `Whisky Z 1.75 litros` | `Whisky Z 1.75 L` |
| `Vino W 1.5 l` | `Vino W 1.5 L` |
| `Garrafa 4L` | `Garrafa 4 L` |
| `Garrafa 5 litros` | `Garrafa 5 L` |
| `Tetra 946ml` | `Tetra 946 ml` |
| `Tetra 999 ml` | `Tetra 999 ml` (límite, sin cambio) |
| `Botella 1000ml` | `Botella 1 L` |
| `Pack 1500 ml` | `Pack 1.5 L` |
| `Medida 0.75L` | `Medida 750 ml` |
| `Medida 187.5 ml` | `Medida 187.5 ml` (sin cambio) |
| `Mezcal J 750 ml C/Reposado 375ml` | `Mezcal J 750 ml C/Reposado 375 ml` |
| `Tequila 1800 Añejo` | `Tequila 1800 Añejo` (sin cambio) |
| `Siete Leguas` | `Siete Leguas` (sin cambio) |
| `Tequila 100% Agave` | `Tequila 100% Agave` (sin cambio) |

### Tareas

| # | Tarea | Archivo | Criterio de aceptación |
|---|---|---|---|
| T1 | Nueva función `normalizar_medidas_en_nombre(nombre: str) -> str` que separa, unifica unidad (`ml`/`L`/`lt`/`lts`/`litros`/`cc`), convierte `<1000 ml → ml` y `≥1000 ml → L`, y es idempotente | `src/clasificacion.py` | Pasa toda la matriz de pruebas |
| T2 | Aplicarla a la columna `producto` **antes** del dedup y de `detectar_duplicados` | `src/actualizar_dashboard_completo.py` (~línea 96) | Ninguna medida con unidad no estandarizada sobrevive; `extraer_ml()` **no cambia** para ninguna fila |
| T3 | Pruebas unitarias con la matriz completa | `tests/test_clasificacion.py` | Pasan; cobertura ≥ 50 % |
| T4 | Regenerar y validar | local | Claves comparativas ≈ 797 → 749; ~190 nombres cambian de texto; **0 cambios en `ml`** |

**Notas de decisión abierta:**
- ¿Aplico la normalización también en los scrapers (a los `scraped_*.csv`)? **Recomendación: no** — dejar el dato crudo tal cual y normalizar en la consolidación.

### Aclaración importante: nombre ≠ volumen

La Fase 1 **solo modifica el texto del nombre** (separa la medida y unifica la unidad). **No suma ni recalcula volúmenes.** El `ml` de la columna se calcula aparte con `extraer_ml()` (`clasificacion.py:197`), que toma la **primera** medida encontrada.

Comprobado con datos reales (`data/catalogo_completo_consolidado.csv`):

| Hecho | Resultado |
|---|---|
| Nombres cuyo texto cambia al normalizar | 190 de 860 |
| Filas cuyo **`ml` extraído cambia** | **0 de 860** |
| Productos con 2+ medidas en el nombre | 36 |
| Su `ml` en la tabla | primera medida (700 / 750 / 940…), **nunca la suma** |
| Combos cuyo `ml` cambiaría al normalizar | **0 de 36** |
| Combos involucrados en las 48 fusiones | **0** |

Por tanto, `"Mezcal Jurame Joven 750 ml C/Reposado 375ml"` pasará a `"… C/Reposado 375 ml"` **en el texto**, pero seguirá mostrando **750 ml** de volumen, exactamente como hoy.

### Hallazgo relacionado (fuera del alcance de Fase 1): combos de dos medidas

Existen **36 productos que en realidad son paquetes** (una botella + otra distinta), p. ej.:
- `Tequila Herradura Cristal 700 ml C/Ultra 375 ml`
- `Tequila Don Julio 70 Añejo 700 ml C/Traviesa & Tremenda Sangria 750 ml`
- `Tequila Solarum Extra Añejo Cristalino 750 ml + Reposado 750 ml`

Hoy se registran con **una sola medida** (la primera) y el **precio del paquete completo**, por lo que su **precio por litro queda distorsionado** (se divide el precio del combo entre la primera medida, aunque el paquete trae más de un líquido). Es un comportamiento **previo** e independiente de la Fase 1.

Opciones a decidir como tarea futura:
- **Opción 1.** Dejarlo como está (primera medida).
- **Opción 2.** Marcar `es_bundle` y **excluir del $/L** comparativo (tratarlos como los outliers).
- **Opción 3.** Tratarlos aparte sin sumar (son líquidos/tipos distintos).

---

## 4. Fase 2 — Botones de orden con estado visible

| # | Tarea | Archivo | Criterio de aceptación |
|---|---|---|---|
| T5 | Unificar ambos botones con clase base + clase *activa* alternable (activo = tonal relleno; inactivo = blanco con borde) | `dashboard_template.html:446-454` | Ambos con el mismo aspecto en reposo |
| T6 | Nueva `actualizarEstadoOrden()` que marca activo **solo** el botón de `columnaOrden` y muestra `↑`/`↓` según `ordenAsc`; se llama al inicio y dentro de `ordenarPor()` | `dashboard_template.html` (~2024) | Al pulsar "Precio Botella" este se activa y "Menor $/Litro" se apaga; alternar dirección cambia la flecha |
| T7 *(opcional)* | Reflejar estado en los encabezados clicables *Precio* / *$Litro* (`aria-sort` + resaltado) | `dashboard_template.html:464-465` | Encabezado activo resaltado |

**Exclusividad garantizada:** el estado es una sola variable (`columnaOrden`), así que solo un botón puede quedar activo.

---

## 5. Fase 3 — Quitar redundancias de la tabla

| # | Tarea | Archivo | Criterio de aceptación |
|---|---|---|---|
| T8 | Mostrar el nombre **sin la palabra inicial de categoría** cuando coincida con `categoria` (helper JS en el render) | `dashboard_template.html:2077-2090` | `"Tequila Herradura…"` se ve `"Herradura…"`; la categoría sigue en su columna |
| T9 | Eliminar el enlace `↗` duplicado de la columna *Acción*, dejando solo **+ Carrito** | `dashboard_template.html:2104-2108` | Columna Acción con un único control; el nombre sigue siendo el enlace |
| T10 *(opcional)* | Quitar la línea inferior `marca` si queda redundante tras T8 | `dashboard_template.html:2085-2088` | Sin duplicar la marca |

**Decisión abierta (Problema 2):** "solo deja la marca" admite dos lecturas:
- **Opción A (recomendada):** quitar solo la **palabra de categoría** inicial → `"Herradura Selección Suprema 750 ml"` (conserva variante).
- **Opción B:** mostrar **solo `marca`** → `"Herradura"` (pierde variante en el nombre; el tipo sigue en su columna).

---

## 6. Fase 4 — Verificación y cierre

| # | Tarea | Criterio | Estado |
|---|---|---|---|
| T11 | `python src/actualizar_dashboard_completo.py` + `python src/generar_dashboard_v4.py` | Datos y `index.html` regenerados | ✅ Completado (760 botellas en dashboard, 985 en consolidado) |
| T12 | `pytest --cov=src`, `ruff check .`, `ruff format --check .` | Todo en verde, cobertura ≥ 50 % | ✅ Completado (117 tests pasados, cobertura 56.77 %, ruff limpio) |
| T13 | Revisión visual (preview) del catálogo: botones, nombres, medidas, sin enlace duplicado | Confirmado en pantalla | ✅ Confirmado (10/10 puntos del checklist visual verificados) |
| T14 | Actualizar `AUDITORIA_V2.md` / README si aplica | Documentado | ✅ Documentado con trazabilidad técnica |

### Resumen de Métricas de Verificación (Fase 1 a 4)
- **Cambios en `ml` calculado:** `0` (100% de coherencia).
- **Medidas pegadas residuales:** `0` (todas unificadas a formato `\d+ ml` o `\d+ L`).
- **Nombres únicos normalizados:** 277 corregidos en el catálogo fuente.
- **Claves comparativas fusionadas:** 49 claves redundantes colapsadas a coincidencias exactas.
- **Outliers en ranking:** 0 (137 marcados como ultra-lujo en consolidado, ranking limpio con 848 botellas).
- **Cross-tienda:** 166 registros correspondientes a 70 productos únicos disponibles en múltiples tiendas.
- **Autocontención:** `index.html` sin placeholders y sin scripts/archivos locales externos.

---

## 7. Orden de ejecución

1. **Fase 1** (datos) — base de todo. ✅
2. **Fase 2** y **Fase 3** (presentación, estado visible de orden y sin redundancias). ✅
3. **Fase 4** (verificación integral, regeneración y documentación de cierre). ✅

## 8. Riesgos y mitigaciones

| Riesgo | Mitigación | Resultado |
|---|---|---|
| Fase 1 fusiona filas en consolidado/ranking | Regenerar y revisar de nuevo outliers y cross-tienda | ✅ Verificado: 0 outliers en ranking, 70 grupos cross-tienda |
| Regex de `L` afecta palabras | Anclar con número delante y `\b`; cubierto por matriz de pruebas | ✅ Verificado: 20 tests unitarios específicos pasando |
| JS del template **no** está cubierto por pytest | Validación visual obligatoria (T13) | ✅ Verificado: funciones e interactividad validadas |
| Fusión reduce el conteo de "botellas verificadas" | Es el comportamiento deseado; documentar el nuevo conteo | ✅ Verificado y documentado |

---

*Fases 1, 2, 3 y 4 completadas satisfactoriamente el 16 de octubre de 2026.*
