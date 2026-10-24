    // =========================================================================
    // FUNCIONALIDADES CROSS-TIENDA (H8: ARBITRAJE, MODAL Y OPTIMIZADOR)
    // =========================================================================
    function toggleModalCrossTienda(originalIndex) {
      const item = DATOS_COMPLETOS[originalIndex];
      if (!item || !item.es_comparable_cross_tienda) return;

      const modal = document.getElementById("modal-cross-tienda");
      if (!modal) return;

      const ofertas = DATOS_COMPLETOS
        .map((p, idx) => ({ p, idx }))
        .filter(x => x.p.clave_comparativa === item.clave_comparativa)
        .sort((a, b) => a.p.precio_por_litro - b.p.precio_por_litro);

      const mlsDistintos = [...new Set(ofertas.map(x => x.p.ml))];
      let tituloModal = item.producto;
      if (mlsDistintos.length > 1) {
        tituloModal += ` (${mlsDistintos.join(" / ")} ml)`;
      } else {
        const yaTieneMl = new RegExp(`\\b${item.ml}\\s*ml\\b`, 'i').test(tituloModal);
        if (!yaTieneMl) {
          tituloModal += ` (${item.ml} ml)`;
        }
      }

      document.getElementById("modal-cross-badge-cat").innerText = item.categoria_comparable;
      document.getElementById("modal-cross-titulo").innerText = tituloModal;
      document.getElementById("modal-cross-subtitulo").innerText =
        `Disponible en ${item.num_tiendas_cross} tiendas · Ahorro máximo entre tiendas: $${item.ahorro_maximo_cross.toFixed(2)} MXN`;

      const mejorOferta = ofertas[0].p;
      const minPorLitro = mejorOferta.precio_por_litro;
      const cont = document.getElementById("modal-cross-contenido");
      let html = "";

      ofertas.forEach(({ p, idx }, rank) => {
        const esMinimo = rank === 0;
        const difVsMin = (p.ml === mejorOferta.ml)
          ? (p.precio_promo - mejorOferta.precio_promo)
          : ((p.precio_por_litro - minPorLitro) * (p.ml / 1000.0));
        const badgeTienda = getBadgeTienda(p.tienda, true);

        let bannerAhorro = "";
        if (esMinimo) {
          bannerAhorro = `<span class="badge bg-[#D3E8DC] text-[#0B2016] border border-[#B7D6C5] text-[10px] font-bold whitespace-normal sm:whitespace-nowrap leading-tight text-left">Mejor Precio (Ahorras hasta $${item.ahorro_maximo_cross.toFixed(2)})</span>`;
        } else {
          bannerAhorro = `<span class="text-[11px] text-[#9B1C1C] font-semibold">+$${difVsMin.toFixed(2)} vs ${mejorOferta.tienda}</span>`;
        }

        html += `
          <div class="p-3.5 rounded-xl border ${esMinimo ? 'bg-[#F4F9F6] border-[#B7D6C5] ring-1 ring-[#486355]/25' : 'bg-white border-[#DFD5C7]'} flex flex-col sm:flex-row sm:items-center justify-between gap-3 transition-all">
            <div class="space-y-1.5 min-w-0 flex-1">
              <div class="flex items-center gap-2 flex-wrap">
                ${badgeTienda}
                ${bannerAhorro}
              </div>
              <div class="font-bold text-sm text-[#1F1B16] leading-snug break-words">${p.producto}</div>
              <div class="text-xs text-[#574A3D] flex flex-wrap items-center gap-x-1.5 gap-y-0.5">
                <span>Precio: <strong class="text-sm font-mono text-[#784516] font-extrabold">$${p.precio_promo.toFixed(2)}</strong></span>
                <span>·</span>
                <span class="font-mono text-[#486355] font-semibold">$${p.precio_por_litro.toFixed(2)} / L</span>
                <span>·</span>
                <span class="text-[11px] text-[#786C5E] font-medium">${p.ml} ml</span>
                ${p.ahorro_verificable > 0 ? `<span class="ml-1 text-[#047857] text-[11px] font-medium">(${p.condiciones})</span>` : ''}
              </div>
            </div>

            <div class="flex items-center gap-2 flex-wrap sm:flex-nowrap justify-end pt-2 sm:pt-0 border-t sm:border-t-0 border-[#DFD5C7]/60 w-full sm:w-auto flex-shrink-0">
              <a href="${p.url}" target="_blank" rel="noopener noreferrer" class="flex-1 sm:flex-initial text-center px-3 py-1.5 md3-btn-tonal text-xs inline-flex items-center justify-center gap-1" title="Ver en ${p.tienda}">
                <span>Ver en Tienda</span> <span>↗</span>
              </a>
              <button onclick="modificarCantidad(${idx}, 1); cerrarModalCrossTienda(); mostrarToast('Añadido al carrito: ${p.producto.replace(/'/g, "\\'")} (${p.tienda})');" class="flex-1 sm:flex-initial px-3 py-1.5 md3-btn-filled text-xs cursor-pointer text-center">
                + Carrito
              </button>
            </div>
          </div>
        `;
      });

      cont.innerHTML = html;
      modal.classList.remove("hidden");
    }

    function cerrarModalCrossTienda() {
      const modal = document.getElementById("modal-cross-tienda");
      if (modal) modal.classList.add("hidden");
    }

    function inicializarSelectorCrossTiendaVersus() {
      const sel = document.getElementById("select-cross-tienda-duelo");
      if (!sel) return;

      const grupos = {};
      DATOS_COMPLETOS.forEach((item, idx) => {
        if (!item.es_comparable_cross_tienda) return;
        const clave = item.clave_comparativa;
        if (!grupos[clave]) {
          grupos[clave] = {
            clave,
            producto: item.producto,
            categoria: item.categoria_comparable,
            ml: item.ml,
            ahorro_max: item.ahorro_maximo_cross,
            tiendas: []
          };
        }
        grupos[clave].tiendas.push({ item, idx });
      });

      const lista = Object.values(grupos).sort((a, b) => b.ahorro_max - a.ahorro_max);
      const badgeTotal = document.getElementById("badge-total-cross");
      if (badgeTotal) badgeTotal.innerText = `${lista.length} botellas`;

      sel.innerHTML = `<option value="">Elige una botella para ver arbitraje entre tiendas (${lista.length} disponibles)...</option>`;
      lista.forEach(g => {
        const prodCorto = g.producto.length > 40 ? g.producto.slice(0, 39) + "…" : g.producto;
        const opt = document.createElement("option");
        opt.value = g.clave;
        const mls = [...new Set(g.tiendas.map(t => t.item.ml))];
        const mlStr = mls.length > 1 ? mls.join("/") + "ml" : `${g.ml}ml`;
        opt.innerText = `${prodCorto} (${mlStr}) — Ahorra hasta $${g.ahorro_max.toFixed(2)}`;
        sel.appendChild(opt);
      });
    }

    function cargarDueloCrossTienda(clave) {
      if (!clave) return;
      const items = DATOS_COMPLETOS
        .map((item, idx) => ({ item, idx }))
        .filter(x => x.item.clave_comparativa === clave)
        .sort((a, b) => a.item.precio_por_litro - b.item.precio_por_litro);

      if (items.length < 2) return;

      const idxMin = items[0].idx;
      const idxMax = items[items.length - 1].idx;

      document.getElementById("select-versus-macro").value = "Todas";
      actualizarSubtiposVersus();
      document.getElementById("select-versus-categoria-filtro").value = "Todas";
      filtrarSelectoresVersusPorCategoria();

      document.getElementById("select-versus-a").value = idxMin;
      document.getElementById("select-versus-b").value = idxMax;
      renderizarVersus();

      mostrarToast(`Duelo cross-tienda: ${items[0].item.tienda} ($${items[0].item.precio_promo.toFixed(2)}) vs ${items[items.length - 1].item.tienda} ($${items[items.length - 1].item.precio_promo.toFixed(2)})`);
    }

    function cambiarTiendaCarrito(idx) {
      const item = DATOS_COMPLETOS[idx];
      if (!item || !item.es_comparable_cross_tienda || item.es_precio_mas_bajo) return;

      const altIdx = DATOS_COMPLETOS.findIndex(d =>
        d.clave_comparativa === item.clave_comparativa &&
        d.tienda === item.tienda_mas_barata
      );

      if (altIdx !== -1) {
        const cant = canastaPersonalizada[idx] || 1;
        const ahorro = (item.diferencia_vs_minimo * cant).toFixed(2);
        delete canastaPersonalizada[idx];
        canastaPersonalizada[altIdx] = (canastaPersonalizada[altIdx] || 0) + cant;
        guardarCanastaEnStorage();
        renderizarConstructorCanasta();
        mostrarToast(`Cambiado a ${item.tienda_mas_barata}. ¡Ahorraste $${ahorro} MXN!`);
      }
    }

    function optimizarTodoAlMejorPrecio() {
      let ahorroTotal = 0;
      let cambios = 0;
      const indices = Object.keys(canastaPersonalizada).map(Number);

      indices.forEach(idx => {
        const item = DATOS_COMPLETOS[idx];
        const cant = canastaPersonalizada[idx];
        if (!item || cant <= 0) return;

        if (item.es_comparable_cross_tienda && !item.es_precio_mas_bajo && item.diferencia_vs_minimo > 0) {
          const altIdx = DATOS_COMPLETOS.findIndex(d =>
            d.clave_comparativa === item.clave_comparativa &&
            d.tienda === item.tienda_mas_barata
          );
          if (altIdx !== -1) {
            ahorroTotal += (item.diferencia_vs_minimo * cant);
            delete canastaPersonalizada[idx];
            canastaPersonalizada[altIdx] = (canastaPersonalizada[altIdx] || 0) + cant;
            cambios++;
          }
        }
      });

      if (cambios > 0) {
        guardarCanastaEnStorage();
        renderizarConstructorCanasta();
        mostrarToast(`¡Canasta optimizada! Ahorraste $${ahorroTotal.toFixed(2)} MXN en ${cambios} botella(s).`);
      } else {
        mostrarToast(`Tu canasta ya tiene los mejores precios disponibles.`);
      }
    }

    function actualizarSubtiposCatalogo() {
      const macro = document.getElementById("filtro-macro-categoria").value;
      const selectSub = document.getElementById("filtro-categoria");
      const labelSub = document.getElementById("label-filtro-categoria");

      if (macro === "Todas") {
        selectSub.disabled = true;
        selectSub.classList.add("opacity-60", "bg-[#EFE8DC]/50", "cursor-not-allowed");
        selectSub.classList.remove("cursor-pointer", "bg-white");
        selectSub.innerHTML = '<option value="Todas" selected>Selecciona primero una categoría...</option>';
        if (labelSub) {
          labelSub.classList.remove("text-[#486355]");
          labelSub.classList.add("text-[#8A7B6B]");
        }
      } else {
        selectSub.disabled = false;
        selectSub.classList.remove("opacity-60", "bg-[#EFE8DC]/50", "cursor-not-allowed");
        selectSub.classList.add("cursor-pointer", "bg-white");
        if (labelSub) {
          labelSub.classList.remove("text-[#8A7B6B]");
          labelSub.classList.add("text-[#486355]");
        }

        const opciones = SUBTIPOS_POR_MACRO[macro] || [];
        selectSub.innerHTML = "";
        opciones.forEach((op, i) => {
          const opt = document.createElement("option");
          opt.value = op.value;
          opt.innerText = op.label;
          if (i === 0) opt.selected = true;
          selectSub.appendChild(opt);
        });
      }

      aplicarFiltros();
    }

    function actualizarSubtiposVersus() {
      const macro = document.getElementById("select-versus-macro").value;
      const selectSub = document.getElementById("select-versus-categoria-filtro");

      selectSub.innerHTML = "";
      if (macro === "Todas") {
        selectSub.disabled = true;
        selectSub.classList.add("opacity-60", "bg-[#EFE8DC]/50", "cursor-not-allowed");
        selectSub.classList.remove("cursor-pointer", "bg-white");
        const optLibre = document.createElement("option");
        optLibre.value = "Todas";
        optLibre.innerText = "Comparativa libre (sin filtro de tipo)";
        selectSub.appendChild(optLibre);
      } else {
        selectSub.disabled = false;
        selectSub.classList.remove("opacity-60", "bg-[#EFE8DC]/50", "cursor-not-allowed");
        selectSub.classList.add("cursor-pointer", "bg-white");
        const opciones = (SUBTIPOS_POR_MACRO[macro] || []).filter(o => o.value !== "Todos_Macro");
        opciones.forEach((op, i) => {
          const opt = document.createElement("option");
          opt.value = op.value;
          opt.innerText = op.label;
          if (i === 0) opt.selected = true;
          selectSub.appendChild(opt);
        });
      }

      filtrarSelectoresVersusPorCategoria();
    }
