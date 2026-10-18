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


def test_generar_dashboard_sin_duplicado_local():
    """Valida que LOCAL_HTML_PATH esté eliminado y solo se genere index.html (H39)."""
    import src.generar_dashboard_v4 as mod_dash

    assert not hasattr(mod_dash, "LOCAL_HTML_PATH")
    assert mod_dash.INDEX_HTML_PATH.name == "index.html"


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


def test_cascada_categoria_tipo_template():
    """Valida que el selector de tipo de bebida inicie desactivado y dependa de la categoría seleccionada."""
    tpl_path = Path("src/templates/dashboard_template.html")
    assert tpl_path.exists()
    contenido = tpl_path.read_text(encoding="utf-8")

    # Selector de tipo de bebida inicia desactivado con placeholder explicativo
    assert 'id="filtro-categoria" onchange="aplicarFiltros()" disabled' in contenido
    assert 'id="label-filtro-categoria"' in contenido
    assert "🔒 Selecciona primero una categoría..." in contenido

    # Lógica de activación reactiva en actualizarSubtiposCatalogo
    assert 'if (macro === "Todas") {' in contenido
    assert "selectSub.disabled = true;" in contenido
    assert "selectSub.disabled = false;" in contenido
    assert 'selectSub.classList.add("opacity-60", "bg-[#EFE8DC]/50", "cursor-not-allowed");' in contenido
    assert 'selectSub.classList.add("cursor-pointer", "bg-white");' in contenido

    # Lógica de desactivación defensiva en versus libre
    assert "🔓 Comparativa libre (sin filtro de tipo)" in contenido


def test_h32_umbrales_centralizados():
    """Valida la centralización de techos de ultra-lujo y límites de presupuesto (H32)."""
    from src.clasificacion import LIMITES_PRESUPUESTO_DASHBOARD, TECHOS_LITRO_OUTLIERS

    categorias_esperadas = {"Tequila", "Mezcal", "Whisky", "Licor de Whisky", "Vino"}
    assert set(TECHOS_LITRO_OUTLIERS.keys()) == categorias_esperadas
    assert set(LIMITES_PRESUPUESTO_DASHBOARD.keys()) == categorias_esperadas

    # Validar que todos los valores sean numéricos positivos
    for cat, techo in TECHOS_LITRO_OUTLIERS.items():
        assert techo > 0, f"Techo inválido para {cat}"

    for cat, lim in LIMITES_PRESUPUESTO_DASHBOARD.items():
        assert "max_precio_promo" in lim or "max_precio_por_litro" in lim, f"Faltan límites para {cat}"


def test_h37_exclusion_explicita_outliers_dashboard(tmp_path: Path):
    """Valida que el dashboard excluya explícitamente outliers de lujo aunque cumplan el tope de precio (H37)."""
    # 3 botellas base a $200 (mediana ppl = $266.67) y una a $1,500 (entra en tope de Tequila <= $1,950, pero ppl=$2000 > 4x mediana)
    df_lujo_sub_tope = crear_df_base(
        [
            {
                "tienda": "Bodegas Alianza",
                "producto": "Tequila Dobel Diamante Añejo Cristalino 750 ml",
                "categoria": "Tequila",
                "subcategoria": "Añejo Cristalino",
                "clase": "Añejo Cristalino",
                "ml": 750,
                "precio_regular": 250.0,
                "precio_promo": 200.0,
            },
            {
                "tienda": "Bodegas Alianza",
                "producto": "Tequila 1800 Cristalino Añejo 750 ml",
                "categoria": "Tequila",
                "subcategoria": "Añejo Cristalino",
                "clase": "Añejo Cristalino",
                "ml": 750,
                "precio_regular": 250.0,
                "precio_promo": 200.0,
            },
            {
                "tienda": "Bodegas Alianza",
                "producto": "Tequila Herradura Añejo Cristalino 750 ml",
                "categoria": "Tequila",
                "subcategoria": "Añejo Cristalino",
                "clase": "Añejo Cristalino",
                "ml": 750,
                "precio_regular": 250.0,
                "precio_promo": 200.0,
            },
            {
                "tienda": "Bodegas Alianza",
                "producto": "Tequila Don Julio 70 Añejo Cristalino 750 ml",
                "categoria": "Tequila",
                "subcategoria": "Añejo Cristalino",
                "clase": "Añejo Cristalino",
                "ml": 750,
                "precio_regular": 1600.0,
                "precio_promo": 1500.0,
            },
        ]
    )

    csv_in = tmp_path / "fuente.csv"
    df_lujo_sub_tope.to_csv(csv_in, index=False)

    records = actualizar_todo(archivos_fuente=[str(csv_in)], carpeta_salida=str(tmp_path))
    prods_en_dashboard = [r["producto"] for r in records]

    # Don Julio 70 cuesta $1,500 (cumple tope Tequila <= $1,950), pero al ser outlier es excluido explícitamente (H37)
    assert not any("Don Julio 70" in p for p in prods_en_dashboard)
    assert any("Dobel Diamante" in p for p in prods_en_dashboard)


def test_filtro_paquete_en_dashboard(tmp_path: Path):
    """Valida que los registros conserven es_paquete y que la plantilla contenga el filtro interactivo."""
    # 1. Verificar presencia de controles en la plantilla HTML
    tpl_path = Path("src/templates/dashboard_template.html")
    assert tpl_path.exists()
    tpl_content = tpl_path.read_text(encoding="utf-8")
    assert 'id="filtro-paquete"' in tpl_content
    assert 'id="filtro-paquete-pill"' in tpl_content
    assert "sincronizarFiltroPaquete" in tpl_content
    assert "esProductoPaquete" in tpl_content

    # 2. Verificar que actualizar_todo exporte es_paquete como booleano
    df_prueba = crear_df_base(
        [
            {
                "tienda": "Bodegas Alianza",
                "producto": "Mezcal 400 Conejos Joven 100% Cosecha Salvaje 700 ml + 2 Vasos + Sal",
                "categoria": "Mezcal",
                "subcategoria": "Silvestre",
                "clase": "Joven Silvestre",
                "ml": 700,
                "precio_regular": 849.0,
                "precio_promo": 849.0,
                "condiciones": "🎁 Edición con obsequio (2 Vasos + Sal)",
            },
            {
                "tienda": "Bodegas Alianza",
                "producto": "Mezcal 400 Conejos Joven 100% Cosecha Salvaje 700 ml",
                "categoria": "Mezcal",
                "subcategoria": "Silvestre",
                "clase": "Joven Silvestre",
                "ml": 700,
                "precio_regular": 849.0,
                "precio_promo": 849.0,
                "condiciones": "Precio regular catálogo",
            },
        ]
    )
    csv_in = tmp_path / "fuente_paquetes.csv"
    df_prueba.to_csv(csv_in, index=False)
    records = actualizar_todo(archivos_fuente=[str(csv_in)], carpeta_salida=str(tmp_path))

    combo_rec = next(r for r in records if "Vasos" in r["producto"])
    single_rec = next(r for r in records if "Vasos" not in r["producto"])
    assert combo_rec["es_paquete"] is True
    assert single_rec["es_paquete"] is False


def test_h35_dashboard_cross_tienda_700_vs_750ml(tmp_path: Path):
    """Valida la unificación de 700 vs 750 ml y cálculo de arbitraje en el pipeline del dashboard (H35)."""
    # 1. Verificar plantilla HTML para modal y versus ordenados por $/L
    tpl_path = Path("src/templates/dashboard_template.html")
    assert tpl_path.exists()
    tpl_content = tpl_path.read_text(encoding="utf-8")
    assert "sort((a, b) => a.p.precio_por_litro - b.p.precio_por_litro)" in tpl_content
    assert "sort((a, b) => a.item.precio_por_litro - b.item.precio_por_litro)" in tpl_content

    # 2. Pipeline con botellas 700 ml vs 750 ml
    df_prueba = crear_df_base(
        [
            {
                "tienda": "Sam's Club",
                "producto": "Tequila Herradura Ultra Añejo 700 ml",
                "categoria": "Tequila",
                "subcategoria": "Añejo Cristalino",
                "clase": "Añejo Cristalino",
                "categoria_comparable": "Tequila - Añejo Cristalino",
                "ml": 700,
                "precio_regular": 750.0,
                "precio_promo": 647.56,
            },
            {
                "tienda": "Walmart",
                "producto": "Tequila Herradura Ultra Añejo 750 ml",
                "categoria": "Tequila",
                "subcategoria": "Añejo Cristalino",
                "clase": "Añejo Cristalino",
                "categoria_comparable": "Tequila - Añejo Cristaljo" if False else "Tequila - Añejo Cristalino",
                "ml": 750,
                "precio_regular": 958.0,
                "precio_promo": 958.0,
            },
        ]
    )
    csv_in = tmp_path / "fuente_h35.csv"
    df_prueba.to_csv(csv_in, index=False)
    records = actualizar_todo(archivos_fuente=[str(csv_in)], carpeta_salida=str(tmp_path))

    assert len(records) == 2
    rec_sams = next(r for r in records if r["tienda"] == "Sam's Club")
    rec_walmart = next(r for r in records if r["tienda"] == "Walmart")

    assert rec_sams["es_comparable_cross_tienda"] is True
    assert rec_walmart["es_comparable_cross_tienda"] is True
    assert rec_sams["num_tiendas_cross"] == 2
    assert rec_walmart["num_tiendas_cross"] == 2

    # Sam's Club tiene menor precio por litro ($925.09 vs $1277.33 / L)
    assert rec_sams["es_precio_mas_bajo"] is True
    assert rec_walmart["es_precio_mas_bajo"] is False
    assert rec_walmart["tienda_mas_barata"] == "Sam's Club"
    assert rec_walmart["diferencia_vs_minimo"] > 240.0


def test_h33_sin_except_exception_genericos():
    """Valida mediante análisis sintáctico (AST) que ningún módulo en src/ use 'except Exception' ni 'except:' genérico (H33)."""
    import ast
    import glob

    violaciones = []
    archivos = sorted(glob.glob("src/**/*.py", recursive=True))
    assert len(archivos) > 0, "No se encontraron archivos en src/"

    for py_file in archivos:
        with open(py_file, "r", encoding="utf-8") as f:
            arbol = ast.parse(f.read(), filename=py_file)
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.ExceptHandler):
                if nodo.type is None:
                    violaciones.append(f"{py_file}:{nodo.lineno} (bare except:)")
                elif isinstance(nodo.type, ast.Name) and nodo.type.id == "Exception":
                    violaciones.append(f"{py_file}:{nodo.lineno} (except Exception:)")

    assert len(violaciones) == 0, f"Se detectaron manejadores genéricos prohibidos (H33): {violaciones}"
