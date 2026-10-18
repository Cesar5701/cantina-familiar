    // 1. CARGA DE DATOS AUDITADOS (653 PRODUCTOS MULTITIENDA)
    const DATOS_COMPLETOS = __DATA_JSON__;

    // PARÁMETROS GLOBALES REACTIVOS (INICIAN EN 0 / EN BLANCO)
    let PRESUPUESTO_OBJETIVO = 0;
    let COOPERADORES_TOTAL = 0;

    // ESTADO DEL CARRITO DE COMPRAS (INICIA VACÍO)
    let canastaPersonalizada = {};

    // DEFINICIÓN JERÁRQUICA DE CATEGORÍA -> SUBTIPOS
    const SUBTIPOS_POR_MACRO = {
      "Tequila": [
        { value: "Todos_Macro", label: "🥃 Todos los Tipos de Tequila (210)" },
        { value: "Tequila - Añejo Cristalino", label: "✨ Añejo Cristalino (88)" },
        { value: "Tequila - Reposado Cristalino", label: "💎 Reposado Cristalino (68)" },
        { value: "Tequila - Añejo Tradicional", label: "🪵 Añejo Tradicional (54)" }
      ],
      "Mezcal": [
        { value: "Todos_Macro", label: "🌵 Todos los Tipos de Mezcal (226)" },
        { value: "Mezcal - Espadín Joven", label: "🔥 Espadín Joven (124)" },
        { value: "Mezcal - Silvestre", label: "🌿 Silvestre: Tobalá / Cupreata / Cuishe (46)" },
        { value: "Mezcal - Reposado", label: "🪵 Reposado en Madera (34)" },
        { value: "Mezcal - Reposado Cristalino", label: "💎 Reposado Cristalino (13)" },
        { value: "Mezcal - Añejo", label: "🥃 Añejo de Barrica (9)" }
      ],
      "Whisky": [
        { value: "Whisky - Blended Scotch", label: "🥃 Blended Scotch (175)" }
      ],
      "Licor de Whisky": [
        { value: "Licor de Whisky - Honey", label: "🍯 Licor de Whisky con Miel / Honey (9)" }
      ],
      "Vino": [
        { value: "Vino - Tinto Clericot", label: "🍷 Vino Tinto para Clericot y Mesa (155)" }
      ]
    };

    // HELPER PARA BADGE DE TIENDA TONAL MD3 (BAJA SATURACIÓN, ALTA LEGIBILIDAD EN FONDO CLARO)
    function getBadgeTienda(tienda, corto = false) {
      if (tienda === "Sam's Club") {
        return `<span class="badge bg-[#DBEAFE] text-[#1E3A8A] border border-[#BFDBFE]">${corto ? "Sam's" : "Sam's Club"}</span>`;
      }
      if (tienda === "Walmart") {
        return `<span class="badge bg-[#E0F2FE] text-[#0C4A6E] border border-[#BAE6FD]">Walmart</span>`;
      }
      if (tienda === "Chedraui") {
        return `<span class="badge bg-[#FFEDD5] text-[#7C2D12] border border-[#FED7AA]">Chedraui</span>`;
      }
      if (tienda === "Soriana") {
        return `<span class="badge bg-[#FFE4E6] text-[#881337] border border-[#FECDD3]">Soriana</span>`;
      }
      return `<span class="badge bg-[#F8E2C8] text-[#784516] border border-[#E5C8A3]">${corto ? "Alianza" : "Bodegas Alianza"}</span>`;
    }

    // DICCIONARIO DE SUGERENCIAS DE DUELOS POR CATEGORÍA (INCLUYE DUELOS MULTITIENDA)
    const SUGERENCIAS_POR_CATEGORIA = {
      "Tequila - Añejo Cristalino": [
        { a: "Maestro Dobel  Diamante Cristalino 700", storeA: "Sam's Club", b: "Maestro Dobel Diamante 700", storeB: "Bodegas Alianza", label: "🏪 Dobel Diamante Sam's ($574.93) vs Alianza ($655)" },
        { a: "Don Julio 70 Cristalino 700", storeA: "Walmart", b: "Don Julio 70 700", storeB: "Bodegas Alianza", label: "🏪 Don Julio 70 Walmart ($699) vs Alianza ($778)" },
        { a: "Tequila 1800 Añejo Cristalino 100% 700", storeA: "Bodegas Alianza", b: "Don Julio 70 Cristalino 700", storeB: "Walmart", label: "1800 Cristalino Alianza ($600) vs Don Julio 70 Walmart ($699)" },
        { a: "Member's Mark  Añejo Cristalino 1.75", storeA: "Sam's Club", b: "Tequila 1800 Añejo Cristalino 100% 700", storeB: "Bodegas Alianza", label: "Member's Mark 1.75L Sam's ($844.70 | $482/L) vs 1800 Crist ($600)" },
        { a: "Tequila 1800 Añejo Cristalino 100% 700", storeA: "Bodegas Alianza", b: "1800 Cristalino Añejo 700", storeB: "Chedraui", label: "🏪 1800 Cristalino Alianza ($600) vs Chedraui ($705)" }
      ],
      "Tequila - Añejo Tradicional": [
        { a: "Tequila 1800 Añejo 700ml", storeA: "Chedraui", b: "Tequila 1800 Añejo 700 ml", storeB: "Bodegas Alianza", label: "🏪 1800 Añejo Chedraui ($585) vs Alianza ($599.25)" },
        { a: "Tres Generaciones Añejo 750", storeA: "Bodegas Alianza", b: "Tequila 1800 Añejo 700ml", storeB: "Chedraui", label: "Tres Generaciones Añejo ($567) vs 1800 Añejo Chedraui ($585)" },
        { a: "Hornitos Black Barrel", storeA: "Bodegas Alianza", b: "Tequila 1800 Añejo 700ml", storeB: "Chedraui", label: "Hornitos Black Barrel ($451.50) vs 1800 Añejo ($585)" },
        { a: "Gran Centenario Añejo 695", storeA: "Bodegas Alianza", b: "Gran Centenario Añejo 695", storeB: "Chedraui", label: "🏪 Gran Centenario Añejo Alianza ($685) vs Chedraui ($699)" }
      ],
      "Tequila - Reposado Cristalino": [
        { a: "Member's Mark  Reposado Cristalino 1.75", storeA: "Sam's Club", b: "Cuervo Tradicional Reposado Cristalino 750", storeB: "Bodegas Alianza", label: "Member's Mark Rep Crist 1.75L ($665 | $380/L) vs Cuervo ($390)" },
        { a: "Gran Centenario Ultra Reposado", storeA: "Bodegas Alianza", b: "Cuervo Tradicional Reposado Cristalino 750", storeB: "Bodegas Alianza", label: "Centenario Ultra ($440) vs Cuervo Tradicional Crist ($390)" },
        { a: "Cuervo Tradicional Reposado Cristalino 750", storeA: "Bodegas Alianza", b: "José Cuervo Tradicional Reposado Cristalino", storeB: "Sam's Club", label: "🏪 Cuervo Cristalino Alianza ($390) vs Sam's Club ($473.65)" },
        { a: "Gran Centenario Ultra Reposado", storeA: "Bodegas Alianza", b: "Herradura Reposado Cristalino", storeB: "Bodegas Alianza", label: "Centenario Ultra ($440) vs Herradura Rep Crist ($521.50)" }
      ],
      "Mezcal - Reposado": [
        { a: "Amarás Rep Espadín", storeA: "Bodegas Alianza", b: "400 Conejos Reposado 700ml", storeB: "Chedraui", label: "🏪 Amarás Rep Alianza ($503) vs 400 Conejos Rep Chedraui ($520)" },
        { a: "400 Conejos Reposado 700ml", storeA: "Chedraui", b: "Mezcal 400 Conejos Reposado 700 ml", storeB: "Bodegas Alianza", label: "🏪 400 Conejos Reposado Chedraui ($520) vs Alianza ($650)" },
        { a: "Amarás Rep Espadín", storeA: "Bodegas Alianza", b: "Artesanal Ojo De Tigre Reposado", storeB: "Bodegas Alianza", label: "Amarás Reposado ($503) vs Ojo de Tigre Reposado ($616)" }
      ],
      "Mezcal - Silvestre": [
        { a: "400 Conejos Tobalá 700ml", storeA: "Chedraui", b: "400 Conejos Joven Espadín Tobala", storeB: "Bodegas Alianza", label: "🏪 400 Conejos Tobalá Chedraui ($520) vs Alianza ($650)" },
        { a: "Amarás Joven Cupreata", storeA: "Bodegas Alianza", b: "400 Conejos Tobalá 700ml", storeB: "Chedraui", label: "Amarás Cupreata Alianza ($719) vs 400 Conejos Tobalá Chedraui ($520)" },
        { a: "400 Conejos Cuishe 700ml", storeA: "Chedraui", b: "Mezcal 400 Conejos Joven Cuishe", storeB: "Bodegas Alianza", label: "🏪 400 Conejos Cuishe Chedraui ($520) vs Alianza ($650)" }
      ],
      "Mezcal - Añejo": [
        { a: "Mezcal 400 Conejos Añejo 700", storeA: "Bodegas Alianza", b: "400 Conejos Espadín Añejo 750ml", storeB: "Chedraui", label: "🏪 400 Conejos Añejo 700ml Alianza ($667.50) vs 750ml Chedraui ($699)" },
        { a: "Mezcal 400 Conejos Añejo 700", storeA: "Bodegas Alianza", b: "Mezcal 400 Conejos Añejo 700", storeB: "Walmart", label: "🏪 400 Conejos Añejo Alianza ($667.50) vs Walmart ($869)" }
      ],
      "Mezcal - Reposado Cristalino": [
        { a: "400 Conejos  Espadín Cristalino 700", storeA: "Sam's Club", b: "400 Conejos Cristalino 100% 700", storeB: "Bodegas Alianza", label: "🏪 400 Conejos Cristalino Sam's ($599.46) vs Alianza ($600)" },
        { a: "400 Conejos Cristalino 100% 700", storeA: "Bodegas Alianza", b: "400 Conejos Cristalino 700", storeB: "Soriana", label: "🏪 400 Conejos Cristalino Alianza ($600) vs Soriana ($685)" }
      ],
      "Mezcal - Espadín Joven": [
        { a: "400 Conejos Joven 700ml", storeA: "Chedraui", b: "Verde Amarás  Espadín 700", storeB: "Sam's Club", label: "🏪 400 Conejos Joven Chedraui ($430) vs Verde Amarás Sam's ($460)" },
        { a: "Joven 400 Conejos  1.75", storeA: "Sam's Club", b: "Amarás  Espadín Joven  1.75", storeB: "Sam's Club", label: "400 Conejos 1.75L Sam's ($1,006) vs Amarás 1.75L Sam's ($1,052)" }
      ],
      "Whisky - Blended Scotch": [
        { a: "Black & White  1l", storeA: "Sam's Club", b: "Black & White Blended Scotch 1 L", storeB: "Bodegas Alianza", label: "🏪 Black & White 1L Sam's ($261.89) vs Alianza ($270)" },
        { a: "Johnnie Walker Red Label 1.75", storeA: "Sam's Club", b: "Red Label Blended Scotch 700", storeB: "Bodegas Alianza", label: "🏪 JW Red Label 1.75L Sam's ($627.10) vs 700ml Alianza ($275)" },
        { a: "Johnnie Walker Red Label 1.75", storeA: "Sam's Club", b: "Johnnie Walker Red Label 1.75", storeB: "Bodegas Alianza", label: "🏪 JW Red Label 1.75L Sam's ($627.10) vs 1.75L Alianza ($825)" },
        { a: "William Lawson's", storeA: "Bodegas Alianza", b: "Black & White  1.75", storeB: "Sam's Club", label: "William Lawson's 1.75L Alianza ($470) vs Black & White 1.75L Sam's ($491)" }
      ],
      "Licor de Whisky - Honey": [
        { a: "Honey Tennessee 700", storeA: "Bodegas Alianza", b: "Tennessee Honey 700ml", storeB: "Chedraui", label: "🏪 Jack Daniel's Honey Alianza ($378) vs Chedraui ($395)" },
        { a: "Honey Tennessee 700", storeA: "Bodegas Alianza", b: "Tennessee Honey 1 L", storeB: "Sam's Club", label: "🏪 Jack Daniel's Honey 700ml Alianza ($378) vs 1.0L Sam's ($562.65)" },
        { a: "Passport Honey 700ml", storeA: "Chedraui", b: "Honey Tennessee 700", storeB: "Bodegas Alianza", label: "Passport Honey Chedraui ($185) vs Jack Daniel's Honey ($378)" }
      ],
      "Vino - Tinto Clericot": [
        { a: "Don Simon  5 L", storeA: "Sam's Club", b: "California Tetra Pak 946", storeB: "Bodegas Alianza", label: "🏪 Don Simón 5L Sam's ($335.52 | $67/L) vs California Tetra ($83 | $88/L)" },
        { a: "California Tetra Pak 946", storeA: "Bodegas Alianza", b: "Carlo Rossi  Blend 4 l", storeB: "Sam's Club", label: "🏪 California Tetra Alianza ($83) vs Carlo Rossi 4L Sam's ($437.83)" },
        { a: "California Cabernet Sauvignon 4 L", storeA: "Soriana", b: "Carlo Rossi  Blend 4 l", storeB: "Sam's Club", label: "🏪 California 4L Soriana ($425) vs Carlo Rossi 4L Sam's ($437.83)" }
      ],
      "Todas": [
        { a: "Maestro Dobel  Diamante Cristalino 700", storeA: "Sam's Club", b: "Maestro Dobel Diamante 700", storeB: "Bodegas Alianza", label: "🏪 Dobel Diamante Sam's ($575) vs Alianza ($655) [Tequila Crist]" },
        { a: "Don Julio 70 Cristalino 700", storeA: "Walmart", b: "Don Julio 70 700", storeB: "Bodegas Alianza", label: "🏪 Don Julio 70 Walmart ($699) vs Alianza ($778) [Tequila Crist]" },
        { a: "400 Conejos Tobalá 700ml", storeA: "Chedraui", b: "400 Conejos Joven Espadín Tobala", storeB: "Bodegas Alianza", label: "🏪 400 Conejos Tobalá Chedraui ($520) vs Alianza ($650) [Mezcal]" },
        { a: "Johnnie Walker Red Label 1.75", storeA: "Sam's Club", b: "Red Label Blended Scotch 700", storeB: "Bodegas Alianza", label: "🏪 Red Label 1.75L Sam's ($627) vs 700ml Alianza ($275) [Whisky]" },
        { a: "Don Simon  5 L", storeA: "Sam's Club", b: "California Tetra Pak 946", storeB: "Bodegas Alianza", label: "🏪 Don Simón 5L Sam's ($335) vs California Tetra ($83) [Vino]" }
      ]
    };

    // ESTADO DE FILTROS EN TABLA
    let datosFiltrados = [...DATOS_COMPLETOS];
    let columnaOrden = "precio_por_litro";
    let ordenAsc = true;
    let paginaActual = 1;
    const itemsPorPagina = 20;

    function getMacroCategoria(item) {
      const cat = item.categoria_comparable || '';
      if (cat.startsWith('Tequila')) return 'Tequila';
      if (cat.startsWith('Mezcal')) return 'Mezcal';
      if (cat.startsWith('Licor de Whisky') || cat.includes('Honey')) return 'Honey';
      if (cat.startsWith('Whisky')) return 'Whisky';
      if (cat.startsWith('Vino')) return 'Vino';
      return 'Otros';
    }

    function buscarIndice(prodKw, storeKw) {
      return DATOS_COMPLETOS.findIndex(p => {
        const matchProd = p.producto.toLowerCase().includes(prodKw.toLowerCase());
        const matchStore = !storeKw || p.tienda.toLowerCase().includes(storeKw.toLowerCase());
        return matchProd && matchStore;
      });
    }

    document.addEventListener("DOMContentLoaded", () => {
      // H51: al cargar, abrir de inmediato la pestaña indicada en la URL sin scroll animado
      const tabInicial = idTabDesdeHash();
      if (tabInicial) cambiarTab(tabInicial);
      const preloadStyle = document.getElementById("tab-preload-style");
      if (preloadStyle) preloadStyle.remove();

      actualizarSubtiposCatalogo();
      actualizarSubtiposVersus();
      inicializarSelectorCrossTiendaVersus();
      renderizarCanastasDinamicas();
      renderizarConstructorCanasta();
      actualizarEstadoOrden();
    });
