"""
Suite de pruebas smoke y de integridad de UI/JS para el Dashboard BI (H44).
Verifica la estructura del DOM, presencia de controles reactivos, atributos data-*
y coherencia del JavaScript embebido sin depender de un navegador headless.
"""

import json

from bs4 import BeautifulSoup

from src.generar_dashboard_v4 import INDEX_HTML_PATH, TEMPLATE_PATH, renderizar_plantilla


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
    assert soup.find(id="filtro-paquete") is not None

    # 4. Inputs de presupuesto
    assert soup.find(id="input-presupuesto-global") is not None
    assert soup.find(id="input-cooperadores-global") is not None

    # 5. Simulador versus y arbitraje
    assert soup.find(id="select-versus-macro") is not None
    assert soup.find(id="select-versus-a") is not None
    assert soup.find(id="select-versus-b") is not None
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
    }
    html = renderizar_plantilla(template_str, datos_json_str=json.dumps([item_test]))

    assert "__DATA_JSON__" not in html
    assert '"Whisky Johnnie Walker Black 750 ml"' in html


def test_dashboard_smoke_funciones_javascript_criticas():
    """Valida la presencia de las funciones JS esenciales de UI y lógica de negocio (H44)."""
    template_str = TEMPLATE_PATH.read_text(encoding="utf-8")

    funciones_esperadas = [
        "function actualizarSubtiposCatalogo",
        "function aplicarFiltros",
        "function ordenarPor",
        "function actualizarEstadoOrden",
        "function agregarDesdeTabla",
        "function vaciarCarrito",
        "function actualizarVersus",
        "function renderizarTabla",
        "function nombreSinCategoria",
        "function toggleModalCrossTienda",
        "function cerrarModalCrossTienda",
    ]

    for fn in funciones_esperadas:
        assert fn in template_str, f"Función JavaScript crítica no encontrada en el template: {fn}"


def test_dashboard_smoke_index_html_produccion():
    """Smoke test del artefacto publicado index.html para asegurar integridad en producción (H44)."""
    if not INDEX_HTML_PATH.exists():
        return

    contenido = INDEX_HTML_PATH.read_text(encoding="utf-8")
    assert len(contenido) > 500_000, "El dashboard publicado index.html está anormalmente pequeño o incompleto"
    assert "<!DOCTYPE html>" in contenido
    assert "Cantina Familiar" in contenido
    assert "__DATA_JSON__" not in contenido
    assert "__CORTE_AUDITORIA__" not in contenido
    assert "__RESUMEN_WHATSAPP_VIGENCIAS__" not in contenido
