"""
Suite de pruebas smoke y de integridad de UI/JS para el Dashboard BI (H44).
Verifica la estructura del DOM, presencia de controles reactivos, atributos data-*
y coherencia del JavaScript embebido sin depender de un navegador headless.
"""

import base64
import json
import re
import unicodedata

import pytest
from bs4 import BeautifulSoup

from src.generar_dashboard_v4 import (
    DATA_JSON_PATH,
    INDEX_HTML_PATH,
    TEMPLATE_PATH,
    TEMPLATES_DIR,
    cargar_plantilla_dashboard,
    ensamblar_plantilla_modular,
    renderizar_plantilla,
)


def test_dashboard_smoke_renderizado_completo():
    """Valida que renderizar_plantilla produzca un DOM válido con todos los controles principales (H44)."""
    assert TEMPLATE_PATH.exists()
    template_str = TEMPLATE_PATH.read_text(encoding="utf-8")

    datos_muestra = [
        {
            "tienda": "Bodegas Alianza",
            "producto": "Tequila Maestro Dobel Diamante 700 ml",
            "categoria": "Tequila",
            "subcategoria": "Añejo Cristalino",
            "ml": 700,
            "precio_promo": 615.0,
            "precio_regular": 780.0,
            "precio_por_litro": 878.57,
            "es_comparable_cross_tienda": True,
            "es_precio_mas_bajo": True,
            "es_paquete": False,
            "url": "https://alianza.com/dobel",
        }
    ]

    html = renderizar_plantilla(
        template_str,
        datos_json_str=json.dumps(datos_muestra),
        corte_auditoria="Octubre 2026",
        resumen_whatsapp="🟠 Alianza hasta 25 Oct",
    )

    soup = BeautifulSoup(html, "html.parser")

    # 1. Estructura general HTML5
    assert soup.find("html") is not None
    assert soup.find("head") is not None
    assert soup.find("body") is not None

    # 2. Pestañas de navegación
    assert soup.find(id="btn-tab-rankings") is not None
    assert soup.find(id="btn-tab-versus") is not None
    assert soup.find(id="btn-tab-carrito") is not None
    assert soup.find(id="btn-tab-matriz") is not None

    # 3. Controles de filtrado reactivo
    assert soup.find(id="filtro-macro-categoria") is not None
    assert soup.find(id="filtro-categoria") is not None
    assert soup.find(id="filtro-tienda") is not None
    assert soup.find(id="filtro-busqueda") is not None
    assert soup.find(id="filtro-mejor-precio") is not None
    assert soup.find(id="filtro-descuento") is not None
    assert soup.find(id="filtro-minimo-historico") is not None
    assert soup.find(id="filtro-paquete") is not None
    assert soup.find(id="btn-restablecer-filtros") is not None

    # 4. Inputs de presupuesto
    assert soup.find(id="input-presupuesto-global") is not None
    assert soup.find(id="input-cooperadores-global") is not None

    # 5. Simulador versus y arbitraje
    assert soup.find(id="select-versus-macro") is not None
    assert soup.find(id="select-versus-a") is not None
    assert soup.find(id="select-versus-b") is not None
    assert soup.find(id="input-busqueda-versus-a") is not None
    assert soup.find(id="input-busqueda-versus-b") is not None
    assert soup.find(id="select-cross-tienda-duelo") is not None
    assert soup.find(id="versus-tarjetas-container") is not None

    # 6. Tabla, lista móvil y paginación
    assert soup.find(id="tabla-productos-body") is not None
    assert soup.find(id="lista-productos-movil") is not None
    assert soup.find(id="btn-prev") is not None
    assert soup.find(id="btn-next") is not None

    # 7. Atributos data-orden en botones y headers
    botones_orden = soup.select("[data-orden]")
    assert len(botones_orden) >= 2
    atributos_orden = {b["data-orden"] for b in botones_orden}
    assert "precio_por_litro" in atributos_orden
    assert "precio_promo" in atributos_orden

    headers_orden = soup.select("[data-orden-header]")
    assert len(headers_orden) >= 2

    # 8. Modal de Comparativa Cross-Tienda (H8 / H44 / Mobile)
    assert soup.find(id="modal-cross-tienda") is not None
    assert soup.find(id="modal-cross-titulo") is not None
    assert soup.find(id="modal-cross-contenido") is not None


def test_dashboard_smoke_datos_json_embebidos():
    """Valida que los datos JSON embebidos sean válidos y estructurados correctamente (H44)."""
    template_str = TEMPLATE_PATH.read_text(encoding="utf-8")
    item_test = {
        "tienda": "Walmart",
        "producto": "Whisky Johnnie Walker Black 750 ml",
        "categoria": "Whisky",
        "subcategoria": "Blended Scotch",
        "ml": 750,
        "precio_promo": 750.0,
        "precio_por_litro": 1000.0,
        "es_comparable_cross_tienda": True,
        "es_precio_mas_bajo": False,
        "es_paquete": False,
        "ofertas_cross_tienda": [{"tienda": "Walmart", "precio": 750.0}],
    }
    html = renderizar_plantilla(template_str, datos_json_str=json.dumps([item_test]))

    assert "__DATA_JSON__" not in html
    assert '"Whisky Johnnie Walker Black 750 ml"' in html
    assert "ofertas_cross_tienda" not in html


def test_dashboard_smoke_funciones_javascript_criticas():
    """Valida la presencia exacta de las funciones JS esenciales de UI y lógica de negocio (H44 / B5 / P3 / P4.1)."""
    template_str = cargar_plantilla_dashboard()

    funciones_esperadas = [
        "function actualizarSubtiposCatalogo(",
        "function aplicarFiltros(",
        "function restablecerFiltros(",
        "function toggleFiltrosMovil(",
        "function ordenarPor(",
        "function actualizarEstadoOrden(",
        "function agregarDesdeTabla(",
        "function agregarDesdeModalCross(",
        "function agregarDesdeVersus(",
        "function vaciarCarrito(",
        "function guardarCanastaEnStorage(",
        "function cargarCanastaDeStorage(",
        "function sincronizarMetricasGlobalesDOM(",
        "function actualizarSubtiposVersus(",
        "function actualizarVersusManual(",
        "function filtrarOpcionesSelectorVersus(",
        "function intercambiarContendientesVersus(",
        "function cargarDueloDirecto(",
        "function getBadgeSemaforoHistorico(",
        "function renderizarTabla(",
        "function nombreSinCategoria(",
        "function toggleModalCrossTienda(",
        "function cerrarModalCrossTienda(",
    ]

    for fn in funciones_esperadas:
        assert fn in template_str, f"Función JavaScript crítica no encontrada en el template: {fn}"

    # B4: Asegurar que no existan interpolaciones inseguras de nombres de productos en atributos onclick
    assert "agregarAlCarritoPersonalizado('${" not in template_str


def test_dashboard_smoke_index_html_produccion():
    """Smoke test del artefacto publicado index.html para asegurar integridad en producción (H44 / D1)."""
    if not INDEX_HTML_PATH.exists():
        return

    contenido = INDEX_HTML_PATH.read_text(encoding="utf-8")
    assert len(contenido) > 500_000, "El dashboard publicado index.html está anormalmente pequeño o incompleto"
    assert "<!DOCTYPE html>" in contenido
    assert "Cantina Familiar" in contenido
    assert "__DATA_JSON__" not in contenido
    assert "__CAMPANAS_JSON__" not in contenido
    assert "__CORTE_AUDITORIA__" not in contenido
    assert "__RESUMEN_WHATSAPP_VIGENCIAS__" not in contenido
    for fecha_obsoleta in ("25 Oct", "31 Oct", "22 Oct", "Octubre 2026"):
        assert fecha_obsoleta not in contenido, f"Vigencia obsoleta detectada en index.html: {fecha_obsoleta}"


def test_dashboard_accesibilidad_formularios_y_zero_flicker():
    """Verifica que todos los controles de formulario tengan labels accesibles y que exista el script zero-flicker."""
    contenido = cargar_plantilla_dashboard()
    assert "ZERO-FLICKER TAB PRE-RENDER" in contenido
    assert "tab-preload-style" in contenido

    soup = BeautifulSoup(contenido, "html.parser")
    controles = soup.find_all(["input", "select", "textarea"])
    assert len(controles) >= 15

    for ctrl in controles:
        ctrl_id = ctrl.get("id")
        tag = ctrl.name
        has_parent_label = bool(ctrl.find_parent("label"))
        has_for_label = bool(ctrl_id and soup.find("label", attrs={"for": ctrl_id}))
        has_aria = bool(ctrl.get("aria-label") or ctrl.get("aria-labelledby"))
        is_hidden = ctrl.get("aria-hidden") == "true"

        es_accesible = has_parent_label or has_for_label or has_aria or is_hidden
        assert es_accesible, f"Control <{tag} id='{ctrl_id}'> sin etiqueta accesible (a11y)"


def test_arquitectura_modular_plantillas():
    """Valida que los módulos de CSS, parciales HTML y JS existan y se ensamblen sin directivas residuales."""
    modulos_esperados = [
        "css/styles.css",
        "partials/header_y_nav.html",
        "partials/tab_rankings.html",
        "partials/tab_versus.html",
        "partials/tab_carrito.html",
        "partials/tab_matriz.html",
        "partials/footer_y_modales.html",
        "js/01_estado_y_utilidades.js",
        "js/02_modales_y_subtipos.js",
        "js/03_carrito_y_canastas.js",
        "js/04_navegacion_y_catalogo.js",
        "js/05_versus_y_arranque.js",
    ]
    for rel in modulos_esperados:
        ruta = TEMPLATES_DIR / rel
        assert ruta.exists(), f"Falta el submódulo de plantilla: {rel}"
        assert ruta.stat().st_size > 100, f"El submódulo {rel} está vacío"

    ensamblado = cargar_plantilla_dashboard()
    assert "@include" not in ensamblado
    assert len(ensamblado.splitlines()) > 2700


def test_identidad_visual_favicon_y_emblema():
    """Valida que el favicon, el apple-touch-icon y el emblema del agave queden incrustados en el HTML."""
    for rel in ["assets/favicon.svg", "assets/apple-touch-icon.png", "assets/agave_emblema.svg"]:
        assert (TEMPLATES_DIR / rel).exists(), f"Falta el recurso de identidad visual: {rel}"

    ensamblado = cargar_plantilla_dashboard()
    assert "@datauri" not in ensamblado

    soup = BeautifulSoup(ensamblado, "html.parser")
    icono = soup.find("link", rel="icon")
    assert icono is not None
    assert icono["href"].startswith("data:image/svg+xml;base64,")
    favicon_decodificado = base64.b64decode(icono["href"].split(",", 1)[1]).decode("utf-8")
    assert "<svg" in favicon_decodificado

    touch = soup.find("link", rel="apple-touch-icon")
    assert touch is not None
    assert touch["href"].startswith("data:image/png;base64,")

    assert soup.find("meta", attrs={"name": "theme-color"}) is not None

    cabecera = soup.find("header")
    assert cabecera is not None
    assert cabecera.find("svg") is not None, "La cabecera debe mostrar el emblema SVG del agave"


def test_datauri_recurso_inexistente_o_no_soportado(tmp_path):
    """La directiva @datauri falla de forma explícita ante recursos ausentes o de tipo desconocido."""
    with pytest.raises(FileNotFoundError):
        ensamblar_plantilla_modular('<link href="<!-- @datauri no_existe.svg -->">', base_dir=tmp_path)

    (tmp_path / "datos.txt").write_text("hola", encoding="utf-8")
    with pytest.raises(ValueError):
        ensamblar_plantilla_modular('<link href="<!-- @datauri datos.txt -->">', base_dir=tmp_path)


def test_include_anidado_y_circular(tmp_path):
    """Los @include anidados se resuelven y las referencias circulares se detectan."""
    (tmp_path / "a.html").write_text("A[<!-- @include b.html -->]", encoding="utf-8")
    (tmp_path / "b.html").write_text("B", encoding="utf-8")
    assert ensamblar_plantilla_modular("<!-- @include a.html -->", base_dir=tmp_path) == "A[B]"

    (tmp_path / "c.html").write_text("<!-- @include c.html -->", encoding="utf-8")
    with pytest.raises(RecursionError):
        ensamblar_plantilla_modular("<!-- @include c.html -->", base_dir=tmp_path)


def _normalizar_texto_busqueda(s: str) -> str:
    s = unicodedata.normalize("NFD", str(s or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"(\d+)\s*(ml|l|lt|lts|oz|pzas?|pack|paq)\b", r"\1 \2", s)
    s = re.sub(r"['’`]", "", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return s.strip()


def _token_coincide(p_tokens: list[str], q_tok: str) -> bool:
    for pt in p_tokens:
        if pt == q_tok:
            return True
        if len(q_tok) >= 3 and not re.match(r"^\d+$", q_tok) and pt.startswith(q_tok):
            return True
    return False


def _buscar_indice_py(datos: list[dict], prod_kw: str, store_kw: str = "", cat_kw: str = "") -> int:
    q_norm = _normalizar_texto_busqueda(prod_kw)
    s_norm = _normalizar_texto_busqueda(store_kw) if store_kw else ""
    c_norm = _normalizar_texto_busqueda(cat_kw) if cat_kw else ""
    tokens = [t for t in q_norm.split(" ") if t]
    pide_cristalino = "cristalino" in tokens

    def _evaluar(exigir_tienda: bool) -> int:
        mejor_idx = -1
        mejor_puntaje = -999999.0
        for i, d in enumerate(datos):
            if d.get("es_paquete") and not re.search(r"pack|pza|combo|vaso|kit|\+", q_norm):
                continue
            if exigir_tienda and s_norm:
                t_norm = _normalizar_texto_busqueda(d.get("tienda", ""))
                if s_norm not in t_norm:
                    continue
            if c_kw := c_norm:
                cat_d = _normalizar_texto_busqueda(
                    f"{d.get('categoria', '')} {d.get('subcategoria', '')} {d.get('categoria_comparable', '')}"
                )
                if c_kw not in cat_d:
                    continue
            p_norm = _normalizar_texto_busqueda(d.get("producto", ""))
            p_tokens = [t for t in p_norm.split(" ") if t]
            if not all(_token_coincide(p_tokens, tok) for tok in tokens):
                continue
            es_cristalino = "cristalino" in p_tokens or "cristalino" in _normalizar_texto_busqueda(
                d.get("subcategoria", "")
            )
            penalizacion_cristalino = 500.0 if (not pide_cristalino and es_cristalino) else 0.0
            puntaje = (
                (1000.0 if q_norm in p_norm else 0.0)
                - penalizacion_cristalino
                - len(p_norm) * 0.5
                - float(d.get("precio_promo") or 99999) * 0.001
            )
            if puntaje > mejor_puntaje:
                mejor_puntaje = puntaje
                mejor_idx = i
        return mejor_idx

    idx = _evaluar(True)
    if idx != -1:
        return idx
    return _evaluar(False)


def test_integridad_duelos_canastas_y_campos_forenses():
    """Verifica que todos los duelos sugeridos (B2), canastas prearmadas (B3) y campos forenses (D4) existan."""
    if not DATA_JSON_PATH.exists():
        return

    datos = json.loads(DATA_JSON_PATH.read_text(encoding="utf-8"))
    assert len(datos) > 800

    # D4: Verificar que abv, productor y tipo_mezcal estén exportados en el JSON
    muestra = datos[0]
    assert "abv" in muestra
    assert "productor" in muestra
    assert "tipo_mezcal" in muestra

    # B2: Todos los duelos sugeridos en 01_estado_y_utilidades.js deben resolver ambos productos (idx != -1)
    js_01 = (TEMPLATES_DIR / "js" / "01_estado_y_utilidades.js").read_text(encoding="utf-8")
    patron_duelos = re.compile(
        r'\{\s*a:\s*"([^"]+)",\s*storeA:\s*"([^"]+)",\s*b:\s*"([^"]+)",\s*storeB:\s*"([^"]+)",\s*label:\s*"([^"]+)"\s*\}'
    )
    duelos = patron_duelos.findall(js_01)
    assert len(duelos) >= 40
    for a_prod, a_store, b_prod, b_store, label in duelos:
        idx_a = _buscar_indice_py(datos, a_prod, a_store)
        idx_b = _buscar_indice_py(datos, b_prod, b_store)
        assert idx_a != -1, f"Duelo '{label}' falló al resolver lado A: ({a_prod}, {a_store})"
        assert idx_b != -1, f"Duelo '{label}' falló al resolver lado B: ({b_prod}, {b_store})"

    # B3: Todas las búsquedas de construirCanastaDinamica en 03_carrito_y_canastas.js deben resolver (idx != -1)
    js_03 = (TEMPLATES_DIR / "js" / "03_carrito_y_canastas.js").read_text(encoding="utf-8")
    patron_canasta = re.compile(r'buscarIndice\("([^"]+)",\s*"([^"]*)",\s*"([^"]*)"\)')
    busquedas = patron_canasta.findall(js_03)
    assert len(busquedas) >= 18
    for prod_kw, store_kw, cat_kw in busquedas:
        idx = _buscar_indice_py(datos, prod_kw, store_kw, cat_kw)
        assert idx != -1, f"Canasta dinámica falló al resolver: ({prod_kw}, {store_kw}, {cat_kw})"


def test_renderizar_plantilla_neutraliza_payloads_xss():
    """Blinda el dashboard contra XSS almacenado en datos scrapeados, corte y resumen (C1)."""
    template_str = (
        "<p>__CORTE_AUDITORIA__</p>"
        "<script>const DATOS = __DATA_JSON__;</script>"
        "<script>const CAMPANAS = __CAMPANAS_JSON__;</script>"
        "<script>const RESUMEN = `__RESUMEN_WHATSAPP_VIGENCIAS__`;</script>"
    )
    payload_producto = "</script><script>alert(1)</script>"
    payload_campana = "</script><script>alert(2)</script>"
    payload_whatsapp = "Hola `backtick` ${alert(3)} </script><script>alert(4)</script>"
    payload_corte = "<img src=x onerror=alert(5)>"

    html = renderizar_plantilla(
        template_str,
        datos_json_str=json.dumps([{"producto": payload_producto, "url": "javascript:alert(6)"}]),
        corte_auditoria=payload_corte,
        resumen_whatsapp=payload_whatsapp,
        campanas_json_str=json.dumps({"Walmart": {"campana": payload_campana}}),
    )

    assert payload_producto not in html
    assert payload_campana not in html
    assert payload_whatsapp not in html
    assert payload_corte not in html
    assert "\\u003c/script\\u003e" in html
    assert "&lt;img src=x onerror=alert(5)&gt;" in html
    assert "\\`backtick\\`" in html
    assert "\\${alert(3)}" in html


def test_template_incluye_helpers_de_seguridad_js():
    """Verifica que el frontend conserve los helpers de escape y validación de URL (C1/C2)."""
    contenido = cargar_plantilla_dashboard()

    assert "function esc(valor)" in contenido
    assert "function urlSegura(valor)" in contenido
    assert 'href="${urlSegura(' in contenido
