"""
Suite de pruebas unitarias para el generador del dashboard (H29)
y el consolidador integral de datos (H24 / H25).
"""

from pathlib import Path

import pytest

from src.actualizar_dashboard_completo import actualizar_todo
from src.generar_dashboard_v4 import generar_dashboard, renderizar_plantilla
from tests.conftest import crear_df_base


def test_renderizar_plantilla():
    """Valida la sustitución correcta de placeholders en la plantilla HTML (H29)."""
    template = "<html>__DATA_JSON__|__CORTE_AUDITORIA__|__RESUMEN_WHATSAPP_VIGENCIAS__</html>"
    datos_json = '[{"producto": "Tequila Dobel Diamante"}]'
    resultado = renderizar_plantilla(
        template,
        datos_json_str=datos_json,
        corte_auditoria="Noviembre 2026",
        resumen_whatsapp="Vigencias test",
    )
    assert '{"producto": "Tequila Dobel Diamante"}' in resultado
    assert "Noviembre 2026" in resultado
    assert "Vigencias test" in resultado
    assert "__DATA_JSON__" not in resultado


def test_generar_dashboard_archivos_temporales(tmp_path: Path):
    """Valida la ejecución de generar_dashboard escribiendo en rutas personalizadas (H29)."""
    json_file = tmp_path / "datos.json"
    json_file.write_text('[{"producto": "Mezcal Ojo de Tigre", "precio_promo": 520.0}]', encoding="utf-8")

    tpl_file = tmp_path / "template.html"
    tpl_file.write_text("<!DOCTYPE html><div>__DATA_JSON__</div>", encoding="utf-8")

    out_file1 = tmp_path / "out1.html"
    out_file2 = tmp_path / "out2.html"

    res = generar_dashboard(
        data_json_path=json_file,
        template_path=tpl_file,
        output_paths=[out_file1, out_file2],
    )

    assert "<!DOCTYPE html>" in res
    assert "Mezcal Ojo de Tigre" in res
    assert out_file1.exists()
    assert out_file2.exists()
    assert out_file1.read_text(encoding="utf-8") == res


def test_generar_dashboard_errores_archivos_inexistentes(tmp_path: Path):
    """Valida que generar_dashboard lance FileNotFoundError ante rutas inválidas."""
    with pytest.raises(FileNotFoundError):
        generar_dashboard(data_json_path=tmp_path / "no_existe.json")

    valid_json = tmp_path / "datos.json"
    valid_json.write_text("[]", encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        generar_dashboard(data_json_path=valid_json, template_path=tmp_path / "no_existe_template.html")


def test_actualizar_todo_pipeline_completo(tmp_path: Path):
    """Valida el pipeline completo del consolidador con datasets sintéticos (H24 / H25)."""
    # Crear dos archivos CSV fuente simulando tiendas distintas
    df_alianza = crear_df_base(
        [
            {
                "tienda": "Bodegas Alianza",
                "producto": "Tequila Dobel Diamante 750 ml",
                "categoria": "Tequila",
                "subcategoria": "Añejo Cristalino",
                "clase": "Añejo Cristalino",
                "ml": 750,
                "precio_regular": 800.0,
                "precio_promo": 650.0,
            },
            {
                "tienda": "Bodegas Alianza",
                "producto": "Licor de Whisky Jack Daniel's Honey 700 ml",
                "categoria": "Licor de Whisky",
                "subcategoria": "Honey Liqueur",
                "clase": "Licor",
                "ml": 700,
                "precio_regular": 550.0,
                "precio_promo": 450.0,
            },
            # Outlier ultra-lujo
            {
                "tienda": "Bodegas Alianza",
                "producto": "Whisky Royal Salute 51 Años 700 ml",
                "categoria": "Whisky",
                "subcategoria": "Blended Scotch",
                "clase": "Ultra Lujo",
                "ml": 700,
                "precio_regular": 690000.0,
                "precio_promo": 690000.0,
            },
            # Artículo a descartar por volumen menor a 650 ml
            {
                "tienda": "Bodegas Alianza",
                "producto": "Tequila Minis 50 ml",
                "ml": 50,
            },
        ]
    )
    df_walmart = crear_df_base(
        [
            {
                "tienda": "Walmart",
                "producto": "Tequila Dobel Diamante 750 ml",
                "categoria": "Tequila",
                "subcategoria": "Añejo Cristalino",
                "clase": "Añejo Cristalino",
                "ml": 750,
                "precio_regular": 820.0,
                "precio_promo": 620.0,
            }
        ]
    )

    path_alianza = tmp_path / "scraped_alianza.csv"
    path_walmart = tmp_path / "scraped_walmart.csv"
    df_alianza.to_csv(path_alianza, index=False)
    df_walmart.to_csv(path_walmart, index=False)

    records = actualizar_todo(
        archivos_fuente=[str(path_alianza), str(path_walmart)],
        carpeta_salida=str(tmp_path),
    )

    # Validar que los 3 artefactos fueron generados
    assert (tmp_path / "catalogo_completo_consolidado.csv").exists()
    assert (tmp_path / "ranking_completo_general.csv").exists()
    assert (tmp_path / "dashboard_data.json").exists()

    # Validar exclusión del outlier en dashboard_data.json y en ranking
    assert len(records) > 0
    productos_en_dashboard = [r["producto"] for r in records]
    assert "Whisky Royal Salute 51 Años 700 ml" not in productos_en_dashboard

    # Validar que Dobel Diamante tiene cálculo cross-tienda enriquecido
    dobel_rec = next(r for r in records if "Dobel Diamante" in r["producto"] and r["tienda"] == "Bodegas Alianza")
    assert dobel_rec["es_comparable_cross_tienda"] is True
    assert dobel_rec["num_tiendas_cross"] == 2
    assert dobel_rec["tienda_mas_barata"] == "Walmart"
    assert dobel_rec["precio_minimo_cross"] == 620.0
    assert len(dobel_rec["ofertas_cross_tienda"]) == 1


def test_actualizar_todo_sin_archivos_fuente(tmp_path: Path):
    """Valida el manejo defensivo cuando no existen archivos fuente para consolidar."""
    res = actualizar_todo(
        archivos_fuente=[str(tmp_path / "inexistente.csv")],
        carpeta_salida=str(tmp_path),
    )
    assert res == []


def test_fase2_botones_orden_template():
    """Valida que la plantilla HTML contenga los atributos data-orden y la función de estado (Fase 2)."""
    tpl_path = Path("src/templates/dashboard_template.html")
    assert tpl_path.exists()
    contenido = tpl_path.read_text(encoding="utf-8")

    # Botones con atributos data-orden
    assert 'data-orden="precio_por_litro"' in contenido
    assert 'data-orden="precio_promo"' in contenido

    # Encabezados de tabla con atributos data-orden-header
    assert 'data-orden-header="precio_promo"' in contenido
    assert 'data-orden-header="precio_por_litro"' in contenido

    # Función y clases de sincronización de estado de orden
    assert "function actualizarEstadoOrden()" in contenido
    assert "CLASE_ORDEN_ACTIVO" in contenido
    assert "CLASE_ORDEN_INACTIVO" in contenido
    assert "orden-flecha" in contenido


def test_fase3_sin_redundancias_template():
    """Valida la eliminación de redundancias de categoría y enlaces duplicados (Fase 3 - Opción A)."""
    tpl_path = Path("src/templates/dashboard_template.html")
    assert tpl_path.exists()
    contenido = tpl_path.read_text(encoding="utf-8")

    # Helper para quitar prefijo de categoría y lista de prefijos
    assert "const PREFIJOS_CATEGORIA =" in contenido
    assert "function nombreSinCategoria(item)" in contenido

    # Nombre visible usa el helper
    assert "${nombreSinCategoria(item)}" in contenido

    # Columna acción solo contiene el botón + Carrito (sin el enlace ↗ duplicado)
    assert '<button onclick="agregarDesdeTabla(${originalIndex})"' in contenido
    # No debe haber enlace duplicado de acción dentro de la celda de acción
    assert 'title="Abrir ${item.producto} en ${item.tienda}"' not in contenido


def test_toggle_solo_mejor_precio_template():
    """Valida la presencia del toggle de solo mejor precio y su lógica de deduplicación."""
    tpl_path = Path("src/templates/dashboard_template.html")
    assert tpl_path.exists()
    contenido = tpl_path.read_text(encoding="utf-8")

    # Toggle en el encabezado de catálogo
    assert 'id="filtro-mejor-precio"' in contenido
    assert "⭐ Solo mejor precio" in contenido

    # Activo por defecto
    assert '<input type="checkbox" id="filtro-mejor-precio" onchange="aplicarFiltros()" checked' in contenido

    # Lógica de deduplicación y filtrado por es_precio_mas_bajo en aplicarFiltros
    assert 'if (tienda === "Todas" && soloMejor)' in contenido
    assert "if (!item.es_precio_mas_bajo) return false;" in contenido
    assert "clavesVistas.has(k)" in contenido
