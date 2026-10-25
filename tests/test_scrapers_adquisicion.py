"""
Suite de pruebas unitarias exhaustivas para la capa de adquisición (H43):
- scraper_multitienda (evaluar_y_normalizar_producto, Chedraui, Walmart, Sam's Club, Soriana)
- scraper_catalogo_completo (procesar_catalogo_completo con mocks VTEX)
- scraper_alianza (consultar_api_alianza con manejo defensivo)
"""

import json
from unittest.mock import patch

from src.scraper_alianza import consultar_api_alianza
from src.scraper_catalogo_completo import procesar_catalogo_completo
from src.scraper_multitienda import (
    evaluar_y_normalizar_producto,
    scrapear_chedraui,
    scrapear_costco,
    scrapear_nextjs_walmart_platform,
    scrapear_soriana,
)

# ==============================================================================
# 1. PRUEBAS DE NORMALIZACIÓN Y CLASIFICACIÓN MULTITIENDA
# ==============================================================================


def test_evaluar_y_normalizar_producto_tequilas():
    """Valida la clasificación de Tequilas permitidos (Añejo Cristalino, Reposado Cristalino, Añejo Tradicional)."""
    fecha = "2026-10-17 12:00"

    # Añejo Cristalino
    dobel = evaluar_y_normalizar_producto(
        tienda="Walmart",
        nombre="Tequila Maestro Dobel Diamante 700 ml",
        marca="Maestro Dobel",
        precio_regular=800.0,
        precio_promo=650.0,
        disponible="disponible",
        url="https://walmart.com/dobel",
        condicion="Oferta",
        fuente="Walmart",
        fecha_actual=fecha,
    )
    assert dobel is not None
    assert dobel["categoria"] == "Tequila"
    assert dobel["subcategoria"] == "Añejo Cristalino"
    assert dobel["precio_promo"] == 650.0
    assert dobel["ml"] == 700

    # Reposado Cristalino
    mayorazgo = evaluar_y_normalizar_producto(
        tienda="Chedraui",
        nombre="Tequila Mayorazgo Cristalino 750 ml",
        marca="Mayorazgo",
        precio_regular=550.0,
        precio_promo=430.0,
        disponible="disponible",
        url="https://chedraui.com/mayorazgo",
        condicion="Precio regular",
        fuente="Chedraui",
        fecha_actual=fecha,
    )
    assert mayorazgo is not None
    assert mayorazgo["subcategoria"] == "Reposado Cristalino"

    # Añejo Tradicional
    herradura = evaluar_y_normalizar_producto(
        tienda="Soriana",
        nombre="Tequila Herradura Añejo 750 ml",
        marca="Herradura",
        precio_regular=920.0,
        precio_promo=780.0,
        disponible="disponible",
        url="https://soriana.com/herradura",
        condicion="Descuento",
        fuente="Soriana",
        fecha_actual=fecha,
    )
    assert herradura is not None
    assert herradura["subcategoria"] == "Añejo Tradicional"


def test_evaluar_y_normalizar_producto_mezcales():
    """Valida la clasificación de Mezcales (Silvestres, Reposados, Añejos, Espadín Joven)."""
    fecha = "2026-10-17 12:00"

    # Silvestre
    tobala = evaluar_y_normalizar_producto(
        tienda="Walmart",
        nombre="Mezcal Ojo de Tigre Tobalá Silvestre 750 ml",
        marca="Ojo de Tigre",
        precio_regular=850.0,
        precio_promo=720.0,
        disponible="disponible",
        url="https://walmart.com/tobala",
        condicion="Oferta",
        fuente="Walmart",
        fecha_actual=fecha,
    )
    assert tobala is not None
    assert tobala["categoria"] == "Mezcal"
    assert tobala["subcategoria"] == "Silvestre"

    # Reposado
    zignum = evaluar_y_normalizar_producto(
        tienda="Bodegas Alianza",
        nombre="Mezcal Zignum Reposado 700 ml",
        marca="Zignum",
        precio_regular=620.0,
        precio_promo=510.0,
        disponible="disponible",
        url="https://alianza.com/zignum",
        condicion="Precio regular",
        fuente="Bodegas Alianza",
        fecha_actual=fecha,
    )
    assert zignum is not None
    assert zignum["subcategoria"] == "Reposado"

    # Espadín Joven
    conejos = evaluar_y_normalizar_producto(
        tienda="Sam's Club",
        nombre="Mezcal 400 Conejos Espadín Joven 750 ml",
        marca="400 Conejos",
        precio_regular=600.0,
        precio_promo=499.0,
        disponible="disponible",
        url="https://sams.com/400conejos",
        condicion="Precio socio",
        fuente="Sam's Club",
        fecha_actual=fecha,
    )
    assert conejos is not None
    assert conejos["subcategoria"] == "Espadín Joven"


def test_evaluar_y_normalizar_producto_whiskies_y_licores():
    """Valida la clasificación de Whisky Blended Scotch y Licores Honey."""
    fecha = "2026-10-17 12:00"

    # Blended Scotch
    jw = evaluar_y_normalizar_producto(
        tienda="Chedraui",
        nombre="Whisky Johnnie Walker Black Label 750 ml",
        marca="Johnnie Walker",
        precio_regular=900.0,
        precio_promo=750.0,
        disponible="disponible",
        url="https://chedraui.com/jw",
        condicion="Oferta",
        fuente="Chedraui",
        fecha_actual=fecha,
    )
    assert jw is not None
    assert jw["categoria"] == "Whisky"
    assert jw["subcategoria"] == "Blended Scotch"

    # Honey Liqueur (Jack Daniel's Honey)
    jd_honey = evaluar_y_normalizar_producto(
        tienda="Walmart",
        nombre="Whiskey Jack Daniel's Honey Tennessee 700 ml",
        marca="Jack Daniel's",
        precio_regular=550.0,
        precio_promo=440.0,
        disponible="disponible",
        url="https://walmart.com/jd-honey",
        condicion="Oferta",
        fuente="Walmart",
        fecha_actual=fecha,
    )
    assert jd_honey is not None
    assert jd_honey["categoria"] == "Licor de Whisky"
    assert jd_honey["subcategoria"] == "Honey Liqueur"


def test_evaluar_y_normalizar_producto_vinos_tintos():
    """Valida la clasificación de Vino Tinto Clericot y garrafas familiares."""
    fecha = "2026-10-17 12:00"

    # Botella estándar económica
    vino = evaluar_y_normalizar_producto(
        tienda="Soriana",
        nombre="Vino Tinto Concha y Toro Reservado Cabernet 750 ml",
        marca="Concha y Toro",
        precio_regular=180.0,
        precio_promo=135.0,
        disponible="disponible",
        url="https://soriana.com/vino",
        condicion="Precio regular",
        fuente="Soriana",
        fecha_actual=fecha,
    )
    assert vino is not None
    assert vino["categoria"] == "Vino"
    assert vino["subcategoria"] == "Tinto Clericot"

    # Garrafa familiar (3L)
    garrafa = evaluar_y_normalizar_producto(
        tienda="Sam's Club",
        nombre="Vino Tinto Carlo Rossi 3 L",
        marca="Carlo Rossi",
        precio_regular=420.0,
        precio_promo=360.0,
        disponible="disponible",
        url="https://sams.com/rossi",
        condicion="Precio socio",
        fuente="Sam's Club",
        fecha_actual=fecha,
    )
    assert garrafa is not None
    assert garrafa["categoria"] == "Vino"
    assert garrafa["ml"] == 3000


def test_evaluar_y_normalizar_producto_descartes():
    """Valida los filtros defensivos de descarte de productos no deseados."""
    fecha = "2026-10-17 12:00"

    # Nombre muy corto
    assert (
        evaluar_y_normalizar_producto("Tienda", "Teq", "M", 500, 400, "disponible", "https://x.com", "O", "F", fecha)
        is None
    )

    # Miniatura < 650 ml
    assert (
        evaluar_y_normalizar_producto(
            "Tienda",
            "Tequila Don Julio 70 50 ml miniatura",
            "M",
            120,
            90,
            "disponible",
            "https://x.com",
            "O",
            "F",
            fecha,
        )
        is None
    )

    # Mercancía no bebible
    assert (
        evaluar_y_normalizar_producto(
            "Tienda",
            "Vaso tequilero caballito 750 ml vidrio",
            "M",
            200,
            150,
            "disponible",
            "https://x.com",
            "O",
            "F",
            fecha,
        )
        is None
    )

    # Bebida excluida (Vodka, Ron, Ginebra)
    assert (
        evaluar_y_normalizar_producto(
            "Tienda",
            "Vodka Smirnoff Tamarindo 750 ml",
            "Smirnoff",
            300,
            240,
            "disponible",
            "https://x.com",
            "O",
            "F",
            fecha,
        )
        is None
    )

    # Precio inválido o menor a umbral mínimo ($50)
    assert (
        evaluar_y_normalizar_producto(
            "Tienda",
            "Tequila Don Julio 70 700 ml",
            "M",
            40,
            30,
            "disponible",
            "https://x.com",
            "O",
            "F",
            fecha,
        )
        is None
    )

    # Tequila Blanco o Reposado tradicional (fuera del alcance familiar)
    assert (
        evaluar_y_normalizar_producto(
            "Tienda",
            "Tequila Don Ramón Blanco Plata 750 ml",
            "Don Ramón",
            350,
            280,
            "disponible",
            "https://x.com",
            "O",
            "F",
            fecha,
        )
        is None
    )

    # Vino blanco descartado
    assert (
        evaluar_y_normalizar_producto(
            "Tienda",
            "Vino Blanco Chardonnay Concha y Toro 750 ml",
            "Concha y Toro",
            200,
            160,
            "disponible",
            "https://x.com",
            "O",
            "F",
            fecha,
        )
        is None
    )


# ==============================================================================
# 2. PRUEBAS DE SCRAPERS MULTITIENDA CON MOCKS
# ==============================================================================


def test_scrapear_chedraui_mock_exitoso():
    """Valida la ejecución de scrapear_chedraui con respuesta mock de la API VTEX (H43)."""
    mock_item = [
        {
            "productId": "12345",
            "productName": "Tequila Maestro Dobel Diamante 700 ml",
            "brand": "Maestro Dobel",
            "link": "https://chedraui.com.mx/dobel",
            "items": [
                {
                    "sellers": [
                        {
                            "commertialOffer": {
                                "Price": 629.0,
                                "ListPrice": 799.0,
                                "AvailableQuantity": 8,
                            }
                        }
                    ]
                }
            ],
        },
        # Item agotado (debe descartarse)
        {
            "productId": "67890",
            "productName": "Tequila Herradura Añejo 750 ml",
            "brand": "Herradura",
            "link": "https://chedraui.com.mx/herradura",
            "items": [
                {
                    "sellers": [
                        {
                            "commertialOffer": {
                                "Price": 700.0,
                                "ListPrice": 850.0,
                                "AvailableQuantity": 0,
                            }
                        }
                    ]
                }
            ],
        },
    ]

    with patch("src.scraper_multitienda.descargar_json_con_reintentos", return_value=mock_item):
        resultados = scrapear_chedraui(terminos=["tequila cristalino"])
        assert len(resultados) == 1
        p = resultados[0]
        assert p["tienda"] == "Chedraui"
        assert p["producto"] == "Tequila Maestro Dobel Diamante 700 ml"
        assert p["precio_promo"] == 629.0
        assert p["precio_regular"] == 799.0
        assert p["disponibilidad"] == "disponible"


def test_scrapear_nextjs_walmart_platform_mock():
    """Valida la extracción desde SSR __NEXT_DATA__ para Walmart y Sam's Club (H43)."""
    next_data = {
        "props": {
            "pageProps": {
                "initialData": {
                    "searchResult": {
                        "itemStacks": [
                            {
                                "items": [
                                    {
                                        "usItemId": "wm_001",
                                        "name": "Tequila Don Julio 70 Añejo Cristalino 700 ml",
                                        "brand": "Don Julio",
                                        "canonicalUrl": "/ip/don-julio-70/wm_001",
                                        "availabilityStatusV2": {"value": "IN_STOCK"},
                                        "priceInfo": {
                                            "linePrice": "$820.00",
                                            "wasPrice": "$990.00",
                                            "savings": "$170",
                                        },
                                    },
                                    # Item agotado
                                    {
                                        "usItemId": "wm_002",
                                        "name": "Whisky Black & White 700 ml",
                                        "availabilityStatusV2": {"value": "OUT_OF_STOCK"},
                                    },
                                ]
                            }
                        ]
                    }
                }
            }
        }
    }
    html = f'<html><script id="__NEXT_DATA__" type="application/json">{json.dumps(next_data)}</script></html>'

    with patch("src.scraper_multitienda.descargar_html_con_reintentos", return_value=html):
        resultados = scrapear_nextjs_walmart_platform(
            tienda="Walmart",
            base_domain="super.walmart.com.mx",
            terminos=["tequila cristalino"],
        )
        assert len(resultados) == 1
        prod = resultados[0]
        assert prod["tienda"] == "Walmart"
        assert prod["producto"] == "Tequila Don Julio 70 Añejo Cristalino 700 ml"
        assert prod["precio_promo"] == 820.0
        assert prod["precio_regular"] == 990.0


def test_scrapear_nextjs_walmart_platform_circuit_breaker_y_respaldo(tmp_path):
    """Valida que ante un reto WAF/PerimeterX se active el Circuit Breaker y cargue el respaldo sin errores."""
    from src.scraper_multitienda.walmart_sams import es_pagina_desafio_waf

    html_waf = "<html><head><title>Verify Your Identity</title></head><body>px-captcha</body></html>"
    assert es_pagina_desafio_waf(html_waf) is True
    assert es_pagina_desafio_waf(None) is True
    assert es_pagina_desafio_waf('<html><script id="__NEXT_DATA__">{}</script></html>') is False

    csv_respaldo = tmp_path / "scraped_sams_mock.csv"
    csv_respaldo.write_text(
        "tienda,producto,marca,categoria,subcategoria,ml,precio_regular,precio_promo,disponibilidad\n"
        "Sam's Club,Tequila Don Julio 70 Añejo Cristalino 700 ml,Don Julio,Tequila,Añejo Cristalino,700,1020.0,846.0,disponible\n",
        encoding="utf-8",
    )

    with patch("src.scraper_multitienda.descargar_html_con_reintentos", return_value=html_waf) as mock_dl:
        resultados = scrapear_nextjs_walmart_platform(
            tienda="Sam's Club",
            base_domain="www.sams.com.mx",
            terminos=["tequila", "mezcal", "whisky"],
            ruta_respaldo=str(csv_respaldo),
        )
        # Circuit breaker debe detenerse en el primer término bloqueado
        assert mock_dl.call_count == 1
        assert len(resultados) == 1
        assert resultados[0]["producto"] == "Tequila Don Julio 70 Añejo Cristalino 700 ml"


def test_scrapear_soriana_mock():
    """Valida la extracción desde HTML Salesforce Commerce Cloud de Soriana (H43)."""
    html_soriana = """
    <html>
      <div class="product-tile">
        <a class="product-tile--link" href="/tequila-herradura-ultra-750-ml">
          Tequila Herradura Ultra Añejo Cristalino 750 ml
        </a>
        <div data-pid="sor_7501005"></div>
        <input name="clevertap-list-price" value="890.00">
        <div class="sales"><span class="cart-price">$699.00</span></div>
      </div>
      <!-- Tile sin enlace válido -->
      <div class="product-tile">
        <div class="sales"><span class="cart-price">$500.00</span></div>
      </div>
    </html>
    """

    with patch("src.scraper_multitienda.descargar_html_con_reintentos", return_value=html_soriana):
        resultados = scrapear_soriana(terminos=["tequila cristalino"])
        assert len(resultados) == 1
        prod = resultados[0]
        assert prod["tienda"] == "Soriana"
        assert "Herradura Ultra" in prod["producto"]
        assert prod["precio_promo"] == 699.0
        assert prod["precio_regular"] == 890.0


def test_scrapear_costco_mock_exitoso():
    """Valida la extracción desde API OCC v2 de SAP Commerce Cloud de Costco (H43)."""
    mock_response = {
        "pagination": {"currentPage": 0, "totalPages": 1, "totalResults": 3},
        "products": [
            {
                "code": "538764",
                "name": "Don Julio 70 Cristalino Tequila 700 ml",
                "price": {"value": 999.0},
                "basePrice": {"value": 1149.0},
                "couponDiscount": {"discountValue": 150.0},
                "stock": {"stockLevelStatus": "inStock"},
                "url": "/tequila/don-julio-70/p/538764",
            },
            # Producto agotado
            {
                "code": "999999",
                "name": "Patrón Tequila Añejo 700 ml",
                "price": {"value": 850.0},
                "stock": {"stockLevelStatus": "outOfStock"},
            },
            # Producto con precio oculto
            {
                "code": "888888",
                "name": "Siete Leguas Tequila Blanco 1 L",
                "hidePriceValue": True,
            },
        ],
    }

    with patch("src.scraper_multitienda.descargar_json_con_reintentos", return_value=mock_response):
        resultados = scrapear_costco(terminos=["tequila cristalino"])
        assert len(resultados) == 1
        p = resultados[0]
        assert p["tienda"] == "Costco"
        assert "Don Julio 70" in p["producto"]
        assert p["precio_promo"] == 999.0
        assert p["precio_regular"] == 1149.0
        assert "Oferta Costco (Ahorra $150.00)" in p["condiciones"]
        assert p["disponibilidad"] == "disponible"
        assert p["url"] == "https://www.costco.com.mx/tequila/don-julio-70/p/538764"


# ==============================================================================
# 3. PRUEBAS DE SCRAPER CATÁLOGO COMPLETO Y ALIANZA
# ==============================================================================


def test_procesar_catalogo_completo_mock():
    """Valida la clasificación exhaustiva de Bodegas Alianza con mock (H43)."""
    mock_items = [
        {
            "productId": "ali_1",
            "productName": "Tequila Maestro Dobel Diamante 700 ml",
            "brand": "Maestro Dobel",
            "link": "https://alianza.com/dobel",
            "items": [
                {
                    "sellers": [
                        {
                            "commertialOffer": {
                                "Price": 615.0,
                                "ListPrice": 780.0,
                                "AvailableQuantity": 10,
                            }
                        }
                    ]
                }
            ],
        },
        {
            "productId": "ali_2",
            "productName": "Mezcal 400 Conejos Espadín Joven 750 ml",
            "brand": "400 Conejos",
            "link": "https://alianza.com/conejos",
            "items": [
                {
                    "sellers": [
                        {
                            "commertialOffer": {
                                "Price": 485.0,
                                "ListPrice": 590.0,
                                "AvailableQuantity": 5,
                            }
                        }
                    ]
                }
            ],
        },
        {
            "productId": "ali_3",
            "productName": "Whisky Johnnie Walker Red Label 700 ml",
            "brand": "Johnnie Walker",
            "link": "https://alianza.com/red",
            "items": [
                {
                    "sellers": [
                        {
                            "commertialOffer": {
                                "Price": 320.0,
                                "ListPrice": 390.0,
                                "AvailableQuantity": 15,
                            }
                        }
                    ]
                }
            ],
        },
    ]

    with patch("src.scraper_catalogo_completo.consultar_endpoint_paginado", return_value=mock_items):
        prods = procesar_catalogo_completo(terminos_busqueda=["tequila"], max_paginas=1)
        assert len(prods) == 3
        cats = {p["categoria"] for p in prods}
        assert cats == {"Tequila", "Mezcal", "Whisky"}


def test_consultar_api_alianza_items_vacios_o_agotados():
    """Valida el manejo defensivo de respuestas incompletas en scraper_alianza."""
    mock_payload = [
        {"productName": "Sin items"},  # items ausente -> descartado
        {"productName": "Con items vacios", "items": []},  # items vacíos -> descartado
        {
            "productName": "Precio Cero",
            "items": [{"sellers": [{"commertialOffer": {"Price": 0.0, "AvailableQuantity": 5}}]}],
        },  # precio <= 0 -> descartado
        {
            "productName": "Tequila Agotado 750 ml",
            "items": [{"sellers": [{"commertialOffer": {"Price": 500.0, "AvailableQuantity": 0}}]}],
        },  # agotado -> se registra con disponibilidad 'agotado'
    ]

    with patch("src.scraper_alianza.descargar_json_con_reintentos", return_value=mock_payload):
        res = consultar_api_alianza("tequila")
        assert len(res) == 1
        assert res[0]["producto"] == "Tequila Agotado 750 ml"
        assert res[0]["disponibilidad"] == "agotado"
