    // 1. CARGA DE DATOS AUDITADOS MULTITIENDA
    const DATOS_COMPLETOS = __DATA_JSON__;
    const CAMPANAS_ACTIVAS = __CAMPANAS_JSON__;

    // PARÁMETROS GLOBALES REACTIVOS (INICIAN EN 0 / EN BLANCO)
    let PRESUPUESTO_OBJETIVO = 0;
    let COOPERADORES_TOTAL = 0;

    // ESTADO DEL CARRITO DE COMPRAS (INICIA VACÍO)
    let canastaPersonalizada = {};
    const CLAVE_STORAGE_CANASTA = "cantina_familiar_estado_v1";

    // DEFINICIÓN JERÁRQUICA DE CATEGORÍA -> SUBTIPOS (CONTEOS SINCRONIZADOS DINÁMICAMENTE)
    const SUBTIPOS_POR_MACRO = {
      "Tequila": [
        { value: "Todos_Macro", baseLabel: "Todos los Tipos de Tequila", label: "Todos los Tipos de Tequila (259)" },
        { value: "Tequila - Añejo Cristalino", baseLabel: "Añejo Cristalino", label: "Añejo Cristalino (104)" },
        { value: "Tequila - Reposado Cristalino", baseLabel: "Reposado Cristalino", label: "Reposado Cristalino (79)" },
        { value: "Tequila - Añejo Tradicional", baseLabel: "Añejo Tradicional", label: "Añejo Tradicional (76)" }
      ],
      "Mezcal": [
        { value: "Todos_Macro", baseLabel: "Todos los Tipos de Mezcal", label: "Todos los Tipos de Mezcal (237)" },
        { value: "Mezcal - Espadín Joven", baseLabel: "Espadín Joven", label: "Espadín Joven (125)" },
        { value: "Mezcal - Silvestre", baseLabel: "Silvestre: Tobalá / Cupreata / Cuishe", label: "Silvestre: Tobalá / Cupreata / Cuishe (51)" },
        { value: "Mezcal - Reposado", baseLabel: "Reposado en Madera", label: "Reposado en Madera (34)" },
        { value: "Mezcal - Añejo", baseLabel: "Añejo de Barrica", label: "Añejo de Barrica (14)" },
        { value: "Mezcal - Reposado Cristalino", baseLabel: "Reposado Cristalino", label: "Reposado Cristalino (13)" }
      ],
      "Whisky": [
        { value: "Whisky - Blended Scotch", baseLabel: "Blended Scotch", label: "Blended Scotch (226)" }
      ],
      "Licor de Whisky": [
        { value: "Licor de Whisky - Honey", baseLabel: "Licor de Whisky: Honey & Apple", label: "Licor de Whisky: Honey & Apple (15)" }
      ],
      "Vino": [
        { value: "Vino - Tinto Clericot", baseLabel: "Vino Tinto para Clericot y Mesa", label: "Vino Tinto para Clericot y Mesa (194)" }
      ]
    };

    // HELPER PARA BADGE DE TIENDA EDITORIAL (INDICADOR CROMÁTICO + SUPERFICIE TONAL CÁLIDA)
    function getBadgeTienda(tienda, corto = false) {
      if (tienda === "Sam's Club") {
        return `<span class="badge bg-[#DBEAFE] text-[#1E3A8A] border border-[#BFDBFE]"><span class="store-dot bg-[#1E3A8A]"></span>${corto ? "Sam's" : "Sam's Club"}</span>`;
      }
      if (tienda === "Costco") {
        return `<span class="badge bg-[#FEE2E2] text-[#991B1B] border border-[#FECACA]"><span class="store-dot bg-[#991B1B]"></span>Costco</span>`;
      }
      if (tienda === "Walmart") {
        return `<span class="badge bg-[#E0F2FE] text-[#0C4A6E] border border-[#BAE6FD]"><span class="store-dot bg-[#0369A1]"></span>Walmart</span>`;
      }
      if (tienda === "Chedraui") {
        return `<span class="badge bg-[#FFEDD5] text-[#7C2D12] border border-[#FED7AA]"><span class="store-dot bg-[#C2410C]"></span>Chedraui</span>`;
      }
      if (tienda === "Soriana") {
        return `<span class="badge bg-[#FFE4E6] text-[#881337] border border-[#FECDD3]"><span class="store-dot bg-[#881337]"></span>Soriana</span>`;
      }
      return `<span class="badge bg-[#F8E2C8] text-[#784516] border border-[#E5C8A3]"><span class="store-dot bg-[#784516]"></span>${corto ? "Alianza" : "Bodegas Alianza"}</span>`;
    }

    // DICCIONARIO DE SUGERENCIAS DE DUELOS POR CATEGORÍA (PRECIOS SINCRONIZADOS DINÁMICAMENTE EN RENDER)
    const SUGERENCIAS_POR_CATEGORIA = {
      "Tequila - Añejo Cristalino": [
        { a: "Maestro Dobel Diamante Cristalino 700", storeA: "Sam's Club", b: "Maestro Dobel Diamante 700", storeB: "Bodegas Alianza", label: "Dobel Diamante Sam's ($509) vs Alianza ($573.75)" },
        { a: "Don Julio 70 700", storeA: "Bodegas Alianza", b: "Don Julio 70 Cristalino 700", storeB: "Walmart", label: "Don Julio 70 Alianza ($655) vs Walmart ($699)" },
        { a: "Tequila 1800 Añejo Cristalino 700", storeA: "Sam's Club", b: "Tequila 1800 Añejo Cristalino 100% 700", storeB: "Bodegas Alianza", label: "1800 Cristalino Sam's ($584) vs Alianza ($663.75)" },
        { a: "Member's Mark Añejo Cristalino 1.75", storeA: "Sam's Club", b: "Tequila 1800 Añejo Cristalino 100% 700", storeB: "Bodegas Alianza", label: "Member's Mark 1.75L Sam's ($844.70) vs 1800 Crist Alianza ($663.75)" },
        { a: "Tequila 1800 Añejo Cristalino 100% 700", storeA: "Bodegas Alianza", b: "1800 Cristalino Añejo 700", storeB: "Chedraui", label: "1800 Cristalino Alianza ($663.75) vs Chedraui ($940)" }
      ],
      "Tequila - Añejo Tradicional": [
        { a: "1800 Añejo Tequila 700", storeA: "Costco", b: "Tequila 1800 Añejo 700", storeB: "Bodegas Alianza", label: "1800 Añejo Costco ($629.29) vs Alianza ($799)" },
        { a: "Tres Generaciones Añejo 750", storeA: "Bodegas Alianza", b: "Tequila 1800 Añejo 700", storeB: "Chedraui", label: "Tres Generaciones Añejo ($526.50) vs 1800 Añejo Chedraui ($823)" },
        { a: "Hornitos Black Barrel", storeA: "Bodegas Alianza", b: "Tequila 1800 Añejo 700", storeB: "Bodegas Alianza", label: "Hornitos Black Barrel ($419.25) vs 1800 Añejo ($799)" },
        { a: "Gran Centenario Añejo 695", storeA: "Bodegas Alianza", b: "Gran Centenario Añejo 695", storeB: "Chedraui", label: "Gran Centenario Añejo Alianza ($685) vs Chedraui ($711)" }
      ],
      "Tequila - Reposado Cristalino": [
        { a: "Member's Mark Reposado Cristalino 1.75", storeA: "Sam's Club", b: "Cuervo Tradicional Reposado Cristalino 750", storeB: "Bodegas Alianza", label: "Member's Mark Rep Crist 1.75L ($664.93) vs Cuervo ($442.50)" },
        { a: "Gran Centenario Ultra Reposado", storeA: "Bodegas Alianza", b: "Cuervo Tradicional Reposado Cristalino 750", storeB: "Bodegas Alianza", label: "Centenario Ultra ($440) vs Cuervo Tradicional Crist ($442.50)" },
        { a: "Cuervo Tradicional Reposado Cristalino 750", storeA: "Bodegas Alianza", b: "José Cuervo Tradicional Reposado Cristalino", storeB: "Sam's Club", label: "Cuervo Cristalino Alianza ($442.50) vs Sam's Club ($566.71)" },
        { a: "Gran Centenario Ultra Reposado", storeA: "Bodegas Alianza", b: "Herradura Reposado Cristalino", storeB: "Bodegas Alianza", label: "Centenario Ultra ($440) vs Herradura Rep Crist ($521.50)" }
      ],
      "Mezcal - Reposado": [
        { a: "Amarás Rep Espadín", storeA: "Bodegas Alianza", b: "400 Conejos Reposado 700", storeB: "Costco", label: "Amarás Rep Alianza ($467.35) vs 400 Conejos Rep Costco ($559.30)" },
        { a: "400 Conejos Reposado 700", storeA: "Costco", b: "Mezcal 400 Conejos Reposado 700", storeB: "Bodegas Alianza", label: "400 Conejos Reposado Costco ($559.30) vs Alianza ($650)" },
        { a: "Amarás Rep Espadín", storeA: "Bodegas Alianza", b: "Artesanal Ojo De Tigre Reposado", storeB: "Bodegas Alianza", label: "Amarás Reposado ($467.35) vs Ojo de Tigre Reposado ($471.25)" }
      ],
      "Mezcal - Silvestre": [
        { a: "400 Conejos Joven Espadín Tobala", storeA: "Bodegas Alianza", b: "400 Conejos Tobalá 700", storeB: "Chedraui", label: "400 Conejos Tobalá Alianza ($650) vs Chedraui ($699)" },
        { a: "Amarás Joven Cupreata", storeA: "Bodegas Alianza", b: "400 Conejos Tobalá 700", storeB: "Chedraui", label: "Amarás Cupreata Alianza ($584.35) vs 400 Conejos Tobalá Chedraui ($699)" },
        { a: "Mezcal 400 Conejos Joven Cuishe", storeA: "Bodegas Alianza", b: "400 Conejos Cuishe 700", storeB: "Chedraui", label: "400 Conejos Cuishe Alianza ($650) vs Chedraui ($699)" }
      ],
      "Mezcal - Añejo": [
        { a: "400 Conejos Espadín Añejo 750", storeA: "Chedraui", b: "Mezcal 400 Conejos Añejo 700", storeB: "Bodegas Alianza", label: "400 Conejos Añejo 750ml Chedraui ($739) vs 700ml Alianza ($890)" },
        { a: "Mezcal 400 Conejos Añejo 700", storeA: "Walmart", b: "Mezcal 400 Conejos Añejo 700", storeB: "Bodegas Alianza", label: "400 Conejos Añejo Walmart ($869) vs Alianza ($890)" }
      ],
      "Mezcal - Reposado Cristalino": [
        { a: "400 Conejos Cristalino 700", storeA: "Costco", b: "400 Conejos Cristalino 100% 700", storeB: "Bodegas Alianza", label: "400 Conejos Cristalino Costco ($524.30) vs Alianza ($600)" },
        { a: "400 Conejos Cristalino 100% 700", storeA: "Bodegas Alianza", b: "400 Conejos Cristalino 700", storeB: "Soriana", label: "400 Conejos Cristalino Alianza ($600) vs Soriana ($685)" }
      ],
      "Mezcal - Espadín Joven": [
        { a: "400 Conejos Joven 700", storeA: "Bodegas Alianza", b: "Verde Amarás Espadín 700", storeB: "Sam's Club", label: "400 Conejos Joven Alianza ($408.75) vs Verde Amarás Sam's ($460.10)" },
        { a: "Amarás Espadín Joven 1.75", storeA: "Sam's Club", b: "Joven 400 Conejos 1.75", storeB: "Sam's Club", label: "Amarás 1.75L Sam's ($1,052.63) vs 400 Conejos 1.75L Sam's ($1,221.45)" }
      ],
      "Whisky - Blended Scotch": [
        { a: "Black & White 1 L", storeA: "Sam's Club", b: "Black & White Blended Scotch 1 L", storeB: "Bodegas Alianza", label: "Black & White 1L Sam's ($226.08) vs Alianza ($245)" },
        { a: "Johnnie Walker Red Label 1.75", storeA: "Sam's Club", b: "Red Label Blended Scotch 700", storeB: "Bodegas Alianza", label: "JW Red Label 1.75L Sam's ($506.39) vs 700ml Alianza ($264)" },
        { a: "Johnnie Walker Red Label 1.75", storeA: "Sam's Club", b: "Johnnie Walker Red Label 1.75", storeB: "Bodegas Alianza", label: "JW Red Label 1.75L Sam's ($506.39) vs 1.75L Alianza ($825)" },
        { a: "Black & White 1.75", storeA: "Sam's Club", b: "William Lawson's 2 L", storeB: "Bodegas Alianza", label: "Black & White 1.75L Sam's ($383.63) vs William Lawson's 2L Alianza ($470)" }
      ],
      "Licor de Whisky - Honey": [
        { a: "Tennesse Apple 700", storeA: "Sam's Club", b: "Apple Tennessee 700", storeB: "Bodegas Alianza", label: "Jack Daniel's Apple Sam's ($360.10) vs Alianza ($378)" },
        { a: "Honey Tennessee 700", storeA: "Bodegas Alianza", b: "Tennessee Honey 700", storeB: "Chedraui", label: "Jack Daniel's Honey Alianza ($378) vs Chedraui ($485)" },
        { a: "Honey Tennessee 700", storeA: "Bodegas Alianza", b: "Tennessee Honey 1 L", storeB: "Sam's Club", label: "Jack Daniel's Honey 700ml Alianza ($378) vs 1.0L Sam's ($504.34)" },
        { a: "Passport Honey 700", storeA: "Chedraui", b: "Honey Tennessee 700", storeB: "Bodegas Alianza", label: "Passport Honey Chedraui ($161.85) vs Jack Daniel's Honey ($378)" }
      ],
      "Vino - Tinto Clericot": [
        { a: "Don Simón Joven 1 L", storeA: "Walmart", b: "California Tetra Pak 946", storeB: "Bodegas Alianza", label: "Don Simón 1L Walmart ($69) vs California Tetra Alianza ($83)" },
        { a: "California Tetra Pak 946", storeA: "Bodegas Alianza", b: "California Cabernet Sauvignon 4 L", storeB: "Soriana", label: "California Tetra Alianza ($83) vs California 4L Soriana ($425)" },
        { a: "California Cabernet Sauvignon 4 L", storeA: "Soriana", b: "Vino Tinto California 4 L", storeB: "Chedraui", label: "California 4L Soriana ($425) vs Chedraui ($465)" }
      ],
      "Todas": [
        { a: "Maestro Dobel Diamante Cristalino 700", storeA: "Sam's Club", b: "Maestro Dobel Diamante 700", storeB: "Bodegas Alianza", label: "Dobel Diamante Sam's ($509) vs Alianza ($573.75) [Tequila Crist]" },
        { a: "Don Julio 70 700", storeA: "Bodegas Alianza", b: "Don Julio 70 Cristalino 700", storeB: "Walmart", label: "Don Julio 70 Alianza ($655) vs Walmart ($699) [Tequila Crist]" },
        { a: "400 Conejos Joven Espadín Tobala", storeA: "Bodegas Alianza", b: "400 Conejos Tobalá 700", storeB: "Chedraui", label: "400 Conejos Tobalá Alianza ($650) vs Chedraui ($699) [Mezcal]" },
        { a: "Johnnie Walker Red Label 1.75", storeA: "Sam's Club", b: "Red Label Blended Scotch 700", storeB: "Bodegas Alianza", label: "Red Label 1.75L Sam's ($506.39) vs 700ml Alianza ($264) [Whisky]" },
        { a: "Don Simón Joven 1 L", storeA: "Walmart", b: "California Tetra Pak 946", storeB: "Bodegas Alianza", label: "Don Simón 1L Walmart ($69) vs California Tetra ($83) [Vino]" }
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

    function normalizarTextoBusqueda(str) {
      return String(str || "")
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/['’`]/g, "")
        .replace(/(\d+(?:\.\d+)?)\s*(ml|l)\b/gi, "$1 $2")
        .replace(/[^a-z0-9.%]+/g, " ")
        .trim()
        .replace(/\s+/g, " ");
    }

    function tokenCoincide(qTok, pTokens) {
      if (pTokens.includes(qTok)) return true;
      if (qTok.length >= 3 && !/^\d/.test(qTok)) {
        return pTokens.some(pt => pt.startsWith(qTok));
      }
      return false;
    }

    function buscarIndice(prodKw, storeKw, catKw) {
      const tokens = normalizarTextoBusqueda(prodKw).split(" ").filter(Boolean);
      const stNorm = storeKw ? normalizarTextoBusqueda(storeKw) : "";
      const quiereCrist = tokens.some(t => ["cristalino", "crist", "diamante", "70", "ultra"].includes(t));
      const candidatos = [];

      for (let i = 0; i < DATOS_COMPLETOS.length; i++) {
        const p = DATOS_COMPLETOS[i];
        if (catKw && catKw !== "Todas" && p.categoria_comparable !== catKw) continue;
        const pNorm = normalizarTextoBusqueda(p.producto);
        const pTokens = pNorm.split(" ").filter(Boolean);
        const tNorm = normalizarTextoBusqueda(p.tienda);

        if (tokens.every(tok => tokenCoincide(tok, pTokens))) {
          if (!stNorm || tNorm.includes(stNorm)) {
            const catNormTokens = normalizarTextoBusqueda(p.categoria_comparable || "").split(" ");
            const esCrist = pTokens.includes("cristalino") || catNormTokens.includes("cristalino");
            const penalizacion = (quiereCrist === esCrist) ? 0 : 1;
            candidatos.push({ penalizacion, i });
          }
        }
      }

      if (candidatos.length > 0) {
        candidatos.sort((a, b) => (a.penalizacion - b.penalizacion) || (a.i - b.i));
        return candidatos[0].i;
      }
      return -1;
    }

    // PERSISTENCIA REACTIVA EN LOCALSTORAGE (B1)
    function guardarCanastaEnStorage() {
      try {
        if (typeof localStorage === "undefined") return;
        const itemsRespaldo = Object.entries(canastaPersonalizada)
          .filter(([idx, cant]) => DATOS_COMPLETOS[idx] && cant > 0)
          .map(([idx, cant]) => ({
            idx: Number(idx),
            cant: Number(cant),
            tienda: DATOS_COMPLETOS[idx].tienda,
            producto: DATOS_COMPLETOS[idx].producto
          }));
        const payload = {
          items: itemsRespaldo,
          presupuesto: PRESUPUESTO_OBJETIVO,
          cooperadores: COOPERADORES_TOTAL
        };
        localStorage.setItem(CLAVE_STORAGE_CANASTA, JSON.stringify(payload));
      } catch (_) {}
    }

    function cargarCanastaDeStorage() {
      try {
        if (typeof localStorage === "undefined") return;
        const raw = localStorage.getItem(CLAVE_STORAGE_CANASTA);
        if (!raw) return;
        const data = JSON.parse(raw);
        if (!data || typeof data !== "object") return;

        if (typeof data.presupuesto === "number" && data.presupuesto > 0) {
          PRESUPUESTO_OBJETIVO = data.presupuesto;
          const elP = document.getElementById("input-presupuesto-global");
          if (elP) elP.value = String(data.presupuesto);
        }
        if (typeof data.cooperadores === "number" && data.cooperadores > 0) {
          COOPERADORES_TOTAL = data.cooperadores;
          const elC = document.getElementById("input-cooperadores-global");
          if (elC) elC.value = String(data.cooperadores);
        }

        if (Array.isArray(data.items)) {
          const restaurada = {};
          data.items.forEach(entry => {
            if (!entry || entry.cant <= 0) return;
            let idx = typeof entry.idx === "number" ? entry.idx : -1;
            const candidato = DATOS_COMPLETOS[idx];
            if (!candidato || candidato.producto !== entry.producto || candidato.tienda !== entry.tienda) {
              idx = buscarIndice(entry.producto || "", entry.tienda || "");
            }
            if (idx !== -1 && DATOS_COMPLETOS[idx]) {
              restaurada[idx] = Math.min(99, Number(entry.cant));
            }
          });
          canastaPersonalizada = restaurada;
        }
      } catch (_) {}
    }

    // SINCRONIZACIÓN DINÁMICA DE CONTEOS Y KPIS GLOBALES DESDE DATOS_COMPLETOS (D2)
    function sincronizarMetricasGlobalesDOM() {
      const totalSkus = DATOS_COMPLETOS.length;
      const conteoPorCat = {};
      const conteoPorSub = {};
      const clavesCross = new Set();
      let maxPctAhorroCross = 0;
      let minVinoLitro = Infinity;

      DATOS_COMPLETOS.forEach(item => {
        conteoPorCat[item.categoria] = (conteoPorCat[item.categoria] || 0) + 1;
        conteoPorSub[item.categoria_comparable] = (conteoPorSub[item.categoria_comparable] || 0) + 1;
        if (item.es_comparable_cross_tienda && item.clave_comparativa) {
          clavesCross.add(item.clave_comparativa);
          const pMax = (item.precio_minimo_cross || 0) + (item.ahorro_maximo_cross || 0);
          if (pMax > 0 && item.ahorro_maximo_cross > 0) {
            const pct = Math.round((item.ahorro_maximo_cross / pMax) * 100);
            if (pct > maxPctAhorroCross) maxPctAhorroCross = pct;
          }
        }
        if (item.categoria === "Vino" && item.disponibilidad !== "agotado" && item.precio_por_litro > 0) {
          if (item.precio_por_litro < minVinoLitro) minVinoLitro = item.precio_por_litro;
        }
      });

      // Actualizar SUBTIPOS_POR_MACRO con los conteos reales del dataset
      Object.entries(SUBTIPOS_POR_MACRO).forEach(([macro, lista]) => {
        const totalMacro = conteoPorCat[macro] || 0;
        lista.forEach(op => {
          const base = op.baseLabel || op.label.replace(/\s*\(\d+\)\s*$/, "");
          op.baseLabel = base;
          if (op.value === "Todos_Macro") {
            op.label = `${base} (${totalMacro})`;
          } else {
            const nSub = conteoPorSub[op.value] || 0;
            op.label = `${base} (${nSub})`;
          }
        });
      });

      // Actualizar opciones del selector de macro-categoría en Catálogo
      const selMacro = document.getElementById("filtro-macro-categoria");
      if (selMacro) {
        const nombresMacro = {
          "Todas": `Todas las Bebidas (${totalSkus})`,
          "Tequila": `Tequila (${conteoPorCat["Tequila"] || 0})`,
          "Mezcal": `Mezcal (${conteoPorCat["Mezcal"] || 0})`,
          "Whisky": `Whisky Escocés (${conteoPorCat["Whisky"] || 0})`,
          "Licor de Whisky": `Licor Whisky (Honey & Apple) (${conteoPorCat["Licor de Whisky"] || 0})`,
          "Vino": `Vino Tinto (${conteoPorCat["Vino"] || 0})`
        };
        Array.from(selMacro.options).forEach(opt => {
          if (nombresMacro[opt.value]) opt.textContent = nombresMacro[opt.value];
        });
      }

      const elHeaderSkus = document.getElementById("badge-header-skus");
      if (elHeaderSkus) elHeaderSkus.textContent = `Auditado • 6 Cadenas Verificadas • ${totalSkus} SKUs`;

      const elFooterSkus = document.getElementById("kpi-total-skus-footer");
      if (elFooterSkus) elFooterSkus.textContent = `6 comercios · ${totalSkus} SKUs`;

      const elCrossEtiq = document.getElementById("kpi-cross-etiquetas");
      if (elCrossEtiq && clavesCross.size > 0) elCrossEtiq.textContent = `${clavesCross.size} Etiquetas`;

      const elCrossMax = document.getElementById("kpi-cross-ahorro-max");
      if (elCrossMax && maxPctAhorroCross > 0) elCrossMax.textContent = `Hasta ${maxPctAhorroCross}% / bot.`;

      const elVinoMin = document.getElementById("kpi-mejor-vino-litro");
      if (elVinoMin && isFinite(minVinoLitro)) elVinoMin.textContent = `$${minVinoLitro.toFixed(2)}/L`;

      // Sincronizar dinámicamente vigencias y nombres de campaña por tienda (Scraping Automático)
      if (typeof CAMPANAS_ACTIVAS === "object" && CAMPANAS_ACTIVAS !== null) {
        document.querySelectorAll("[data-vigencia-tienda]").forEach(el => {
          const t = el.dataset.vigenciaTienda;
          const info = CAMPANAS_ACTIVAS[t];
          if (info && info.vigencia_corta) {
            el.textContent = info.vigencia_corta;
            if (info.campana) {
              const tooltip = `${t}: ${info.campana} (hasta ${info.vigencia_corta}) · Verificado al ${info.fecha_auditoria || ''}`;
              el.title = tooltip;
              if (el.parentElement && el.parentElement.tagName === "SPAN" && el.parentElement.hasAttribute("title")) {
                el.parentElement.title = tooltip;
              }
            }
          }
        });

        const elListaVig = document.getElementById("lista-vigencias-resumen");
        if (elListaVig && Object.keys(CAMPANAS_ACTIVAS).length > 0) {
          const colores = {
            "Bodegas Alianza": "text-primary",
            "Sam's Club": "text-[#1E3A8A]",
            "Costco": "text-[#991B1B]",
            "Walmart": "text-[#0C4A6E]",
            "Chedraui": "text-[#9A3412]",
            "Soriana": "text-[#881337]"
          };
          const nombresCortos = {
            "Bodegas Alianza": "Alianza",
            "Sam's Club": "Sam's",
            "Costco": "Costco",
            "Walmart": "Walmart",
            "Chedraui": "Chedraui",
            "Soriana": "Soriana"
          };
          elListaVig.innerHTML = Object.entries(CAMPANAS_ACTIVAS).map(([tienda, info]) => {
            const color = colores[tienda] || "text-on-surface";
            const nom = nombresCortos[tienda] || tienda;
            const fullText = `• ${nom}: ${info.vigencia_corta} (${info.campana})`;
            return `<li class="truncate" title="${fullText}">• ${nom}: <strong class="${color}">${info.vigencia_corta}</strong> (${info.campana})</li>`;
          }).join("");
        }
      }
    }

    document.addEventListener("DOMContentLoaded", () => {
      // H51: al cargar, abrir de inmediato la pestaña indicada en la URL sin scroll animado
      const tabInicial = idTabDesdeHash();
      if (tabInicial) cambiarTab(tabInicial);
      const preloadStyle = document.getElementById("tab-preload-style");
      if (preloadStyle) preloadStyle.remove();

      cargarCanastaDeStorage();
      sincronizarMetricasGlobalesDOM();
      actualizarSubtiposCatalogo();
      actualizarSubtiposVersus();
      inicializarSelectorCrossTiendaVersus();
      renderizarCanastasDinamicas();
      renderizarConstructorCanasta();
      actualizarEstadoOrden();
    });
