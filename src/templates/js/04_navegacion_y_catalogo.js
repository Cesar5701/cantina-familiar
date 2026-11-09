    // PESTAÑA ACTIVA EN EL HASH (H51): la recarga conserva la pestaña elegida
    // y un enlace con fragmento (#versus, #carrito, #matriz, #rankings) abre directo en ella.
    const PESTANAS_VALIDAS = ["tab-rankings", "tab-versus", "tab-carrito", "tab-matriz"];

    function hashDesdeTab(idTab) {
      return "#" + idTab.replace(/^tab-/, "");
    }

    function escribirHashEnURL(hash) {
      if (!window.history || !history.replaceState) return;
      if (location.hash === hash) return;
      try {
        history.replaceState(null, "", hash);
      } catch (_) {
        // Entornos restringidos (p. ej. file://): la pestaña sigue operativa,
        // solo no se persiste en la URL.
      }
    }

    function idTabDesdeHash() {
      const bruto = decodeURIComponent(String(location.hash || "").replace(/^#/, "")).trim().toLowerCase();
      if (!bruto) return null;
      const id = "tab-" + bruto.replace(/^tab-/, "");
      return PESTANAS_VALIDAS.includes(id) ? id : null;
    }

    let esCargaInicialTab = true;

    // CAMBIAR PESTAÑA (SINCRONIZA BARRA DESKTOP STITCH Y TAB BAR MÓVIL)
    function cambiarTab(idTab) {
      // Limpiar estilo temporal anti-flicker si fue inyectado en el pre-render
      const preloadStyle = document.getElementById("tab-preload-style");
      if (preloadStyle) preloadStyle.remove();

      document.querySelectorAll(".tab-content").forEach(el => el.classList.add("hidden"));
      const tabTarget = document.getElementById(idTab);
      if (tabTarget) tabTarget.classList.remove("hidden");

      // Desktop Stitch Archival Bar
      document.querySelectorAll(".tab-btn").forEach(el => {
        el.classList.remove("bg-[#8c5332]", "text-white", "font-semibold", "shadow-sm");
        el.classList.add("text-[#52443c]", "font-medium");
      });
      const btn = document.getElementById("btn-" + idTab);
      if (btn) {
        btn.classList.add("bg-[#8c5332]", "text-white", "font-semibold", "shadow-sm");
        btn.classList.remove("text-[#52443c]", "font-medium");
      }

      // Mobile Bottom Tab Bar
      document.querySelectorAll(".mob-tab-btn").forEach(el => {
        el.classList.remove("text-[#703c1d]", "font-bold");
        el.classList.add("text-[#85746b]", "font-medium");
      });
      const mobBtn = document.getElementById("mob-btn-" + idTab);
      if (mobBtn) {
        mobBtn.classList.add("text-[#703c1d]", "font-bold");
        mobBtn.classList.remove("text-[#85746b]", "font-medium");
      }

      if (idTab === 'tab-rankings') {
        renderizarGraficoTop10();
      }

      // H51: dejar la pestaña activa en la URL sin recargar y sin manchar el historial.
      escribirHashEnURL(hashDesdeTab(idTab));

      if (!esCargaInicialTab) {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
      esCargaInicialTab = false;
    }

    // Restaurar pestaña si el usuario edita el fragmento o abre un enlace compartido.
    window.addEventListener("hashchange", () => {
      const id = idTabDesdeHash();
      if (id) cambiarTab(id);
    });

    function toggleFiltrosMovil() {
      const cont = document.getElementById("contenedor-controles-filtro");
      const icono = document.getElementById("icono-toggle-filtros-movil");
      if (!cont) return;
      const oculto = cont.classList.toggle("hidden");
      if (icono) {
        icono.textContent = oculto ? "expand_more" : "expand_less";
      }
    }

    function restablecerFiltros() {
      const elMacro = document.getElementById("filtro-macro-categoria");
      const elTienda = document.getElementById("filtro-tienda");
      const elBusq = document.getElementById("filtro-busqueda");
      const chkMejor = document.getElementById("filtro-mejor-precio");
      const chkDesc = document.getElementById("filtro-descuento");
      const chkMinHist = document.getElementById("filtro-minimo-historico");
      const chkDisp = document.getElementById("filtro-disponible");
      const chkPaq1 = document.getElementById("filtro-paquete");
      const chkPaq2 = document.getElementById("filtro-paquete-pill");

      if (elMacro) elMacro.value = "Todas";
      if (elTienda) elTienda.value = "Todas";
      if (elBusq) elBusq.value = "";
      if (chkMejor) chkMejor.checked = true;
      if (chkDesc) chkDesc.checked = false;
      if (chkMinHist) chkMinHist.checked = false;
      if (chkDisp) chkDisp.checked = true;
      if (chkPaq1) chkPaq1.checked = false;
      if (chkPaq2) chkPaq2.checked = false;

      columnaOrden = "precio_por_litro";
      ordenAsc = true;
      actualizarSubtiposCatalogo();
      actualizarEstadoOrden();
      mostrarToast("Filtros restablecidos al catálogo general");
    }

    function sincronizarFiltroPaquete(estado) {
      const chk1 = document.getElementById("filtro-paquete");
      const chk2 = document.getElementById("filtro-paquete-pill");
      if (chk1) chk1.checked = estado;
      if (chk2) chk2.checked = estado;
      aplicarFiltros();
    }

    function esProductoPaquete(item) {
      if (!item) return false;
      if (item.es_paquete !== undefined && typeof item.es_paquete === "boolean") return item.es_paquete;
      const nom = (item.producto || "").toLowerCase();
      const cond = (item.condiciones || "").toLowerCase();
      if (cond.includes("\u{1F381}") || cond.includes("obsequio") || cond.includes("combo") || cond.includes("kit")) return true;
      const patron = /\b(pack|paquete|combo|kit|caja|set)\b|\b\d+\s*pzas?\b|\bx\s*\d+\b|\b\d+\s*botellas?\b|\bcon\s+(vaso|copa|termo|shaker|tumbler|caballito|sal|kit)\b/i;
      if (patron.test(nom)) return true;
      if (nom.includes(" + ") || nom.includes(" c/") || nom.includes(" con ")) {
        if (/\+\s*(\d+|vaso|copa|termo|sal|bot|agua|refresco|chivas|jack|absolut|woodford|mason|shaker|tumbler)/i.test(nom)) return true;
        if (/c\/\s*(\d+|bot|vaso|copa|bal[oó]n|caballito|termo|porta|kit|escurridor|concentrado|tamborin|sangria|tinto|vino|ultra|reposado|joven|pechuga)/i.test(nom)) return true;
      }
      return false;
    }

    function aplicarFiltros() {
      const busq = document.getElementById("filtro-busqueda").value.toLowerCase();
      const macroCat = document.getElementById("filtro-macro-categoria").value;
      const subCat = document.getElementById("filtro-categoria").value;
      const tienda = document.getElementById("filtro-tienda").value;
      const soloDesc = document.getElementById("filtro-descuento") ? document.getElementById("filtro-descuento").checked : false;
      const chkMinHist = document.getElementById("filtro-minimo-historico");
      const soloMinHist = chkMinHist ? chkMinHist.checked : false;
      const chkPaq = document.getElementById("filtro-paquete") || document.getElementById("filtro-paquete-pill");
      const soloPaquete = chkPaq ? chkPaq.checked : false;
      const chkMejor = document.getElementById("filtro-mejor-precio");
      const soloMejor = chkMejor ? chkMejor.checked : true;
      const chkDisp = document.getElementById("filtro-disponible");
      const soloDisp = chkDisp ? chkDisp.checked : false;

      // Contabilizar filtros no predeterminados activos para feedback visual
      let nFiltrosActivos = 0;
      if (busq.trim()) nFiltrosActivos++;
      if (macroCat !== "Todas") nFiltrosActivos++;
      if (subCat !== "Todas" && subCat !== "Todos_Macro") nFiltrosActivos++;
      if (tienda !== "Todas") nFiltrosActivos++;
      if (soloDesc) nFiltrosActivos++;
      if (soloMinHist) nFiltrosActivos++;
      if (soloPaquete) nFiltrosActivos++;
      if (!soloMejor) nFiltrosActivos++;
      if (!soloDisp) nFiltrosActivos++;

      const badgeFiltros = document.getElementById("badge-filtros-activos");
      if (badgeFiltros) {
        if (nFiltrosActivos > 0) {
          badgeFiltros.textContent = String(nFiltrosActivos);
          badgeFiltros.classList.remove("hidden");
        } else {
          badgeFiltros.classList.add("hidden");
        }
      }

      // Actualizar estado visual y disponibilidad del toggle según la tienda seleccionada
      if (chkMejor) {
        if (tienda !== "Todas") {
          chkMejor.disabled = true;
          chkMejor.parentElement.classList.add("opacity-50", "cursor-not-allowed");
          chkMejor.parentElement.classList.remove("hover:bg-[#EFE8DC]", "cursor-pointer");
          chkMejor.parentElement.title = "Filtro activo solo al ver Todas las Tiendas";
        } else {
          chkMejor.disabled = false;
          chkMejor.parentElement.classList.remove("opacity-50", "cursor-not-allowed");
          chkMejor.parentElement.classList.add("hover:bg-[#EFE8DC]", "cursor-pointer");
          chkMejor.parentElement.title = "Mostrar únicamente la opción más barata por cada producto (oculta ofertas repetidas de tiendas más caras)";
        }
      }

      const busqTokens = busq ? normalizarTextoBusqueda(busq).split(" ").filter(Boolean) : [];
      datosFiltrados = DATOS_COMPLETOS.filter(item => {
        let matchBusq = true;
        if (busqTokens.length > 0) {
          const itemTokens = normalizarTextoBusqueda(`${item.producto} ${item.marca}`).split(" ").filter(Boolean);
          matchBusq = busqTokens.every(tok => tokenCoincide(tok, itemTokens));
        }
        const matchMacro = (macroCat === 'Todas') || (item.categoria === macroCat);
        const matchSub = (subCat === 'Todas' || subCat === 'Todos_Macro') || (item.categoria_comparable === subCat);
        const matchTienda = (tienda === 'Todas') || (item.tienda === tienda);
        const matchDesc = !soloDesc || (item.ahorro_verificable > 0);
        const matchMinHist = !soloMinHist || (item.semaforo_historico === 'minimo_historico');
        const matchPaquete = !soloPaquete || esProductoPaquete(item);
        const matchDisp = !soloDisp || (item.disponibilidad !== 'agotado');
        return matchBusq && matchMacro && matchSub && matchTienda && matchDesc && matchMinHist && matchPaquete && matchDisp;
      });


      // Si está en 'Todas las Tiendas' y el filtro está activo, mostrar únicamente la mejor oferta por producto
      if (tienda === "Todas" && soloMejor) {
        const clavesVistas = new Set();
        datosFiltrados = datosFiltrados.filter(item => {
          if (!item.es_precio_mas_bajo) return false;
          const k = item.clave_comparativa || (item.producto + "_" + item.ml);
          if (clavesVistas.has(k)) return false;
          clavesVistas.add(k);
          return true;
        });
      }

      datosFiltrados.sort((a, b) => {
        let vA = a[columnaOrden] || 0;
        let vB = b[columnaOrden] || 0;
        return ordenAsc ? vA - vB : vB - vA;
      });

      paginaActual = 1;
      renderizarTabla();
      renderizarGraficoTop10();
      document.getElementById("contador-filtrados").innerText = `${datosFiltrados.length} botellas verificadas`;
      const tituloG = (subCat !== 'Todas' && subCat !== 'Todos_Macro') ? subCat : (macroCat !== 'Todas' ? macroCat : 'Catálogo General');
      document.getElementById("chart-titulo").innerText = `Top 10 Rendimiento $/Litro: ${tituloG}`;

      const elKpiVal = document.getElementById("kpi-mejor-litro-valor");
      const elKpiDet = document.getElementById("kpi-mejor-litro-detalle");
      if (elKpiVal && elKpiDet && datosFiltrados.length > 0) {
        const candidatosDest = datosFiltrados.filter(d => d.categoria !== 'Vino');
        const poolKpi = candidatosDest.length > 0 ? candidatosDest : datosFiltrados;
        const mejor = [...poolKpi].sort((a, b) => a.precio_por_litro - b.precio_por_litro)[0];
        elKpiVal.innerText = `$${mejor.precio_por_litro.toFixed(2)}`;
        elKpiDet.innerText = `${nombreSinCategoria(mejor)} · ${mejor.tienda}`;
      }
    }

    const CLASE_ORDEN_BASE = "px-3 py-1.5 rounded font-mono font-semibold text-xs transition-colors cursor-pointer min-h-[34px]";
    const CLASE_ORDEN_ACTIVO = "bg-[#8c5332] text-white border border-[#703c1d] shadow-xs";
    const CLASE_ORDEN_INACTIVO = "bg-surface-container-lowest border border-outline-variant text-on-surface hover:bg-surface-container-high";

    function actualizarEstadoOrden() {
      document.querySelectorAll("[data-orden]").forEach(btn => {
        const activo = btn.dataset.orden === columnaOrden;
        btn.className = `${CLASE_ORDEN_BASE} ${activo ? CLASE_ORDEN_ACTIVO : CLASE_ORDEN_INACTIVO}`;
        const f = btn.querySelector(".orden-flecha");
        if (f) f.textContent = activo ? (ordenAsc ? "↑" : "↓") : "";
      });

      document.querySelectorAll("[data-orden-header]").forEach(th => {
        const activo = th.dataset.ordenHeader === columnaOrden;
        th.setAttribute("aria-sort", activo ? (ordenAsc ? "ascending" : "descending") : "none");
        const f = th.querySelector(".orden-flecha");
        if (f) f.textContent = activo ? (ordenAsc ? "↑" : "↓") : "";
        if (activo) {
          th.classList.add("text-primary", "font-bold");
        } else {
          th.classList.remove("text-primary", "font-bold");
        }
      });
    }

    function ordenarPor(col) {
      if (columnaOrden === col) ordenAsc = !ordenAsc;
      else { columnaOrden = col; ordenAsc = true; }
      aplicarFiltros();
      actualizarEstadoOrden();
    }

    const PREFIJOS_CATEGORIA = [
      "licor de whisky", "licor de wisky", "tequila", "mezcal",
      "whisky", "whiskey", "vino", "licor", "ron", "cerveza",
      "brandy", "vodka", "ginebra"
    ];

    function nombreSinCategoria(item) {
      let nombre = (item.producto || "").trim();
      const lower = nombre.toLowerCase();
      for (const pref of PREFIJOS_CATEGORIA) {
        if (lower.startsWith(pref)) {
          nombre = nombre.slice(pref.length).trim();
          break;
        }
      }
      return nombre || item.producto || "";
    }

    function getBadgeSemaforoHistorico(item, incluirEstable = false) {
      if (!item || !item.semaforo_historico) return "";
      const sem = item.semaforo_historico;
      const minHist = Number(item.precio_min_historico || item.precio_promo || 0);
      const maxHist = Number(item.precio_max_historico || item.precio_promo || 0);
      const regMin = Number(item.precio_reg_min_historico || item.precio_regular || 0);

      if (sem === "minimo_historico") {
        const tooltip = `Mejor precio registrado para esta botella en ${esc(item.tienda)} (máx. histórico: $${maxHist.toFixed(2)})`;
        return `<span class="badge bg-[#eaf4ec] text-[#24592a] border border-[#c5dfc9] text-[10px] font-semibold" title="${tooltip}">🟢 Mín. histórico</span>`;
      }
      if (sem === "descuento_inflado") {
        const tooltip = `Alerta: el precio regular reportado ($${Number(item.precio_regular || 0).toFixed(2)}) subió frente al regular histórico de $${regMin.toFixed(2)} en ${esc(item.tienda)}`;
        return `<span class="badge bg-[#fbeae8] text-[#ba1a1a] border border-[#ffdad6] text-[10px] font-semibold" title="${tooltip}">🔴 Desc. inflado</span>`;
      }
      if (sem === "subio_vs_minimo") {
        const diff = Math.max(1, Math.round(Number(item.precio_promo || 0) - minHist));
        const tooltip = `Estuvo a $${minHist.toFixed(2)} en capturas previas de ${esc(item.tienda)}`;
        return `<span class="badge bg-[#fef3eb] text-[#8c5332] border border-[#f3ddce] text-[10px] font-medium" title="${tooltip}">🟡 +$${diff} vs mín. hist.</span>`;
      }
      if (incluirEstable && sem === "estable") {
        const tooltip = `Sin variación en capturas históricas de ${esc(item.tienda)} ($${minHist.toFixed(2)})`;
        return `<span class="badge bg-surface-container text-on-surface-variant border border-outline-variant/80 text-[10px]" title="${tooltip}">⚪ Precio estable</span>`;
      }
      return "";
    }

    function renderizarTabla() {
      const tbody = document.getElementById("tabla-productos-body");
      const contMovil = document.getElementById("lista-productos-movil");
      if (tbody) tbody.innerHTML = "";
      if (contMovil) contMovil.innerHTML = "";

      const inicio = (paginaActual - 1) * itemsPorPagina;
      const fin = Math.min(inicio + itemsPorPagina, datosFiltrados.length);
      const paginaItems = datosFiltrados.slice(inicio, fin);

      if (paginaItems.length === 0) {
        const emptyStateHtml = `
          <div class="p-8 text-center space-y-3 max-w-md mx-auto">
            <span class="material-symbols-outlined text-3xl text-outline">search_off</span>
            <p class="font-headline font-bold text-base text-on-surface">Sin coincidencias con los filtros actuales</p>
            <p class="font-mono text-xs text-on-surface-variant leading-relaxed">
              Prueba ampliar la categoría, limpiar el texto de búsqueda o desactivar los filtros de "Solo ofertas" / "Solo paquetes".
            </p>
            <button type="button" onclick="restablecerFiltros()"
                    class="mt-1 px-4 py-2 rounded md3-btn-filled font-mono text-xs font-semibold inline-flex items-center gap-1.5 cursor-pointer">
              <span class="material-symbols-outlined text-[16px]">restart_alt</span>
              <span>Restablecer todos los filtros</span>
            </button>
          </div>
        `;
        if (tbody) {
          tbody.innerHTML = `<tr><td colspan="8">${emptyStateHtml}</td></tr>`;
        }
        if (contMovil) {
          contMovil.innerHTML = emptyStateHtml;
        }
        return;
      }

      let movilHtml = "";

      paginaItems.forEach(item => {
        const ahorroBadge = item.ahorro_verificable > 0
          ? `<span class="badge bg-[#eaf4ec] text-[#24592a] border border-[#c5dfc9]">-$${item.ahorro_verificable.toFixed(2)} (${item.porcentaje_ahorro}%)</span>`
          : `<span class="text-outline font-mono text-[11px]">Precio regular</span>`;

        const tiendaBadge = getBadgeTienda(item.tienda, false);
        const tiendaBadgeCorto = getBadgeTienda(item.tienda, true);
        const originalIndex = DATOS_COMPLETOS.indexOf(item);
        const semaforoBadge = getBadgeSemaforoHistorico(item, false);
        const semaforoBadgeDesktop = semaforoBadge ? `<div class="mt-1">${semaforoBadge}</div>` : "";

        // Capa 0: Badge de frescura honesta
        let staleBadgeDesktop = "";
        let staleBadgeMovil = "";
        if (item.es_stale) {
          const dias = Math.round(Number(item.dias_desde_actualizacion || 0));
          const txtDias = dias > 0 ? `Verificado hace ${dias}d` : "No verificado recientemente";
          staleBadgeDesktop = `<div class="mt-1"><span class="badge bg-amber-50 text-amber-800 border border-amber-300 text-[10px] font-semibold" title="Precio capturado previamente (${esc(item.fecha_consulta || 'antiguo')}). Requiere confirmación en tienda física.">⏳ ${txtDias}</span></div>`;
          staleBadgeMovil = `<span class="badge bg-amber-50 text-amber-800 border border-amber-300 text-[10px] font-semibold" title="Precio capturado previamente.">⏳ ${txtDias}</span>`;
        }


        let crossBadgeDesktop = "";
        let crossBadgeMovil = "";
        if (item.es_comparable_cross_tienda) {
          if (item.es_precio_mas_bajo) {
            crossBadgeDesktop = `
              <div class="mt-1">
                <button type="button" onclick="toggleModalCrossTienda(${originalIndex})" class="btn-cross-badge bg-[#eaf4ec] text-[#24592a] border border-[#c5dfc9] hover:bg-[#d5ebd8] cursor-pointer" title="Ver comparativa de precios en ${item.num_tiendas_cross} tiendas">
                  <span>Mejor precio de ${item.num_tiendas_cross} tiendas</span>
                  <span class="text-[9px] underline font-normal">Comparar →</span>
                </button>
              </div>
            `;
            crossBadgeMovil = `
              <div class="pt-0.5">
                <button type="button" onclick="toggleModalCrossTienda(${originalIndex})" class="btn-cross-badge bg-[#eaf4ec] text-[#24592a] border border-[#c5dfc9] active:bg-[#d5ebd8] cursor-pointer w-full justify-between" title="Ver comparativa de precios en ${item.num_tiendas_cross} tiendas">
                  <span>Mejor precio de ${item.num_tiendas_cross} tiendas</span>
                  <span class="text-[10px] underline font-normal">Comparar →</span>
                </button>
              </div>
            `;
          } else {
            crossBadgeDesktop = `
              <div class="mt-1">
                <button type="button" onclick="toggleModalCrossTienda(${originalIndex})" class="btn-cross-badge bg-error-container text-on-error-container border border-[#e0a8a1] hover:bg-[#f9c6c0] cursor-pointer" title="Ver comparativa de precios en ${item.num_tiendas_cross} tiendas">
                  <span>Más barato en ${esc(item.tienda_mas_barata)} ($${item.precio_minimo_cross.toFixed(2)})</span>
                  <span class="text-[9px] underline font-bold">Ahorra $${item.diferencia_vs_minimo.toFixed(2)} →</span>
                </button>
              </div>
            `;
            crossBadgeMovil = `
              <div class="pt-0.5">
                <button type="button" onclick="toggleModalCrossTienda(${originalIndex})" class="btn-cross-badge bg-error-container text-on-error-container border border-[#e0a8a1] active:bg-[#f9c6c0] cursor-pointer w-full justify-between" title="Ver comparativa de precios en ${item.num_tiendas_cross} tiendas">
                  <span>Más barato en ${esc(item.tienda_mas_barata)} ($${item.precio_minimo_cross.toFixed(2)})</span>
                  <span class="text-[10px] underline font-bold">Ahorra $${item.diferencia_vs_minimo.toFixed(2)} →</span>
                </button>
              </div>
            `;
          }
        }

        let paqueteBadgeDesktop = "";
        let paqueteBadgeMovil = "";
        if (esProductoPaquete(item)) {
          const textoPaq = (item.condiciones && item.condiciones.includes("\u{1F381}"))
            ? item.condiciones.replace("\u{1F381}", "").trim()
            : "Paquete / Combo";
          paqueteBadgeDesktop = `
            <div class="mt-1">
              <span class="badge bg-secondary-container text-on-secondary-fixed border border-outline-variant/80" title="Presentación en paquete o con obsequios incluidos">
                <span>${esc(textoPaq)}</span>
              </span>
            </div>
          `;
          paqueteBadgeMovil = `
            <div>
              <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded text-[10px] font-mono font-bold bg-secondary-container text-on-secondary-fixed border border-outline-variant/80 leading-tight" title="Presentación en paquete o con obsequios incluidos">
                <span>${esc(textoPaq)}</span>
              </span>
            </div>
          `;
        }

        let stockBadgeDesktop = "";
        let stockBadgeMovil = "";
        if (item.disponibilidad === "agotado") {
          stockBadgeDesktop = `<div class="mt-1"><span class="badge bg-[#fbeae8] text-[#ba1a1a] border border-[#ffdad6] font-semibold" title="Sin existencias reportadas">Agotado</span></div>`;
          stockBadgeMovil = `<span class="badge bg-[#fbeae8] text-[#ba1a1a] border border-[#ffdad6] text-[10px] font-semibold">Agotado</span>`;
        } else if (item.stock_unidades !== null && item.stock_unidades !== undefined && item.stock_unidades !== "" && Number(item.stock_unidades) > 0 && Number(item.stock_unidades) <= 5) {
          stockBadgeDesktop = `<div class="mt-1"><span class="badge bg-[#fef3eb] text-[#8c5332] border border-[#f3ddce] font-semibold" title="${item.stock_unidades} unidades en inventario">Últimas ${item.stock_unidades} pzas</span></div>`;
          stockBadgeMovil = `<span class="badge bg-[#fef3eb] text-[#8c5332] border border-[#f3ddce] text-[10px] font-semibold">Últimas ${item.stock_unidades} pzas</span>`;
        } else if (item.stock_unidades !== null && item.stock_unidades !== undefined && item.stock_unidades !== "" && Number(item.stock_unidades) > 5) {
          stockBadgeDesktop = `<div class="mt-1"><span class="badge bg-[#eaf4ec] text-[#24592a] border border-[#c5dfc9] font-medium" title="${item.stock_unidades} unidades disponibles">Existencia: ${item.stock_unidades}</span></div>`;
          stockBadgeMovil = `<span class="badge bg-[#eaf4ec] text-[#24592a] border border-[#c5dfc9] text-[10px] font-medium">Existencia: ${item.stock_unidades}</span>`;
        }

        // 1. Fila Desktop (tr) — Stitch Archival Ledger Row
        if (tbody) {
          const tr = document.createElement("tr");
          tr.className = "ledger-row transition-colors";
          tr.innerHTML = `
            <td class="py-3.5 px-4 font-medium text-on-surface max-w-xs">
              <a href="${urlSegura(item.url)}" target="_blank" rel="noopener noreferrer"
                 class="hover:underline text-on-surface hover:text-primary inline-flex items-center gap-1 group font-semibold leading-snug"
                 title="Ver ${esc(item.producto)} en tienda oficial ${esc(item.tienda)}">
                <span class="line-clamp-2">${esc(nombreSinCategoria(item))}</span>
                <span class="text-[10px] text-outline group-hover:text-primary flex-shrink-0">↗</span>
              </a>
              ${paqueteBadgeDesktop}
              ${crossBadgeDesktop}
            </td>
            <td class="py-3.5 px-3 text-xs">
              <span class="badge bg-surface-container border border-outline-variant/70 text-on-surface-variant">${esc(item.categoria_comparable)}</span>
            </td>
            <td class="py-3.5 px-3 text-xs font-mono text-on-surface-variant text-right hidden md:table-cell whitespace-nowrap">${item.ml} mL</td>
            <td class="py-3.5 px-3 font-bold text-on-surface font-mono text-right whitespace-nowrap">$${item.precio_promo.toFixed(2)}</td>
            <td class="py-3.5 px-4 font-extrabold text-primary font-mono text-right bg-surface-container/60 border-x border-outline-variant/40 whitespace-nowrap">$${item.precio_por_litro.toFixed(2)}</td>
            <td class="py-3.5 px-3 hidden lg:table-cell whitespace-nowrap">${ahorroBadge}${semaforoBadgeDesktop}${stockBadgeDesktop}${staleBadgeDesktop}</td>
            <td class="py-3.5 px-3 whitespace-nowrap">${tiendaBadge}</td>
            <td class="py-3.5 px-4 text-right whitespace-nowrap">
              <button onclick="agregarDesdeTabla(${originalIndex})" class="px-3 py-1.5 text-xs md3-btn-tonal cursor-pointer whitespace-nowrap">
                + Carrito
              </button>
            </td>
          `;
          tbody.appendChild(tr);
        }

        // 2. Tarjeta Móvil (Mobile Card táctil sin desbordamiento)
        const ahorroBadgeMovil = item.ahorro_verificable > 0
          ? `<span class="badge bg-[#eaf4ec] text-[#24592a] border border-[#c5dfc9] text-[10px]">-$${item.ahorro_verificable.toFixed(2)} (${item.porcentaje_ahorro}%)</span>`
          : "";

        movilHtml += `
          <div class="p-3.5 space-y-2 hover:bg-surface-container-low transition-colors">
            <div class="flex items-center justify-between gap-1.5 flex-wrap">
              <div class="flex items-center gap-1.5 flex-wrap">
                ${tiendaBadgeCorto}
                ${stockBadgeMovil}
                ${staleBadgeMovil}
                <span class="badge bg-surface-container border border-outline-variant/70 text-on-surface-variant text-[10px]">${esc(item.categoria_comparable)}</span>
              </div>

              <span class="text-xs font-mono font-bold text-on-surface-variant">${item.ml} mL</span>
            </div>

            <div class="font-bold text-sm text-on-surface leading-snug">
              <a href="${urlSegura(item.url)}" target="_blank" rel="noopener noreferrer"
                 class="hover:underline hover:text-primary inline-flex items-center gap-1 group"
                 title="Ver ${esc(item.producto)} en tienda oficial ${esc(item.tienda)}">
                <span>${esc(nombreSinCategoria(item))}</span>
                <span class="text-xs text-outline group-hover:text-primary flex-shrink-0">↗</span>
              </a>
            </div>

            ${paqueteBadgeMovil}
            ${crossBadgeMovil}

            <div class="flex items-center justify-between pt-1.5 border-t border-outline-variant/50 mt-1">
              <div class="flex items-baseline gap-2 flex-wrap">
                <span class="font-extrabold text-base text-on-surface font-mono">$${item.precio_promo.toFixed(2)}</span>
                <span class="text-xs font-extrabold text-primary font-mono">$${item.precio_por_litro.toFixed(2)} <span class="font-normal text-[10px] text-on-surface-variant">/ L</span></span>
                ${ahorroBadgeMovil}
                ${semaforoBadge}
              </div>
              <button onclick="agregarDesdeTabla(${originalIndex})" class="px-3.5 py-1.5 text-xs font-bold md3-btn-tonal cursor-pointer whitespace-nowrap min-h-[36px] flex items-center gap-1 shadow-xs">
                <span>+</span> Carrito
              </button>
            </div>
          </div>
        `;
      });

      if (contMovil) contMovil.innerHTML = movilHtml;

      document.getElementById("info-paginacion").innerText = `Mostrando ${inicio + 1} - ${fin} de ${datosFiltrados.length}`;
      document.getElementById("btn-prev").disabled = paginaActual === 1;
      document.getElementById("btn-next").disabled = fin >= datosFiltrados.length;
    }

    function cambiarPagina(delta) {
      paginaActual += delta;
      renderizarTabla();
    }

    function renderizarGraficoTop10() {
      const container = document.getElementById("chart-container");
      const top10 = datosFiltrados.slice(0, 10);
      if (top10.length === 0) {
        container.innerHTML = "<div class='text-xs font-mono text-on-surface-variant p-4'>Sin datos para graficar</div>";
        return;
      }

      const maxLitro = Math.max(...top10.map(d => d.precio_por_litro));

      let svgHtml = `<div class="space-y-3 py-1">`;
      top10.forEach((item, idx) => {
        const anchoPorcentaje = Math.max(15, (item.precio_por_litro / maxLitro) * 100);
        const colorBarra = idx === 0
          ? "bg-[#2d6a36]"
          : (idx < 3 ? "bg-[#703c1d]" : "bg-[#775836]/80");

        svgHtml += `
          <div class="space-y-1">
            <div class="flex items-center justify-between gap-2 text-xs">
              <span class="font-semibold text-on-surface truncate flex-1 min-w-0 font-mono text-[11px] sm:text-xs"><strong class="text-primary">#0${idx + 1}</strong> ${esc(item.producto)} <span class="text-on-surface-variant font-normal">(${esc(item.tienda)})</span></span>
              <span class="font-bold font-mono text-primary flex-shrink-0 whitespace-nowrap">$${item.precio_por_litro.toFixed(2)} / L</span>
            </div>
            <div class="w-full bg-surface-container-highest h-2.5 rounded overflow-hidden border border-outline-variant/40">
              <div class="${colorBarra} h-full rounded transition-all duration-500" style="width: ${anchoPorcentaje}%"></div>
            </div>
          </div>
        `;
      });
      svgHtml += `</div>`;
      container.innerHTML = svgHtml;
    }
