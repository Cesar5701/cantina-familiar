    function agregarDesdeTabla(idx) {
      modificarCantidad(idx, 1);
      mostrarToast(`Añadido al carrito: ${DATOS_COMPLETOS[idx].producto}`);
    }

    function mostrarToast(mensaje) {
      const toast = document.getElementById("toast-notif");
      toast.innerText = mensaje;
      toast.classList.add("show");
      setTimeout(() => {
        toast.classList.remove("show");
      }, 2500);
    }

    function modificarCantidad(idx, delta) {
      const actual = canastaPersonalizada[idx] || 0;
      const nuevo = actual + delta;
      if (nuevo <= 0) {
        delete canastaPersonalizada[idx];
      } else {
        canastaPersonalizada[idx] = nuevo;
      }
      renderizarConstructorCanasta();
    }

    function fijarCantidad(idx, valor) {
      const cant = parseInt(valor);
      if (isNaN(cant) || cant <= 0) {
        delete canastaPersonalizada[idx];
      } else {
        canastaPersonalizada[idx] = Math.min(99, cant);
      }
      renderizarConstructorCanasta();
    }

    function eliminarProducto(idx) {
      delete canastaPersonalizada[idx];
      renderizarConstructorCanasta();
    }

    function vaciarCarrito() {
      canastaPersonalizada = {};
      renderizarConstructorCanasta();
      mostrarToast("Carrito vaciado");
    }

    // GENERADOR DINÁMICO DE CANASTAS
    function construirCanastaDinamica(perfil) {
      const nPersonas = COOPERADORES_TOTAL > 0 ? COOPERADORES_TOTAL : 12;

      const idxDobelSams = buscarIndice("Maestro Dobel  Diamante Cristalino 700", "Sam");
      const idx1800CristAlianza = buscarIndice("1800 Añejo Cristalino 100% 700", "Alianza");
      const idxDonJulioWalmart = buscarIndice("Don Julio 70 Cristalino 700", "Walmart");
      const idxMemberCristSams = buscarIndice("Member's Mark  Añejo Cristalino 1.75", "Sam");

      const idxTresGenAlianza = buscarIndice("Tres Generaciones Añejo 750", "Alianza");
      const idx1800AnejoChedraui = buscarIndice("1800 Añejo 700ml", "Chedraui");
      const idxHerraduraAnejo = buscarIndice("Herradura Añejo", "Alianza");

      const idxAmarasRep = buscarIndice("Amarás Rep Espadín", "Alianza");
      const idx400RepChedraui = buscarIndice("400 Conejos Reposado 700ml", "Chedraui");
      const idx400TobalaChedraui = buscarIndice("400 Conejos Tobalá 700ml", "Chedraui");
      const idx400AnejoAlianza = buscarIndice("400 Conejos Añejo 700", "Alianza");
      const idxAmarasCupreata = buscarIndice("Amarás Joven Cupreata", "Alianza");

      const idxJWRedSams = buscarIndice("Johnnie Walker Red Label 1.75", "Sam");
      const idxBW175Sams = buscarIndice("Black & White  1.75", "Sam");
      const idxHoneyAlianza = buscarIndice("Honey Tennessee 700", "Alianza");

      const idxDonSimon5L = buscarIndice("Don Simon  5 L", "Sam");
      const idxCalTetra = buscarIndice("California Tetra Pak 946", "Alianza");
      const idxCarloRossi4L = buscarIndice("Carlo Rossi  Blend 4", "Sam");

      const factorEscala = Math.max(1, nPersonas / 12);
      let seleccion = {};

      if (perfil === 'rendimiento') {
        if (idxMemberCristSams !== -1) seleccion[idxMemberCristSams] = Math.max(1, Math.round(1 * factorEscala));
        if (idxDobelSams !== -1) seleccion[idxDobelSams] = Math.max(1, Math.round(1.5 * factorEscala));
        if (idxTresGenAlianza !== -1) seleccion[idxTresGenAlianza] = Math.max(1, Math.round(1 * factorEscala));
        if (idxAmarasRep !== -1) seleccion[idxAmarasRep] = Math.max(1, Math.round(1.5 * factorEscala));
        if (idx400TobalaChedraui !== -1) seleccion[idx400TobalaChedraui] = Math.max(1, Math.round(1 * factorEscala));
        if (idxBW175Sams !== -1) seleccion[idxBW175Sams] = Math.max(1, Math.round(1 * factorEscala));
        if (idxHoneyAlianza !== -1) seleccion[idxHoneyAlianza] = Math.max(1, Math.round(1.5 * factorEscala));
        if (idxDonSimon5L !== -1) seleccion[idxDonSimon5L] = Math.max(1, Math.round(1 * factorEscala));
      } else if (perfil === 'equilibrada') {
        if (idxDobelSams !== -1) seleccion[idxDobelSams] = Math.max(1, Math.round(2 * factorEscala));
        if (idx1800CristAlianza !== -1) seleccion[idx1800CristAlianza] = Math.max(1, Math.round(1 * factorEscala));
        if (idx1800AnejoChedraui !== -1) seleccion[idx1800AnejoChedraui] = Math.max(1, Math.round(1 * factorEscala));
        if (idx400RepChedraui !== -1) seleccion[idx400RepChedraui] = Math.max(1, Math.round(1.5 * factorEscala));
        if (idx400TobalaChedraui !== -1) seleccion[idx400TobalaChedraui] = Math.max(1, Math.round(1 * factorEscala));
        if (idxJWRedSams !== -1) seleccion[idxJWRedSams] = Math.max(1, Math.round(1 * factorEscala));
        if (idxHoneyAlianza !== -1) seleccion[idxHoneyAlianza] = Math.max(1, Math.round(2 * factorEscala));
        if (idxCalTetra !== -1) seleccion[idxCalTetra] = Math.max(3, Math.round(4.5 * factorEscala));
      } else if (perfil === 'gala') {
        if (idxDonJulioWalmart !== -1) seleccion[idxDonJulioWalmart] = Math.max(1, Math.round(2 * factorEscala));
        if (idxDobelSams !== -1) seleccion[idxDobelSams] = Math.max(1, Math.round(1.5 * factorEscala));
        if (idxHerraduraAnejo !== -1) seleccion[idxHerraduraAnejo] = Math.max(1, Math.round(1 * factorEscala));
        if (idxAmarasCupreata !== -1) seleccion[idxAmarasCupreata] = Math.max(1, Math.round(1 * factorEscala));
        if (idx400AnejoAlianza !== -1) seleccion[idx400AnejoAlianza] = Math.max(1, Math.round(1 * factorEscala));
        if (idxJWRedSams !== -1) seleccion[idxJWRedSams] = Math.max(1, Math.round(1 * factorEscala));
        if (idxHoneyAlianza !== -1) seleccion[idxHoneyAlianza] = Math.max(2, Math.round(2.5 * factorEscala));
        if (idxCarloRossi4L !== -1) seleccion[idxCarloRossi4L] = Math.max(1, Math.round(1 * factorEscala));
      }

      if (PRESUPUESTO_OBJETIVO >= 1200) {
        const calcTotal = (sel) => Object.entries(sel).reduce((acc, [k, c]) => acc + (DATOS_COMPLETOS[k].precio_promo * c), 0);
        let iter = 0;
        while (calcTotal(seleccion) > PRESUPUESTO_OBJETIVO && iter < 40) {
          const entradas = Object.entries(seleccion).filter(([_, c]) => c > 0);
          if (entradas.length <= 2) break;
          entradas.sort((a, b) => b[1] - a[1]);
          const [idxMax, cantMax] = entradas[0];
          if (cantMax > 1) seleccion[idxMax] = cantMax - 1;
          else delete seleccion[idxMax];
          iter++;
        }
        const candidatosExtra = [idxDobelSams, idx1800CristAlianza, idx400TobalaChedraui, idxHoneyAlianza].filter(i => i !== -1);
        let idxCand = 0;
        while (calcTotal(seleccion) < PRESUPUESTO_OBJETIVO * 0.85 && iter < 60 && candidatosExtra.length > 0) {
          const prodIdx = candidatosExtra[idxCand % candidatosExtra.length];
          const precioProd = DATOS_COMPLETOS[prodIdx].precio_promo;
          if (calcTotal(seleccion) + precioProd <= PRESUPUESTO_OBJETIVO) {
            seleccion[prodIdx] = (seleccion[prodIdx] || 0) + 1;
          } else {
            break;
          }
          idxCand++;
          iter++;
        }
      }

      return seleccion;
    }

    function renderizarCanastasDinamicas() {
      const cont = document.getElementById("contenedor-canastas-dinamicas");
      const sub = document.getElementById("subtitulo-generador-dinamico");
      if (!cont) return;

      const tieneDatos = PRESUPUESTO_OBJETIVO > 0 || COOPERADORES_TOTAL > 0;
      if (tieneDatos) {
        const txtPres = PRESUPUESTO_OBJETIVO > 0 ? `Presupuesto activo: $${PRESUPUESTO_OBJETIVO.toLocaleString('es-MX')}` : `Presupuesto libre`;
        const txtPers = COOPERADORES_TOTAL > 0 ? `${COOPERADORES_TOTAL} personas` : `Base 12 personas`;
        sub.innerHTML = `<span class="text-[#784516] font-bold">Recalculado en vivo (${txtPres} · ${txtPers}):</span> Toca cualquiera de las 3 propuestas dinámicas para cargarla al carrito.`;
      } else {
        sub.innerText = "Ingresa arriba tu Presupuesto ($) y Personas (N) para que estas 3 propuestas recalculen su número de botellas y cuota automáticamente.";
      }

      const perfiles = [
        {
          id: "rendimiento",
          titulo: "1. Máximo Rendimiento $/L",
          badgeBg: "bg-[#D3E8DC] text-[#0B2016] border-[#B7D6C5]",
          desc: "Prioriza presentaciones de 1.75L y 5L en Sam's, Chedraui y Alianza."
        },
        {
          id: "equilibrada",
          titulo: "2. Selección Equilibrada",
          badgeBg: "bg-[#F8E2C8] text-[#784516] border-[#E5C8A3]",
          desc: "Dobel Diamante, 1800 Cristalino y Añejo, 400 Conejos Tobalá, Red Label y Honey."
        },
        {
          id: "gala",
          titulo: "3. Cava de Gala & Silvestres",
          badgeBg: "bg-[#FAD9DF] text-[#753B47] border-[#E5B3BC]",
          desc: "Don Julio 70, Herradura Añejo, Amarás Cupreata Silvestre, Red Label y Honey."
        }
      ];

      let html = "";
      perfiles.forEach(p => {
        const sel = construirCanastaDinamica(p.id);
        let totalCosto = 0;
        let totalBotellas = 0;
        let lineas = [];

        Object.entries(sel).forEach(([strIdx, cant]) => {
          const item = DATOS_COMPLETOS[parseInt(strIdx)];
          if (!item || cant <= 0) return;
          totalCosto += item.precio_promo * cant;
          totalBotellas += cant;
          const nombreCorto = item.producto.replace(/^Tequila |^Mezcal |^Whisky |^Whiskey |^Vino Tinto /i, '').slice(0, 32);
          lineas.push(`<li>• <strong>${cant}×</strong> ${nombreCorto} <span class="text-[#574A3D]">(${item.tienda})</span></li>`);
        });

        const cuotaTexto = COOPERADORES_TOTAL > 0
          ? `$${(totalCosto / COOPERADORES_TOTAL).toFixed(2)} por persona (${COOPERADORES_TOTAL}p)`
          : `Ingresa personas arriba para ver cuota`;

        html += `
          <div class="md3-surface-low p-4 flex flex-col justify-between transition-all hover:border-[#8A7B6B]">
            <div>
              <div class="flex justify-between items-center gap-2">
                <span class="badge ${p.badgeBg} border">${p.titulo}</span>
                <span class="text-[11px] font-mono text-[#574A3D] font-semibold">${totalBotellas} unid.</span>
              </div>
              <div class="text-2xl font-extrabold text-[#1F1B16] mt-2 font-mono">$${totalCosto.toLocaleString('es-MX', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
              <div class="text-xs text-[#784516] font-semibold mt-0.5 font-mono">${cuotaTexto}</div>
              <p class="text-[11px] text-[#574A3D] mt-2">${p.desc}</p>
              <ul class="text-[11px] text-[#1F1B16] space-y-1 mt-3 border-t border-[#DFD5C7] pt-2.5 max-h-36 overflow-y-auto">
                ${lineas.join('')}
              </ul>
            </div>
            <button onclick="cargarCanastaDinamica('${p.id}')" class="mt-4 w-full py-2 px-3 md3-btn-tonal text-xs cursor-pointer">
              Cargar Propuesta Dinámica
            </button>
          </div>
        `;
      });

      cont.innerHTML = html;
    }

    function cargarCanastaDinamica(perfil) {
      canastaPersonalizada = construirCanastaDinamica(perfil);
      renderizarConstructorCanasta();
      mostrarToast("Canasta dinámica cargada en el carrito");
    }

    function renderizarConstructorCanasta() {
      const macros = ['Tequila', 'Mezcal', 'Whisky', 'Honey', 'Vino'];
      const itemsPorMacro = { Tequila: [], Mezcal: [], Whisky: [], Honey: [], Vino: [] };
      const subtotales = {
        Tequila: { cant: 0, total: 0 },
        Mezcal: { cant: 0, total: 0 },
        Whisky: { cant: 0, total: 0 },
        Honey: { cant: 0, total: 0 },
        Vino: { cant: 0, total: 0 }
      };

      let granTotal = 0;
      let totalPiezas = 0;
      let totalVolumenMl = 0;
      let subAlianza = 0;
      let subSams = 0;
      let subCostco = 0;
      let subWalmart = 0;
      let subChedraui = 0;
      let subSoriana = 0;

      Object.keys(canastaPersonalizada).forEach(strIdx => {
        const idx = parseInt(strIdx);
        const cant = canastaPersonalizada[idx];
        const item = DATOS_COMPLETOS[idx];
        if (!item || cant <= 0) return;

        const macro = getMacroCategoria(item);
        if (itemsPorMacro[macro]) {
          itemsPorMacro[macro].push({ item, idx, cant });
          const sub = cant * item.precio_promo;
          subtotales[macro].cant += cant;
          subtotales[macro].total += sub;

          granTotal += sub;
          totalPiezas += cant;
          totalVolumenMl += (cant * (item.ml || 750));

          if (item.tienda === "Sam's Club") subSams += sub;
          else if (item.tienda === "Costco") subCostco += sub;
          else if (item.tienda === "Walmart") subWalmart += sub;
          else if (item.tienda === "Chedraui") subChedraui += sub;
          else if (item.tienda === "Soriana") subSoriana += sub;
          else subAlianza += sub;
        }
      });

      macros.forEach(macro => {
        const cont = document.getElementById(`lista-botellas-${macro.toLowerCase()}`);
        if (!cont) return;

        const items = itemsPorMacro[macro];
        if (items.length === 0) {
          const catNombre = macro === "Honey" ? "Licor de Whisky Honey" : macro;
          const catFiltro = macro === "Honey" ? "Licor de Whisky" : macro;
          cont.innerHTML = `
            <div class="p-4 text-center text-xs text-[#574A3D] md3-surface-low border-dashed rounded-2xl flex flex-col sm:flex-row items-center justify-between gap-3">
              <span>Sin botellas de ${catNombre} agregadas al carrito.</span>
              <button type="button" onclick="cambiarTab('tab-rankings'); document.getElementById('filtro-macro-categoria').value='${catFiltro}'; actualizarSubtiposCatalogo();" class="px-3.5 py-1.5 md3-btn-tonal text-xs font-semibold cursor-pointer inline-flex items-center gap-1.5 transition-all">
                <span>Añadir desde Catálogo</span> <span>→</span>
              </button>
            </div>
          `;
        } else {
          let html = "";
          items.forEach(({ item, idx, cant }) => {
            const costoLinea = cant * item.precio_promo;
            const tiendaBadge = getBadgeTienda(item.tienda, true);

            let claseBadgeColor = "bg-[#EFE8DC] text-[#574A3D] border-[#D6C8B8]";
            if (item.categoria_comparable.includes("Añejo Cristalino")) claseBadgeColor = "bg-[#F8E2C8] text-[#784516] border-[#E5C8A3]";
            else if (item.categoria_comparable.includes("Silvestre")) claseBadgeColor = "bg-[#D3E8DC] text-[#0B2016] border-[#B7D6C5]";

            let alertaAhorro = "";
            if (item.es_comparable_cross_tienda && !item.es_precio_mas_bajo && item.diferencia_vs_minimo > 0) {
              const ahorroTotalLinea = (item.diferencia_vs_minimo * cant).toFixed(2);
              alertaAhorro = `
                <div class="mt-2 p-2 rounded-xl bg-[#FDE8E8] border border-[#F8B4B4] text-[11px] flex items-center justify-between gap-2 flex-wrap">
                  <div class="text-[#9B1C1C]">
                    <strong>Disponible más barato en ${item.tienda_mas_barata}:</strong> a $${item.precio_minimo_cross.toFixed(2)} (Ahorras <strong>$${item.diferencia_vs_minimo.toFixed(2)}/u</strong> · Total: <strong>$${ahorroTotalLinea}</strong>).
                  </div>
                  <button type="button" onclick="cambiarTiendaCarrito(${idx})" class="px-2.5 py-1 rounded-lg bg-[#9B1C1C] hover:bg-[#771D1D] text-white font-bold text-[10px] whitespace-nowrap cursor-pointer transition-colors shadow-sm" title="Cambiar a la oferta de ${item.tienda_mas_barata}">
                    Cambiar a ${item.tienda_mas_barata}
                  </button>
                </div>
              `;
            }

            let badgeStockCarrito = "";
            if (item.disponibilidad === "agotado") {
              badgeStockCarrito = `<span class="badge bg-[#fbeae8] text-[#ba1a1a] border border-[#ffdad6] text-[10px] font-bold">⚠️ Agotado</span>`;
            } else if (item.stock_unidades !== null && item.stock_unidades !== undefined && item.stock_unidades !== "" && Number(item.stock_unidades) > 0 && Number(item.stock_unidades) <= 5) {
              badgeStockCarrito = `<span class="badge bg-[#fef3eb] text-[#8c5332] border border-[#f3ddce] text-[10px] font-semibold">Últimas ${item.stock_unidades} pzas</span>`;
            }

            let alertaStock = "";
            if (item.disponibilidad === "agotado") {
              alertaStock = `
                <div class="mt-2 p-2 rounded-xl bg-[#FDE8E8] border border-[#F8B4B4] text-[11px] text-[#9B1C1C]">
                  <strong>Aviso de inventario:</strong> Esta botella figura como <em>agotada</em> en ${item.tienda}. Considera verificar disponibilidad en tienda física o buscar una alternativa en otra cadena.
                </div>
              `;
            }

            html += `
              <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 md3-surface-low hover:border-[#8A7B6B] transition-colors min-w-0">
                <div class="space-y-1 flex-1 min-w-0">
                  <div class="flex flex-wrap items-center gap-1.5">
                    <span class="badge ${claseBadgeColor} border text-[10px]">${item.categoria_comparable}</span>
                    ${tiendaBadge}
                    ${badgeStockCarrito}
                    <span class="text-xs font-mono text-[#574A3D]">${item.ml} ml</span>
                  </div>
                  <div class="font-semibold text-sm text-[#1F1B16] leading-tight break-words">
                    <a href="${item.url}" target="_blank" rel="noopener noreferrer"
                       class="hover:underline hover:text-[#784516] inline-flex items-center gap-1 group"
                       title="Ver en tienda oficial ${item.tienda}">
                      <span>${item.producto}</span>
                      <span class="text-[10px] text-[#8A7B6B] group-hover:text-[#784516] inline-block">↗</span>
                    </a>
                  </div>
                  <div class="text-xs text-[#574A3D] font-mono">
                    Unitario: <strong class="text-[#784516] font-bold">$${item.precio_promo.toFixed(2)}</strong> · <span class="text-[#486355] font-semibold">$${item.precio_por_litro.toFixed(2)} / L</span>
                  </div>
                  ${alertaAhorro}
                  ${alertaStock}
                </div>

                <!-- CONTROLES DE CANTIDAD TÁCTILES (HIG 44pt) -->
                <div class="flex items-center justify-between sm:justify-end gap-3 border-t sm:border-t-0 pt-2.5 sm:pt-0 border-[#DFD5C7] sm:flex-shrink-0">
                  <div class="flex items-center gap-1 bg-white p-1 rounded-lg border border-[#D6C8B8]">
                    <button onclick="modificarCantidad(${idx}, -1)" class="w-8 h-8 flex items-center justify-center rounded-md bg-[#EFE8DC] hover:bg-[#E6DDD0] text-sm font-bold text-[#1F1B16] transition-colors cursor-pointer">
                      −
                    </button>
                    <input type="number" min="0" max="99" value="${cant}"
                           aria-label="Cantidad de botellas"
                           onchange="fijarCantidad(${idx}, this.value)"
                           class="w-10 text-center bg-transparent font-mono font-bold text-sm text-[#1F1B16] focus:outline-none">
                    <button onclick="modificarCantidad(${idx}, 1)" class="w-8 h-8 flex items-center justify-center rounded-md bg-[#EFE8DC] hover:bg-[#E6DDD0] text-sm font-bold text-[#1F1B16] transition-colors cursor-pointer">
                      +
                    </button>
                  </div>

                  <div class="text-right min-w-[5.5rem]">
                    <div class="text-[11px] text-[#574A3D]">Subtotal:</div>
                    <div class="font-bold font-mono text-sm text-[#784516]">$${costoLinea.toFixed(2)}</div>
                  </div>

                  <button onclick="eliminarProducto(${idx})" title="Quitar botella" class="w-8 h-8 flex items-center justify-center rounded-lg text-[#8A7B6B] hover:text-[#753B47] hover:bg-[#FAD9DF] transition-colors cursor-pointer">
                    ✕
                  </button>
                </div>
              </div>
            `;
          });
          cont.innerHTML = html;
        }

        document.getElementById(`subtotal-cant-${macro.toLowerCase()}`).innerText = `${subtotales[macro].cant} ${macro === 'Vino' ? 'piezas' : 'botellas'}`;
        document.getElementById(`subtotal-precio-${macro.toLowerCase()}`).innerText = `$${subtotales[macro].total.toLocaleString('es-MX', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
      });

      const litros = totalVolumenMl / 1000;
      document.getElementById("badge-nav-carrito-count").innerText = totalPiezas;
      const mobBadge = document.getElementById("mob-badge-carrito");
      if (mobBadge) mobBadge.innerText = totalPiezas;

      document.getElementById("sim-total-piezas").innerText = `${totalPiezas} ${totalPiezas === 1 ? 'unidad' : 'unidades'}`;
      document.getElementById("sim-total-volumen").innerText = `${litros.toFixed(2)} Litros`;

      document.getElementById("sim-total-alianza").innerText = `$${subAlianza.toLocaleString('es-MX', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
      document.getElementById("sim-total-sams").innerText = `$${subSams.toLocaleString('es-MX', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
      const elCostco = document.getElementById("sim-total-costco");
      if (elCostco) elCostco.innerText = `$${subCostco.toLocaleString('es-MX', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
      document.getElementById("sim-total-walmart").innerText = `$${subWalmart.toLocaleString('es-MX', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
      document.getElementById("sim-total-chedraui").innerText = `$${subChedraui.toLocaleString('es-MX', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
      document.getElementById("sim-total-soriana").innerText = `$${subSoriana.toLocaleString('es-MX', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
      document.getElementById("sim-gran-total").innerText = `$${granTotal.toLocaleString('es-MX', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;

      if (COOPERADORES_TOTAL > 0) {
        const cuota = granTotal / COOPERADORES_TOTAL;
        document.getElementById("badge-sidebar-cooperadores").innerText = `${COOPERADORES_TOTAL} Personas`;
        document.getElementById("sim-cuota-persona").innerText = `$${cuota.toLocaleString('es-MX', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
        document.getElementById("sim-subtitulo-cuota").innerText = `Dividido entre ${COOPERADORES_TOTAL} cooperadores`;
      } else {
        document.getElementById("badge-sidebar-cooperadores").innerText = `Sin definir`;
        document.getElementById("sim-cuota-persona").innerText = granTotal > 0 ? `$${granTotal.toLocaleString('es-MX', {minimumFractionDigits: 2, maximumFractionDigits: 2})}` : `—`;
        document.getElementById("sim-subtitulo-cuota").innerText = `Escribe el N° de personas arriba para dividir la cuenta`;
      }

      const barraEl = document.getElementById("sim-barra-dinamica");
      const alertaBox = document.getElementById("sim-alerta-sobrante");
      const labelSobrante = document.getElementById("sim-label-sobrante");
      const valSobrante = document.getElementById("sim-sobrante");

      if (PRESUPUESTO_OBJETIVO > 0) {
        const sobrante = PRESUPUESTO_OBJETIVO - granTotal;
        const porcentajeUso = Math.min(100, (granTotal / PRESUPUESTO_OBJETIVO) * 100);
        document.getElementById("sim-porcentaje-barra").innerText = `${porcentajeUso.toFixed(1)}%`;
        barraEl.style.width = `${porcentajeUso}%`;

        if (granTotal > PRESUPUESTO_OBJETIVO) {
          barraEl.className = "bg-[#ba1a1a] h-full rounded-full transition-all duration-300";
          alertaBox.className = "p-2 rounded flex flex-col justify-between text-xs bg-error-container border border-[#e0a8a1]";
          labelSobrante.innerText = "Excedente sobre tope:";
          labelSobrante.className = "text-on-error-container font-bold text-[10px]";
          valSobrante.innerText = `-$${Math.abs(sobrante).toLocaleString('es-MX', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
          valSobrante.className = "text-on-error-container font-black text-xs font-mono mt-0.5";
        } else {
          barraEl.className = "bg-primary h-full rounded-full transition-all duration-300";
          alertaBox.className = "p-2 rounded flex flex-col justify-between text-xs bg-[#eaf4ec] border border-[#c5dfc9]";
          labelSobrante.innerText = "Presupuesto Disponible:";
          labelSobrante.className = "text-[#24592a] font-medium text-[10px]";
          valSobrante.innerText = `+$${sobrante.toLocaleString('es-MX', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
          valSobrante.className = "text-[#24592a] font-bold text-xs font-mono mt-0.5";
        }
      } else {
        document.getElementById("sim-porcentaje-barra").innerText = `Sin tope`;
        barraEl.style.width = `0%`;
        alertaBox.className = "p-2 rounded flex flex-col justify-between text-xs md3-surface-low";
        labelSobrante.innerText = "Presupuesto Objetivo:";
        labelSobrante.className = "text-on-surface-variant font-medium text-[10px]";
        valSobrante.innerText = "Ingresa monto arriba";
        valSobrante.className = "text-primary font-mono text-xs font-semibold mt-0.5";
      }

      // Alerta de Ahorro Potencial Cross-Tienda en Carrito
      let ahorroPotencialTotal = 0;
      Object.keys(canastaPersonalizada).forEach(strIdx => {
        const idx = parseInt(strIdx);
        const cant = canastaPersonalizada[idx];
        const item = DATOS_COMPLETOS[idx];
        if (item && cant > 0 && item.es_comparable_cross_tienda && !item.es_precio_mas_bajo && item.diferencia_vs_minimo > 0) {
          ahorroPotencialTotal += (item.diferencia_vs_minimo * cant);
        }
      });

      const alertaOptimizar = document.getElementById("sim-alerta-optimizacion");
      if (alertaOptimizar) {
        if (ahorroPotencialTotal > 0) {
          alertaOptimizar.innerHTML = `
            <div class="p-3 rounded-lg bg-[#FDE8E8] border border-[#F8B4B4] space-y-1.5 text-xs">
              <div class="flex items-center justify-between text-[#9B1C1C] font-bold">
                <span>Ahorro Cross-Tienda:</span>
                <span class="font-mono text-sm font-extrabold">$${ahorroPotencialTotal.toFixed(2)} MXN</span>
              </div>
              <p class="text-[11px] text-[#771D1D] leading-tight">
                Hay botellas en tu carrito con mejor precio en otra tienda.
              </p>
              <button onclick="optimizarTodoAlMejorPrecio()" class="w-full py-1.5 px-3 rounded-md bg-[#9B1C1C] hover:bg-[#771D1D] text-white font-bold text-xs transition-colors cursor-pointer text-center shadow-xs">
                Optimizar Carrito al Mejor Precio
              </button>
            </div>
          `;
          alertaOptimizar.classList.remove("hidden");
        } else {
          alertaOptimizar.classList.add("hidden");
        }
      }
    }

    function actualizarParametrosGlobales() {
      const valP = document.getElementById("input-presupuesto-global").value.trim();
      const valC = document.getElementById("input-cooperadores-global").value.trim();
      const p = parseFloat(valP);
      const c = parseInt(valC);

      PRESUPUESTO_OBJETIVO = (!isNaN(p) && p > 0) ? p : 0;
      COOPERADORES_TOTAL = (!isNaN(c) && c > 0) ? c : 0;

      renderizarCanastasDinamicas();
      renderizarConstructorCanasta();
      renderizarVersus();
    }

    function copiarListaCompra() {
      const macros = ['Tequila', 'Mezcal', 'Whisky', 'Honey', 'Vino'];
      let texto = `LISTA DE COMPRA MULTITIENDA - CANTINA FAMILIAR 2026\n`;
      if (PRESUPUESTO_OBJETIVO > 0 || COOPERADORES_TOTAL > 0) {
        texto += `Presupuesto: ${PRESUPUESTO_OBJETIVO > 0 ? '$' + PRESUPUESTO_OBJETIVO.toFixed(2) : 'Libre'} | Personas: ${COOPERADORES_TOTAL > 0 ? COOPERADORES_TOTAL : 'Sin definir'}\n`;
      }
      texto += `--------------------------------------------------------\n`;

      let total = 0;
      let subTiendas = {
        "Bodegas Alianza": 0,
        "Sam's Club": 0,
        "Costco": 0,
        "Walmart": 0,
        "Chedraui": 0,
        "Soriana": 0
      };

      macros.forEach(macro => {
        const items = Object.keys(canastaPersonalizada)
          .map(idx => ({ item: DATOS_COMPLETOS[idx], cant: canastaPersonalizada[idx] }))
          .filter(x => x.item && getMacroCategoria(x.item) === macro && x.cant > 0);

        if (items.length > 0) {
          texto += `\n[${macro.toUpperCase()}]\n`;
          items.forEach(({ item, cant }) => {
            const sub = cant * item.precio_promo;
            total += sub;
            subTiendas[item.tienda] = (subTiendas[item.tienda] || 0) + sub;
            texto += `• ${cant}× ${item.producto} (${item.ml}ml) - $${item.precio_promo.toFixed(2)} c/u [Sub: $${sub.toFixed(2)}] (${item.tienda})\n  ${item.url}\n`;
          });
        }
      });

      texto += `\n--------------------------------------------------------\n`;
      Object.entries(subTiendas).forEach(([tienda, monto]) => {
        if (monto > 0) {
          texto += `SUBTOTAL ${tienda.toUpperCase()}: $${monto.toFixed(2)}\n`;
        }
      });
      texto += `COSTO TOTAL: $${total.toFixed(2)} MXN\n`;
      if (COOPERADORES_TOTAL > 0) {
        texto += `CUOTA POR PERSONA (${COOPERADORES_TOTAL} personas): $${(total / COOPERADORES_TOTAL).toFixed(2)} MXN\n`;
      }
      texto += `--------------------------------------------------------\n`;
      texto += `VIGENCIAS DE OFERTAS POR TIENDA:\n__RESUMEN_WHATSAPP_VIGENCIAS__\n`;

      navigator.clipboard.writeText(texto).then(() => {
        mostrarToast("¡Lista de compras copiada al portapapeles!");
      }).catch(() => {
        mostrarToast("No se pudo copiar automáticamente.");
      });
    }
