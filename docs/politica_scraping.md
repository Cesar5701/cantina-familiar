# Política de Scraping Ético y Gobernanza de Datos (H17)

**Proyecto:** Cantina Familiar — Sistema de Apoyo a la Decisión de Compra Navideña  
**Fecha de emisión:** Octubre 2026  
**Ámbito:** Extracción automatizada, auditoría y análisis de precios minoristas de bebidas en México.

---

## 1. Principios Fundamentales y Propósito

El sistema *Cantina Familiar* tiene como único objetivo asistir en la **optimización de presupuesto y decisión de compra familiar para eventos privados y no comerciales** (Navidad y Año Nuevo).

1. **Uso no comercial y estrictamente personal:** La información recopilada no se revende, no se distribuye a terceros para lucro ni se utiliza para actividades comerciales de arbitraje competitivo.
2. **Minimización de impacto en servidores:** Cada petición efectuada a comercios en línea debe conducirse con cortesía digital, evitando la saturación de ancho de banda o recursos de cómputo de los proveedores.
3. **Privacidad absoluta:** Únicamente se extraen datos de catálogo público (precios, descripciones, volúmenes de botellas y disponibilidad en inventario). Jamás se recopilan datos de usuarios, compradores, cuentas ni sesiones privadas.

---

## 2. Jerarquía de Fuentes y Métodos de Extracción

Para garantizar la máxima estabilidad y respeto a los sistemas de los comercios minoristas, se establece el siguiente orden estricto de prelación:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. APIs Públicas / Endpoints VTEX (Preferente)              │
│    - Bodegas Alianza, Chedraui                              │
│    - Cero renderizado de interfaz, payload mínimo JSON      │
└──────────────────────────────┬──────────────────────────────┘
                               │ (si no existe API oficial)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Extracción Estática de SSR / __NEXT_DATA__               │
│    - Sam's Club, Walmart, Soriana                           │
│    - Descarga de HTML sin ejecución continua de JavaScript  │
└──────────────────────────────┬──────────────────────────────┘
                               │ (solo en contingencia / HITL)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Automatización con Navegador (Selenium - No Oficial)     │
│    - Modo asistido (Human-in-the-Loop)                      │
│    - Frágil, no programable en bucles desatendidos          │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Respeto a `robots.txt` y Cortesía de Red

1. **Cumplimiento de robots.txt:**
   - Se revisan y respetan las directrices de `robots.txt` de los sitios consultados.
   - Para **Bodegas Alianza**, la consulta se realiza contra sus endpoints públicos de búsqueda de catálogo catalogados en el sitemap de productos.
2. **Control de Frecuencia y Delays Aleatorios (Jitter):**
   - El sistema implementa pausas obligatorias entre consultas consecutivas (`1.0 s` a `3.0 s`).
   - El módulo `src/http_utils.py` incorpora retrasos exponenciales con fluctuación estocástica (*full jitter*), reduciendo la probabilidad de sincronización de peticiones o picos de tráfico concurrentes.
3. **Manejo Responsable de Errores HTTP (Backoff Exponencial):**
   - Ante respuestas de saturación (`HTTP 429 Too Many Requests` o `HTTP 503 Service Unavailable`), el sistema aplica una pausa progresiva multiplicativa antes de reintentar.
   - Si un endpoint falla de forma repetida (límite de 3 reintentos agotado), el proceso se detiene de inmediato para esa fuente sin insistir.
4. **Horarios de Extracción:**
   - Se recomienda ejecutar el pipeline de actualización en horas de baja demanda comercial (ej. 23:00 a 06:00 hrs CST).

---

## 4. Política sobre Scrapers Dinámicos y Evasión (Selenium)

El módulo `src/scraper_selenium.py` incluye mecanismos para interactuar con aplicaciones de página única (SPA) que requieren interacción manual o hidratación en el cliente:

> [!WARNING]
> **Aviso de Fragilidad y Uso Asistido (HITL):**  
> Cualquier método que modifique banderas del navegador (`navigator.webdriver`, `--disable-blink-features=AutomationControlled`) o que requiera resolver desafíos CAPTCHA se considera **estrictamente de contingencia asistida por humanos (Human-in-the-Loop)** y **no oficial**.

- **No desatendido:** Este módulo no debe configurarse en cron jobs desatendidos ni ejecutarse de manera periódica sin supervisión activa.
- **Términos de Servicio (ToS):** Ciertas tiendas en línea restringen la extracción masiva automatizada en sus términos y condiciones. Si una tienda bloquea explícitamente el acceso o activa retos de seguridad, el operador debe suspender la extracción para dicho comercio y registrar la cotización de forma manual en `data/bebidas_verificadas.csv`.
- **Cero evasión de paywalls o autenticación:** No se accede a áreas privadas ni se violan credenciales de acceso restringido.

---

## 5. Gobernanza y Retención de Datos

1. **Almacenamiento Local y Efímero:**
   - Los datos brutos recolectados residen localmente en el directorio `data/`.
   - No se publican volcados masivos innecesarios en repositorios de control de versiones git (restringidos mediante `.gitignore`).
2. **Escrituras Atómicas:**
   - La persistencia se realiza mediante archivos temporales con reemplazo atómico (`src/io_utils.py`), garantizando que un fallo de red o caída de proceso nunca corrompa datasets consolidados previos.
3. **Trazabilidad y Auditoría:**
   - Cada registro conserva su `fecha_consulta`, `tienda` y `url` de origen para permitir la verificación manual de precios por cualquier miembro de la familia antes de efectuar la compra definitiva.
