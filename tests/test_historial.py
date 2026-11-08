"""
Pruebas unitarias para el gestor y consultor de historial de precios (src/historial.py).
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd

from src.historial import (
    construir_historial_desde_git,
    consultar_historial,
    enriquecer_con_metricas_historicas,
    extraer_archivo_git,
    formatear_tabla_historial,
    normalizar_df_para_historial,
    obtener_snapshots_git,
    registrar_precios_historicos,
)


def test_normalizar_df_para_historial():
    # DataFrame vacío
    df_vacio = normalizar_df_para_historial(pd.DataFrame(), "2026-11-06")
    assert df_vacio.empty
    assert "fecha_dia" in df_vacio.columns

    # DataFrame con datos variados
    df_raw = pd.DataFrame(
        [
            {
                "tienda": "Walmart",
                "producto": "Tequila Don Julio 70 700 ml",
                "marca": "Don Julio",
                "categoria": "Tequila",
                "subcategoria": "Añejo Cristalino",
                "ml": "700",
                "precio_regular": 1100.0,
                "precio_promo": 850.0,
                "condiciones": "Oferta",
                "url": "https://walmart.com.mx/p1",
            },
            {
                "tienda": "Bodegas Alianza",
                "producto": "Mezcal 400 Conejos Joven 750 ml",
                "ml": 750,
                "precio_regular": 400.0,
                "precio_promo": 500.0,  # Regular menor que promo -> debe igualar
                "fecha_consulta": "2026-10-24 15:30",
            },
        ]
    )

    df_norm = normalizar_df_para_historial(df_raw, "2026-11-06")
    assert len(df_norm) == 2
    assert df_norm.loc[0, "fecha_dia"] == "2026-11-06"
    assert df_norm.loc[1, "fecha_dia"] == "2026-10-24"
    assert df_norm.loc[0, "precio_por_litro"] == round(850.0 / 0.7, 2)
    assert df_norm.loc[0, "ahorro_verificable"] == 250.0
    # Caso 2: regular corregido a promo
    assert df_norm.loc[1, "precio_regular"] == 500.0


def test_registrar_precios_historicos(tmp_path: Path):
    ruta_hist = str(tmp_path / "historial_test.csv")

    df_lote1 = pd.DataFrame(
        [
            {
                "fecha_consulta": "2026-10-15 10:00",
                "tienda": "Soriana",
                "producto": "Whisky Black & White 700 ml",
                "ml": 700,
                "precio_regular": 350.0,
                "precio_promo": 280.0,
            }
        ]
    )

    # Registro en archivo nuevo
    df_res1 = registrar_precios_historicos(df_lote1, ruta_hist)
    assert len(df_res1) == 1
    assert Path(ruta_hist).exists()

    # Segundo lote con nuevo producto y un duplicado de la misma fecha
    df_lote2 = pd.DataFrame(
        [
            {
                "fecha_consulta": "2026-10-15 12:00",  # Misma fecha_dia (2026-10-15)
                "tienda": "Soriana",
                "producto": "Whisky Black & White 700 ml",
                "ml": 700,
                "precio_regular": 350.0,
                "precio_promo": 270.0,  # Actualiza precio
            },
            {
                "fecha_consulta": "2026-11-06 18:00",
                "tienda": "Soriana",
                "producto": "Whisky Black & White 700 ml",
                "ml": 700,
                "precio_regular": 350.0,
                "precio_promo": 260.0,
            },
        ]
    )

    df_res2 = registrar_precios_historicos(df_lote2, ruta_hist)
    # Debe haber 2 registros: uno del 2026-10-15 y otro del 2026-11-06
    assert len(df_res2) == 2
    filas_oct15 = df_res2[df_res2["fecha_dia"] == "2026-10-15"]
    assert len(filas_oct15) == 1
    assert filas_oct15.iloc[0]["precio_promo"] == 270.0


def test_consultar_historial(tmp_path: Path):
    ruta_hist = str(tmp_path / "historial_test.csv")
    df_datos = pd.DataFrame(
        [
            {
                "fecha_dia": "2026-10-15",
                "fecha_consulta": "2026-10-15 10:00",
                "tienda": "Walmart",
                "producto": "Tequila Herradura Ultra 700 ml",
                "ml": 700,
                "precio_regular": 950.0,
                "precio_promo": 750.0,
                "precio_por_litro": 1071.43,
                "condiciones": "Promo",
                "url": "",
            },
            {
                "fecha_dia": "2026-10-24",
                "fecha_consulta": "2026-10-24 10:00",
                "tienda": "Bodegas Alianza",
                "producto": "Tequila Herradura Ultra 700 ml",
                "ml": 700,
                "precio_regular": 890.0,
                "precio_promo": 623.0,
                "precio_por_litro": 890.0,
                "condiciones": "Descuento",
                "url": "",
            },
            {
                "fecha_dia": "2026-10-24",
                "fecha_consulta": "2026-10-24 10:00",
                "tienda": "Costco",
                "producto": "Mezcal Montelobos 750 ml",
                "ml": 750,
                "precio_regular": 600.0,
                "precio_promo": 550.0,
                "precio_por_litro": 733.33,
                "condiciones": "Regular",
                "url": "",
            },
        ]
    )
    df_datos.to_csv(ruta_hist, index=False)

    # Consulta solo por producto
    res_herradura = consultar_historial("Herradura Ultra", ruta_historial=ruta_hist)
    assert len(res_herradura) == 2

    # Consulta con filtro de tienda
    res_alianza = consultar_historial("Herradura Ultra", tienda="Alianza", ruta_historial=ruta_hist)
    assert len(res_alianza) == 1
    assert res_alianza.iloc[0]["tienda"] == "Bodegas Alianza"


def test_formatear_tabla_historial():
    df_vacio = pd.DataFrame()
    txt_vacio = formatear_tabla_historial(df_vacio)
    assert "No se encontraron" in txt_vacio

    df = pd.DataFrame(
        [
            {
                "fecha_dia": "2026-10-24",
                "tienda": "Costco",
                "producto": "Tequila Dobel Diamante 700 ml",
                "ml": 700,
                "precio_regular": 850.0,
                "precio_promo": 699.0,
                "precio_por_litro": 998.57,
                "condiciones": "Cuponera",
            }
        ]
    )
    txt_tabla = formatear_tabla_historial(df)
    assert "Dobel Diamante" in txt_tabla
    assert "699.0" in txt_tabla


def test_obtener_snapshots_git_y_extraer():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            stdout="sha1 2026-10-15\nsha2 2026-10-24\n",
            returncode=0,
        )
        snapshots = obtener_snapshots_git()
        assert len(snapshots) == 2
        assert snapshots[0] == ("sha1", "2026-10-15")
        assert snapshots[1] == ("sha2", "2026-10-24")

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            stdout="tienda,producto,ml,precio_regular,precio_promo\nWalmart,Vino Tinto,750,150,120\n",
            returncode=0,
        )
        df = extraer_archivo_git("sha1", "data/scraped_walmart.csv")
        assert df is not None
        assert len(df) == 1


def test_construir_historial_desde_git_con_mocks(tmp_path: Path):
    ruta_salida = str(tmp_path / "historial_mock.csv")
    with (
        patch("src.historial.obtener_snapshots_git", return_value=[("sha_mock", "2026-10-20")]),
        patch("src.historial.extraer_archivo_git") as mock_extraer,
    ):
        mock_extraer.return_value = pd.DataFrame(
            [
                {
                    "tienda": "Chedraui",
                    "producto": "Tequila 1800 Añejo 700 ml",
                    "ml": 700,
                    "precio_regular": 800.0,
                    "precio_promo": 650.0,
                }
            ]
        )
        df_hist = construir_historial_desde_git(ruta_salida=ruta_salida)
        assert len(df_hist) >= 1
        assert Path(ruta_salida).exists()


def test_enriquecer_con_metricas_historicas():
    df_hist = pd.DataFrame(
        [
            # Producto 1: bajó de 900 a 700 -> minimo_historico
            {
                "fecha_dia": "2026-10-15",
                "tienda": "Walmart",
                "producto": "Tequila Don Julio 70 700 ml",
                "ml": 700,
                "precio_regular": 900.0,
                "precio_promo": 900.0,
            },
            {
                "fecha_dia": "2026-11-06",
                "tienda": "Walmart",
                "producto": "Tequila Don Julio 70 700 ml",
                "ml": 700,
                "precio_regular": 900.0,
                "precio_promo": 700.0,
            },
            # Producto 2: subió regular de 600 a 900 para fingir oferta en 650 -> descuento_inflado
            {
                "fecha_dia": "2026-10-15",
                "tienda": "Chedraui",
                "producto": "Whisky Chivas Regal 12 750 ml",
                "ml": 750,
                "precio_regular": 600.0,
                "precio_promo": 600.0,
            },
            {
                "fecha_dia": "2026-11-06",
                "tienda": "Chedraui",
                "producto": "Whisky Chivas Regal 12 750 ml",
                "ml": 750,
                "precio_regular": 900.0,
                "precio_promo": 650.0,
            },
            # Producto 3: subió de 500 a 580 sin descuento -> subio_vs_minimo
            {
                "fecha_dia": "2026-10-15",
                "tienda": "Soriana",
                "producto": "Ron Bacardi Blanco 980 ml",
                "ml": 980,
                "precio_regular": 580.0,
                "precio_promo": 500.0,
            },
            {
                "fecha_dia": "2026-11-06",
                "tienda": "Soriana",
                "producto": "Ron Bacardi Blanco 980 ml",
                "ml": 980,
                "precio_regular": 580.0,
                "precio_promo": 580.0,
            },
        ]
    )

    df_actual = pd.DataFrame(
        [
            {
                "tienda": "Walmart",
                "producto": "Tequila Don Julio 70 700 ml",
                "ml": 700,
                "precio_regular": 900.0,
                "precio_promo": 700.0,
                "ahorro_verificable": 200.0,
            },
            {
                "tienda": "Chedraui",
                "producto": "Whisky Chivas Regal 12 750 ml",
                "ml": 750,
                "precio_regular": 900.0,
                "precio_promo": 650.0,
                "ahorro_verificable": 250.0,
            },
            {
                "tienda": "Soriana",
                "producto": "Ron Bacardi Blanco 980 ml",
                "ml": 980,
                "precio_regular": 580.0,
                "precio_promo": 580.0,
                "ahorro_verificable": 0.0,
            },
            {
                "tienda": "Costco",
                "producto": "Vino Nuevo Sin Historial 750 ml",
                "ml": 750,
                "precio_regular": 320.0,
                "precio_promo": 320.0,
                "ahorro_verificable": 0.0,
            },
        ]
    )

    df_enriq = enriquecer_con_metricas_historicas(df_actual, df_hist)
    assert df_enriq.loc[0, "semaforo_historico"] == "minimo_historico"
    assert df_enriq.loc[0, "precio_min_historico"] == 700.0
    assert df_enriq.loc[0, "precio_max_historico"] == 900.0

    assert df_enriq.loc[1, "semaforo_historico"] == "descuento_inflado"
    assert df_enriq.loc[1, "precio_reg_min_historico"] == 600.0

    assert df_enriq.loc[2, "semaforo_historico"] == "subio_vs_minimo"
    assert df_enriq.loc[2, "precio_min_historico"] == 500.0

    assert df_enriq.loc[3, "semaforo_historico"] == "nuevo"
