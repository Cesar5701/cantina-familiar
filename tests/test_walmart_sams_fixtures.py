"""
Suite de pruebas unitarias para src/scraper_multitienda/walmart_sams.py
respaldada por fixtures estáticas JSON/HTML congeladas en tests/fixtures/.

Valida:
1. Parsing completo de productos disponibles, agotados, duplicados y descartados desde JSON congelado.
2. Degradación elegante ante payloads malformados o con ramas ausentes (sin itemStacks / searchResult).
3. Detección de desafíos WAF (Akamai / PerimeterX) mediante HTML congelado y activación de contingencias.
4. Descubrimiento por pasillos oficiales, Ruta C (nodriver CDP por lotes) y manejo de errores de red/respaldo.
"""

import json
import urllib.error
from pathlib import Path
from unittest.mock import patch

from selenium.common.exceptions import WebDriverException

from src.io_archivos import ResumenScraping
from src.scraper_multitienda.walmart_sams import (
    _cargar_respaldo_csv,
    _configurar_flag_booleano,
    _ejecutar_contingencia_navegador,
    _generar_clave_producto,
    descubrir_productos_pasillos_walmart,
    es_respuesta_prerender_falsa,
    extraer_item_nextjs,
    scrapear_nextjs_walmart_platform,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ==============================================================================
# 1. PARSING DE FIXTURE DE ÉXITO Y DEGRADACIÓN ANTE MALFORMADOS
# ==============================================================================


def test_scrapear_walmart_con_fixture_nextjs_exito(tmp_path):
    """Valida el parsing integral de items en stock, agotados, duplicados y filtrados desde walmart_nextjs_exito.json."""
    raw_json = (FIXTURES_DIR / "walmart_nextjs_exito.json").read_text(encoding="utf-8")
    html_exito = f'<html><body><script id="__NEXT_DATA__" type="application/json">{raw_json}</script></body></html>'

    csv_previo = tmp_path / "scraped_walmart_base.csv"
    csv_previo.write_text(
        "tienda,producto,marca,categoria,subcategoria,ml,precio_regular,precio_promo,disponibilidad,url\n"
        "Walmart,Tequila Don Julio 70 Añejo Cristalino 700 ml,Don Julio,Tequila,Añejo Cristalino,700,1049.0,899.0,disponible,https://www.walmart.com.mx/ip/tequila-don-julio-70-700-ml/wm_exito_001\n",
        encoding="utf-8",
    )

    with (
        patch("src.scraper_multitienda.walmart_sams.descargar_html_con_reintentos", return_value=html_exito),
        patch("time.sleep") as mock_sleep,
    ):
        resultados = scrapear_nextjs_walmart_platform(
            tienda="Walmart",
            base_domain="www.walmart.com.mx",
            terminos=["tequila", "mezcal"],
            ruta_respaldo=str(csv_previo),
            explorar_pasillos=False,
            usar_fallback_selenium=False,
            pausar=True,
            delay_min=0.01,
            delay_max=0.02,
        )

    # De los 6 items del fixture:
    # - wm_exito_001 (Don Julio 70) -> válido
    # - wm_exito_001 duplicado -> ignorado por ids_vistos
    # - wm_exito_002 (Mezcal 400 Conejos) -> válido
    # - wm_agotado_003 (Buchanan's agotado) -> descartado por agotado
    # - wm_descarte_004 (Refresco de Cola) -> descartado por filtro categoría NOM
    # - Item sin usItemId -> ignorado
    assert len(resultados) == 2
    por_nombre = {r["producto"]: r for r in resultados}

    dj = por_nombre["Tequila Don Julio 70 Añejo Cristalino 700 ml"]
    assert dj["precio_promo"] == 829.0
    assert dj["precio_regular"] == 1049.0
    assert "Ahorra $220.00" in dj["condiciones"]
    assert dj["disponibilidad"] == "disponible"
    assert dj["url"] == "https://www.walmart.com.mx/ip/tequila-don-julio-70-700-ml/wm_exito_001"

    mezcal = por_nombre["Mezcal 400 Conejos Joven Espadín 750 ml"]
    assert mezcal["precio_promo"] == 525.0
    assert mezcal["precio_regular"] == 525.0
    assert mezcal["condiciones"] == "Precio regular Walmart"

    # Al haber 2 términos con pausar=True, se ejecuta la pausa de cortesía entre el 1ro y el 2do
    mock_sleep.assert_called_once()


def test_scrapear_walmart_con_fixture_malformado_sin_excepciones():
    """Valida que payloads sin props, sin searchResult o sin itemStacks degraden elegantemente sin KeyError."""
    malformados = json.loads((FIXTURES_DIR / "walmart_nextjs_malformado.json").read_text(encoding="utf-8"))["variantes"]

    respuestas_html = [
        f'<html><script id="__NEXT_DATA__" type="application/json">{json.dumps(payload)}</script></html>'
        for payload in malformados.values()
    ]

    with patch("src.scraper_multitienda.walmart_sams.descargar_html_con_reintentos", side_effect=respuestas_html):
        resultados = scrapear_nextjs_walmart_platform(
            tienda="Walmart",
            base_domain="www.walmart.com.mx",
            terminos=list(malformados.keys()),
            explorar_pasillos=False,
            usar_fallback_selenium=False,
            pausar=False,
        )

    assert resultados == []


def test_extraer_item_nextjs_entradas_invalidas_y_agotado_conservado():
    """Valida guardas defensivas en extraer_item_nextjs para tipos no dict, sin nombre y agotados no descartados."""
    assert extraer_item_nextjs(None, "Walmart", "www.walmart.com.mx", "2026-11-10") == (None, False)  # type: ignore[arg-type]
    assert extraer_item_nextjs({}, "Walmart", "www.walmart.com.mx", "2026-11-10") == (None, False)

    # Producto agotado cuando descartar_agotados=False y tienda Sam's Club sin rebaja
    item_sams = {
        "title": "Tequila Herradura Añejo 750 ml",
        "brand": "Herradura",
        "isOutOfStock": True,
        "priceInfo": {"linePrice": "$680.00"},
    }
    norm, agotado = extraer_item_nextjs(
        it=item_sams,
        tienda="Sam's Club",
        base_domain="www.sams.com.mx",
        fecha_actual="2026-11-10 12:00",
        descartar_agotados=False,
    )
    assert agotado is True
    assert norm is not None
    assert norm["disponibilidad"] == "agotado"
    assert norm["condiciones"] == "Precio socio Sam's Club"


# ==============================================================================
# 2. DETECCIÓN DE DESAFÍOS WAF Y CONTINGENCIAS CON FIXTURE HTML
# ==============================================================================


def test_desafio_waf_con_y_sin_respaldo_activa_circuit_breaker_y_contingencia(tmp_path):
    """Verifica el manejo de sams_nextjs_desafio.html con respaldo (Circuit Breaker) y sin respaldo (Contingencia)."""
    html_desafio = (FIXTURES_DIR / "sams_nextjs_desafio.html").read_text(encoding="utf-8")
    # HTML que contiene el texto '__NEXT_DATA__' en el cuerpo pero carece de etiqueta <script id="__NEXT_DATA__">
    html_sin_script = "<html><body><div>Referencia texto __NEXT_DATA__ sin etiqueta script</div></body></html>"

    # A) Con archivo de respaldo existente: activa Circuit Breaker inmediato y conserva catálogo previo
    csv_respaldo = tmp_path / "scraped_sams_previo.csv"
    csv_respaldo.write_text(
        "tienda,producto,marca,categoria,subcategoria,ml,precio_regular,precio_promo,disponibilidad,url\n"
        "Sam's Club,Tequila Don Julio 70 Añejo Cristalino 700 ml,Don Julio,Tequila,Añejo Cristalino,700,1049.0,829.0,disponible,https://www.sams.com.mx/ip/dj70/1\n",
        encoding="utf-8",
    )
    with patch("src.scraper_multitienda.walmart_sams.descargar_html_con_reintentos", return_value=html_desafio) as m_dl:
        res_cb = scrapear_nextjs_walmart_platform(
            tienda="Sam's Club",
            base_domain="www.sams.com.mx",
            terminos=["tequila", "whisky"],
            ruta_respaldo=str(csv_respaldo),
            explorar_pasillos=False,
            usar_fallback_selenium=False,
            pausar=False,
        )
    assert m_dl.call_count == 1
    assert len(res_cb) == 1

    # B) Sin archivo de respaldo: registra errores de red/parseo y salta a contingencia Selenium
    prods_contingencia = [
        {
            "producto": "Whisky Johnnie Walker Black Label 750 ml",
            "marca": "Johnnie Walker",
            "precio_promo": "$750.00",
            "precio_regular": "$600.00",  # menor que promo -> debe ajustarse a p_reg = p_promo
            "disponibilidad": "disponible",
            "url": "https://www.sams.com.mx/ip/jw-black/999",
        },
        {
            "producto": "Agua Mineral 600 ml",  # No licor -> descartado en contingencia
            "marca": "Manantial",
            "precio_promo": "$18.00",
            "disponibilidad": "disponible",
        },
    ]

    with (
        patch(
            "src.scraper_multitienda.walmart_sams.descargar_html_con_reintentos",
            side_effect=[html_desafio, None, html_sin_script],
        ),
        patch(
            "src.scraper_multitienda.walmart_sams.consultar_urls_secuenciales",
            return_value=prods_contingencia,
        ) as mock_sel,
        patch("time.sleep"),
    ):
        resultados = scrapear_nextjs_walmart_platform(
            tienda="Sam's Club",
            base_domain="www.sams.com.mx",
            terminos=["whisky", "tequila", "mezcal"],
            ruta_respaldo=None,
            explorar_pasillos=False,
            usar_fallback_selenium=True,
            headless_selenium=True,
            pausar=False,
        )

    assert mock_sel.call_count == 1
    assert len(resultados) == 1
    assert resultados[0]["precio_promo"] == 750.0
    assert resultados[0]["precio_regular"] == 750.0


def test_ejecutar_contingencia_navegador_ruta_c_nodriver_por_lotes():
    """Valida la Ruta C con nodriver CDP agrupando PDPs conocidas por categoría y enfriamiento entre lotes."""
    catalogo = {
        "walmart|tequila don julio 70 añejo cristalino 700 ml|700": {
            "tienda": "Walmart",
            "producto": "Tequila Don Julio 70 Añejo Cristalino 700 ml",
            "categoria": "Tequila",
            "url": "https://www.walmart.com.mx/ip/don-julio-70/001",
        },
        "walmart|ron zacapa 23 750 ml|750": {
            "tienda": "Walmart",
            "producto": "Ron Zacapa 23 750 ml",
            "categoria": "Ron",  # Categoría fuera de lista estándar -> se agrupa en 'Otros'
            "url": "https://www.walmart.com.mx/ip/ron-zacapa/002",
        },
        "walmart|url externa invalida|750": {
            "tienda": "Walmart",
            "producto": "Tequila Externo 750 ml",
            "categoria": "Tequila",
            "url": "https://otro-dominio.com/ip/externo/003",  # No coincide con base_domain
        },
        "walmart|url sin ip|750": {
            "tienda": "Walmart",
            "producto": "Tequila Sin IP 750 ml",
            "categoria": "Tequila",
            "url": "https://www.walmart.com.mx/browse/licores",  # No contiene /ip/
        },
    }
    resumen = ResumenScraping("Walmart")

    lote_tequila = [
        {
            "producto": "Tequila Don Julio 70 Añejo Cristalino 700 ml",
            "marca": "Don Julio",
            "precio_promo": 815.0,
            "precio_regular": 990.0,
            "disponibilidad": "disponible",
            "url": "https://www.walmart.com.mx/ip/don-julio-70/001",
        },
        {
            "producto": "Mezcal Ojo de Tigre Reposado 750 ml",
            "marca": "Ojo de Tigre",
            "precio_promo": 510.0,
            "precio_regular": 620.0,
            "disponibilidad": "disponible",
            "url": "https://www.walmart.com.mx/ip/ojo-de-tigre/004",
        },
    ]

    # El primer lote (Tequila) actualiza 1 existente e inserta 1 nuevo; el segundo lote (Otros) lanza RuntimeError
    with (
        patch(
            "src.scraper_multitienda.walmart_sams.consultar_pdps_con_nodriver",
            side_effect=[lote_tequila, RuntimeError("Fallo temporal CDP")],
        ) as mock_cdp,
        patch("time.sleep") as mock_sleep,
    ):
        act, ins = _ejecutar_contingencia_navegador(
            tienda="Walmart",
            base_domain="www.walmart.com.mx",
            terminos=["tequila"],
            catalogo_acumulado=catalogo,
            resumen=resumen,
            fecha_actual="2026-11-10 12:00",
            headless=True,
            pausar=True,
        )

    assert mock_cdp.call_count == 2
    assert act == 1
    assert ins == 1
    mock_sleep.assert_called_once_with(5.0)


def test_ejecutar_contingencia_navegador_fallo_webdriver():
    """Valida que si Selenium lanza WebDriverException, se capture limpiamente retornando (0, 0)."""
    resumen = ResumenScraping("Sam's Club")
    with patch(
        "src.scraper_multitienda.walmart_sams.consultar_urls_secuenciales",
        side_effect=WebDriverException("Sin binario de navegador"),
    ):
        act, ins = _ejecutar_contingencia_navegador(
            tienda="Sam's Club",
            base_domain="www.sams.com.mx",
            terminos=["tequila"],
            catalogo_acumulado={},
            resumen=resumen,
            fecha_actual="2026-11-10 12:00",
            headless=True,
            pausar=False,
        )
    assert (act, ins) == (0, 0)


# ==============================================================================
# 3. DESCUBRIMIENTO POR PASILLOS Y EXCEPCIONES DE RED / RESPALDO
# ==============================================================================


def test_descubrir_productos_pasillos_casos_borde(monkeypatch):
    """Valida todas las ramas de descubrir_productos_pasillos_walmart: fallback HTTP, sin script, agotados y errores."""
    monkeypatch.setenv("WALMART_MAX_PAGINAS_PASILLO", "1")
    html_desafio = (FIXTURES_DIR / "sams_nextjs_desafio.html").read_text(encoding="utf-8")
    raw_exito = (FIXTURES_DIR / "walmart_nextjs_exito.json").read_text(encoding="utf-8")
    html_exito = f'<html><script id="__NEXT_DATA__">{raw_exito}</script></html>'
    html_sin_next = "<html><body><div>Contenido con palabra __NEXT_DATA__ pero sin script</div></body></html>"
    html_script_vacio = '<html><body><script id="__NEXT_DATA__"></script></body></html>'
    html_json_roto = '<html><body><script id="__NEXT_DATA__">{json_invalido</script></body></html>'
    html_sin_cambios = (
        '<html><body><script id="__NEXT_DATA__">'
        '{"props":{"pageProps":{"initialData":{"searchResult":{"itemStacks":[{"items":[]}]}}}}}'
        "</script></body></html>"
    )

    pasillos_prueba = {
        "Pasillo_Exito": "/browse/exito",
        "Pasillo_WAF": "/browse/waf",
        "Pasillo_SinScript": "/browse/sin-script",
        "Pasillo_ScriptVacio": "/browse/vacio",
        "Pasillo_JsonRoto": "/browse/roto",
        "Pasillo_SinNuevos": "/browse/sin-nuevos",
    }

    # Para Pasillo_Exito: curl_cffi devuelve None -> activa fallback descargar_html_con_reintentos que devuelve html_exito
    curl_effects = [
        None,
        html_desafio,
        html_sin_next,
        html_script_vacio,
        html_json_roto,
        html_sin_cambios,
    ]
    http_effects = [
        html_exito,
        html_desafio,
    ]

    catalogo: dict[str, dict] = {}
    resumen = ResumenScraping("Walmart")

    with (
        patch("src.scraper_multitienda.walmart_sams.peticion_curl_cffi", side_effect=curl_effects),
        patch("src.scraper_multitienda.walmart_sams.descargar_html_con_reintentos", side_effect=http_effects),
        patch("time.sleep") as mock_sleep,
    ):
        act, ins = descubrir_productos_pasillos_walmart(
            tienda="Walmart",
            base_domain="www.walmart.com.mx",
            catalogo_acumulado=catalogo,
            resumen=resumen,
            fecha_actual="2026-11-10 12:00",
            pasillos=pasillos_prueba,
            max_paginas=None,
            delay_min=0.01,
            delay_max=0.02,
            pausar=True,
        )

    # En Pasillo_Exito el fixture tiene 2 productos válidos (y 1 duplicado que actualiza al mismo en la misma pasada)
    assert ins == 2
    assert act == 1
    assert len(catalogo) == 2
    mock_sleep.assert_called_once()


def test_excepciones_red_y_fallback_respaldo_final(tmp_path):
    """Valida la captura de errores de conexión durante la búsqueda y la carga de respaldo al final."""
    csv_respaldo = tmp_path / "respaldo_emergencia.csv"
    csv_respaldo.write_text(
        "tienda,producto,marca,categoria,subcategoria,ml,precio_regular,precio_promo,disponibilidad,url\n"
        "Walmart,Tequila Siete Leguas Blanco 700 ml,Siete Leguas,Tequila,Blanco,700,850.0,720.0,disponible,https://www.walmart.com.mx/ip/7leguas/1\n",
        encoding="utf-8",
    )

    with (
        patch("src.scraper_multitienda.walmart_sams.descubrir_productos_pasillos_walmart", return_value=(0, 0)),
        patch(
            "src.scraper_multitienda.walmart_sams.descargar_html_con_reintentos",
            side_effect=[urllib.error.URLError("DNS lookup failed"), TimeoutError("Read timed out")],
        ),
        # Simular que en la carga inicial devuelve [] y en el bloque de respaldo final devuelve los datos
        patch(
            "src.scraper_multitienda.walmart_sams._cargar_respaldo_csv",
            side_effect=[[], [{"tienda": "Walmart", "producto": "Tequila Siete Leguas Blanco 700 ml"}]],
        ),
        patch("time.sleep") as mock_sleep,
    ):
        resultados = scrapear_nextjs_walmart_platform(
            tienda="Walmart",
            base_domain="www.walmart.com.mx",
            terminos=["tequila", "mezcal"],
            ruta_respaldo=str(csv_respaldo),
            explorar_pasillos=True,
            usar_fallback_selenium=False,
            pausar=True,
        )

    assert len(resultados) == 1
    assert resultados[0]["producto"] == "Tequila Siete Leguas Blanco 700 ml"
    mock_sleep.assert_called_once()


# ==============================================================================
# 4. FUNCIONES AUXILIARES (PRERENDER, CLAVE, FLAGS, RESPALDO CORRUPTO)
# ==============================================================================


def test_auxiliares_prerender_claves_flags_y_respaldo(tmp_path, monkeypatch):
    """Cubre casos borde en funciones auxiliares de walmart_sams.py."""
    # 1. es_respuesta_prerender_falsa: entrada no dict, término corto (<3 chars) y detección por título
    assert es_respuesta_prerender_falsa(None, "tequila") == (False, "")  # type: ignore[arg-type]
    assert es_respuesta_prerender_falsa({}, "ab") == (False, "")
    data_titulo_falso = {
        "query": {},
        "props": {"pageProps": {"initialData": {"searchResult": {"title": 'Resultados para "avena quaker"'}}}},
    }
    es_falso, det = es_respuesta_prerender_falsa(data_titulo_falso, "tequila")
    assert es_falso is True
    assert "avena quaker" in det

    # 2. _cargar_respaldo_csv: ruta inexistente y error de lectura (ej. pasando un directorio)
    assert _cargar_respaldo_csv(None) == []
    assert _cargar_respaldo_csv(str(tmp_path / "no_existe.csv")) == []
    assert _cargar_respaldo_csv(str(tmp_path)) == []

    # 3. _generar_clave_producto: fallback a URL normalizada cuando falta tienda o producto
    clave_url = _generar_clave_producto({"url": "https://www.walmart.com.mx/ip/don-julio/001/"})
    assert clave_url == "walmart.com.mx/ip/don-julio/001"

    # 4. _configurar_flag_booleano: lectura desde variable de entorno y valor por defecto
    monkeypatch.setenv("TEST_FLAG_BOOL", "true")
    assert _configurar_flag_booleano(None, "TEST_FLAG_BOOL", False) is True
    monkeypatch.setenv("TEST_FLAG_BOOL", "0")
    assert _configurar_flag_booleano(None, "TEST_FLAG_BOOL", True) is False
    monkeypatch.delenv("TEST_FLAG_BOOL", raising=False)
    assert _configurar_flag_booleano(None, "TEST_FLAG_BOOL", True) is True
