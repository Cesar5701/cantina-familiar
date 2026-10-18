    function filtrarSelectoresVersusPorCategoria() {
      const filtroCat = document.getElementById("select-versus-categoria-filtro").value;
      const selA = document.getElementById("select-versus-a");
      const selB = document.getElementById("select-versus-b");

      let items = [];
      let catEfectiva = filtroCat;

      if (filtroCat === "Todas") {
        items = DATOS_COMPLETOS.map((item, idx) => ({ item, idx }));
      } else {
        items = DATOS_COMPLETOS
          .map((item, idx) => ({ item, idx }))
          .filter(x => x.item.categoria_comparable === filtroCat);
      }

      selA.innerHTML = "";
      selB.innerHTML = "";

      items.forEach(({ item, idx }) => {
        const prodNom = item.producto.length > 48 ? item.producto.slice(0, 47).trim() + "…" : item.producto;
        const label = `${prodNom} ($${item.precio_promo.toFixed(2)} | $${item.precio_por_litro.toFixed(2)}/L) — ${item.tienda}`;
        const optA = new Option(label, idx);
        optA.title = item.producto;
        const optB = new Option(label, idx);
        optB.title = item.producto;
        selA.add(optA);
        selB.add(optB);
      });

      if (items.length > 0) {
        selA.value = items[0].idx;
        selB.value = items.length > 1 ? items[1].idx : items[0].idx;
      }

      renderizarSugerenciasVersus(catEfectiva);
      renderizarVersus();
    }

    function renderizarSugerenciasVersus(cat) {
      const cont = document.getElementById("versus-sugerencias-container");
      const info = document.getElementById("versus-sugerencias-info");
      cont.innerHTML = "";

      let lista = SUGERENCIAS_POR_CATEGORIA[cat];
      if (!lista || lista.length === 0) {
        lista = SUGERENCIAS_POR_CATEGORIA["Todas"] || [];
      }

      info.innerText = `${lista.length} duelos sugeridos en ${cat}`;

      lista.forEach(duelo => {
        const btn = document.createElement("button");
        btn.className = "w-full sm:w-auto text-left whitespace-normal break-words rounded-xl px-3.5 py-2 text-xs font-semibold border border-[#E5C8A3] bg-[#F8E2C8] text-[#2B1500] hover:bg-[#F2D5B3] transition-all cursor-pointer shadow-xs leading-snug";
        btn.innerText = duelo.label;
        btn.onclick = () => cargarDueloDirecto(duelo.a, duelo.b, duelo.storeA, duelo.storeB);
        cont.appendChild(btn);
      });
    }

    function cargarDueloDirecto(kwA, kwB, storeA, storeB) {
      const idxA = DATOS_COMPLETOS.findIndex(d => {
        const matchP = d.producto.toLowerCase().includes(kwA.toLowerCase());
        const matchS = !storeA || d.tienda.toLowerCase().includes(storeA.toLowerCase());
        return matchP && matchS;
      });
      const idxB = DATOS_COMPLETOS.findIndex(d => {
        const matchP = d.producto.toLowerCase().includes(kwB.toLowerCase());
        const matchS = !storeB || d.tienda.toLowerCase().includes(storeB.toLowerCase());
        return matchP && matchS;
      });

      if (idxA !== -1 && idxB !== -1) {
        const prodA = DATOS_COMPLETOS[idxA];
        const prodB = DATOS_COMPLETOS[idxB];
        const macroSelect = document.getElementById("select-versus-macro");
        const filtroSelect = document.getElementById("select-versus-categoria-filtro");

        if (prodA.categoria_comparable === prodB.categoria_comparable) {
          macroSelect.value = prodA.categoria;
          actualizarSubtiposVersus();
          filtroSelect.value = prodA.categoria_comparable;
          filtrarSelectoresVersusPorCategoria();
        } else {
          macroSelect.value = "Todas";
          actualizarSubtiposVersus();
        }

        document.getElementById("select-versus-a").value = idxA;
        document.getElementById("select-versus-b").value = idxB;
        renderizarVersus();
      }
    }

    function actualizarVersusManual() {
      renderizarVersus();
    }

    function getABV(p) {
      if (p.categoria_comparable.includes("Vino")) return "11.5% - 12.5% Alc. Vol.";
      if (p.categoria_comparable.includes("Whisky")) return "40.0% Alc. Vol.";
      if (p.categoria_comparable.includes("Honey")) return "35.0% Alc. Vol.";
      if (p.categoria_comparable.includes("Mezcal")) return "38.0% - 45.0% Alc. Vol.";
      if (p.categoria_comparable.includes("Tequila")) return "35.0% - 40.0% Alc. Vol.";
      return "40.0% Alc. Vol.";
    }

    function getMaduracionInfo(p) {
      const c = p.categoria_comparable;
      if (c.includes("Añejo Cristalino")) return "Añejado ≥12 meses en barrica de roble y filtrado selectivo con carbón activado.";
      if (c.includes("Añejo Tradicional")) return "Añejado ≥12 meses en roble blanco. Conserva su color ámbar natural y notas intensas de madera.";
      if (c.includes("Reposado Cristalino")) return "Reposado de 2 a 11 meses en barrica y clarificado para máxima suavidad en boca.";
      if (c.includes("Mezcal - Reposado")) return "Maduración de 2 a 11 meses en madera que suaviza el ahumado del agave.";
      if (c.includes("Mezcal - Añejo")) return "Maduración ≥12 meses en roble con notas profundas de cacao y frutos secos.";
      if (c.includes("Mezcal - Silvestre")) return "Agaves silvestres (Tobalá, Cupreata, Cuishe) de 8 a 15 años de maduración en monte.";
      if (c.includes("Whisky")) return "Blended Scotch madurado mínimo 3 años en barricas de roble escocés.";
      if (c.includes("Honey")) return "Licor de whiskey infusionado con miel natural de abeja.";
      if (c.includes("Vino")) return "Vino tinto frutal ideal para clericot o servicio directo en mesa.";
      return "Destilación artesanal certificada.";
    }

    function generarTipFamiliar(prodA, prodB, ahorroTotal, ahorroPersona, cantBotellas, nPers) {
      const catA = prodA.categoria_comparable;
      const catB = prodB.categoria_comparable;
      const textoCuota = COOPERADORES_TOTAL > 0
        ? `(<strong>$${ahorroPersona.toFixed(2)} MXN menos por persona</strong> entre ${nPers} cooperadores)`
        : `(ingresa el número de personas arriba para calcular el ahorro individual)`;

      if (catA.includes("Añejo Cristalino") && catB.includes("Añejo Cristalino")) {
        return `
          <div class="md3-surface-tonal p-4 text-xs space-y-1.5 text-[#1F1B16]">
            <div class="flex items-center gap-1.5 font-bold text-[#784516]">
              <span>💡</span> <span>Tip de Arbitraje en Añejo Cristalino:</span>
            </div>
            <p class="text-[#574A3D]">
              <strong>Maestro Dobel Diamante en Sam's Club ($574.93)</strong>, <strong>1800 Cristalino en Alianza ($600)</strong> y <strong>Don Julio 70 en Walmart ($699)</strong> lideran cada segmento. Elegir la opción de mejor precio en ${cantBotellas} botellas representa un ahorro directo de <strong class="text-[#1F1B16]">$${ahorroTotal.toFixed(2)} MXN</strong> ${textoCuota}.
            </p>
          </div>
        `;
      }

      if (catA.includes("Mezcal") && catB.includes("Mezcal")) {
        return `
          <div class="md3-surface-tonal p-4 text-xs space-y-1.5 text-[#1F1B16]">
            <div class="flex items-center gap-1.5 font-bold text-[#486355]">
              <span>🌵</span> <span>Tip de Arbitraje en Mezcal:</span>
            </div>
            <p class="text-[#574A3D]">
              La línea <strong>400 Conejos en Chedraui ($520 en Reposado, Tobalá y Cuishe)</strong> tiene un descuento de $130 por botella frente a Bodegas Alianza ($650), mientras que <strong>Amarás Reposado en Alianza ($503.30)</strong> es el campeón en relación suavidad-precio.
            </p>
          </div>
        `;
      }

      return `
        <div class="md3-surface-tonal p-4 text-xs text-[#574A3D]">
          <strong class="text-[#1F1B16]">Tip de Compra:</strong> Optar por la presentación de menor $/Litro dentro del mismo tipo de bebida ahorra <strong class="text-[#784516]">$${ahorroTotal.toFixed(2)} MXN</strong> en una compra de ${cantBotellas} unidades ${textoCuota}.
        </div>
      `;
    }

    function renderizarVersus() {
      const idxA = parseInt(document.getElementById("select-versus-a").value) || 0;
      const idxB = parseInt(document.getElementById("select-versus-b").value) || 0;

      const prodA = DATOS_COMPLETOS[idxA] || DATOS_COMPLETOS[0];
      const prodB = DATOS_COMPLETOS[idxB] || DATOS_COMPLETOS[1];

      const contTarjetas = document.getElementById("versus-tarjetas-container");
      const alertaCompat = document.getElementById("versus-alerta-compatibilidad");
      const impactoBox = document.getElementById("versus-impacto-familiar-box");
      const veredictoBox = document.getElementById("versus-veredicto-box");

      const compatible = prodA.categoria_comparable === prodB.categoria_comparable;

      if (!compatible) {
        alertaCompat.innerHTML = `
          <div class="bg-[#FAD9DF] border border-[#E5B3BC] rounded-2xl p-4 flex items-start gap-3 text-xs text-[#2C0811]">
            <span class="text-xl">⚠️</span>
            <div>
              <strong class="font-bold text-[#753B47]">Comparando Tipos de Bebida Distintos:</strong>
              <p class="mt-1">
                Estás enfrentando <strong>${prodA.categoria_comparable}</strong> contra <strong>${prodB.categoria_comparable}</strong>.
                Para una comparativa equivalente en tiempo de barrica, selecciona un tipo específico arriba.
              </p>
            </div>
          </div>
        `;
      } else {
        alertaCompat.innerHTML = `
          <div class="bg-[#D3E8DC] border border-[#B7D6C5] rounded-2xl p-3.5 flex items-center gap-2 text-xs text-[#0B2016]">
            <span>✅</span>
            <span><strong>Mismo Tipo de Bebida:</strong> Ambos contendientes pertenecen a <strong>${prodA.categoria_comparable}</strong>.</span>
          </div>
        `;
      }

      const esVinoA = prodA.categoria_comparable.includes("Vino");
      const esVinoB = prodB.categoria_comparable.includes("Vino");
      const dosisA = esVinoA ? 150 : 45;
      const dosisB = esVinoB ? 150 : 45;
      const labelDosisA = esVinoA ? "Copa (150 ml)" : "Trago (45 ml)";
      const labelDosisB = esVinoB ? "Copa (150 ml)" : "Trago (45 ml)";

      const costoTragoA = (prodA.precio_promo / prodA.ml) * dosisA;
      const costoTragoB = (prodB.precio_promo / prodB.ml) * dosisB;
      const tragosA = Math.floor(prodA.ml / dosisA);
      const tragosB = Math.floor(prodB.ml / dosisB);

      function generarTarjetaProd(p, colorBorder, letra, costoTrago, tragosTotales, labelDosis) {
        const ahorro = p.ahorro_verificable > 0
          ? `<span class="badge bg-[#D3E8DC] text-[#0B2016] border border-[#B7D6C5] whitespace-normal text-left">Ahorro: -$${p.ahorro_verificable.toFixed(2)} (${p.porcentaje_ahorro}%)</span>`
          : `<span class="text-xs text-[#8A7B6B]">Precio Regular</span>`;

        const tiendaBadge = getBadgeTienda(p.tienda, false);

        return `
          <div class="md3-card border-t-4 ${colorBorder} p-4 sm:p-5 space-y-4 min-w-0 overflow-hidden">
            <div class="flex flex-wrap justify-between items-start gap-2">
              <span class="badge bg-[#EFE8DC] border border-[#D6C8B8] font-bold text-xs text-[#1F1B16]">Contendiente ${letra}</span>
              <div class="flex flex-wrap gap-1.5 items-center">${tiendaBadge}${ahorro}</div>
            </div>

            <div class="min-w-0">
              <span class="text-xs font-mono text-[#784516] font-bold">${p.categoria_comparable}</span>
              <h4 class="text-base sm:text-lg font-bold font-display-md3 text-[#1F1B16] mt-0.5 leading-snug break-words">${p.producto}</h4>
              <p class="text-xs text-[#574A3D] break-words">${p.marca} · ${p.ml} ml · ${getABV(p)}</p>
            </div>

            <div class="grid grid-cols-2 gap-3 md3-surface-low p-3.5">
              <div>
                <span class="text-[11px] text-[#574A3D]">Precio Botella:</span>
                <div class="text-lg sm:text-xl font-bold font-mono text-[#1F1B16]">$${p.precio_promo.toFixed(2)}</div>
              </div>
              <div>
                <span class="text-[11px] text-[#574A3D]">Precio / Litro:</span>
                <div class="text-lg sm:text-xl font-bold font-mono text-[#784516]">$${p.precio_por_litro.toFixed(2)}</div>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-3 md3-surface-low p-3 text-xs">
              <div>
                <span class="text-[11px] text-[#574A3D]">Costo por ${labelDosis}:</span>
                <div class="text-sm sm:text-base font-bold font-mono text-[#486355] mt-0.5">$${costoTrago.toFixed(2)}</div>
              </div>
              <div>
                <span class="text-[11px] text-[#574A3D]">Rendimiento por Envase:</span>
                <div class="text-sm sm:text-base font-bold font-mono text-[#784516] mt-0.5">~${tragosTotales} ${p.categoria_comparable.includes("Vino") ? "copas" : "tragos"}</div>
              </div>
            </div>

            <div class="text-xs md3-surface-tonal p-3 text-[#574A3D] leading-relaxed break-words">
              <strong class="text-[#1F1B16]">Perfil de Barrica:</strong> ${getMaduracionInfo(p)}
            </div>

            <div class="pt-2 flex flex-col sm:flex-row justify-between items-stretch sm:items-center gap-2 text-xs border-t border-[#DFD5C7]">
              <a href="${p.url}" target="_blank" rel="noopener noreferrer" class="text-xs font-semibold text-[#784516] hover:underline text-center sm:text-left py-1">Ver en tienda en línea ↗</a>
              <button onclick="modificarCantidad(${DATOS_COMPLETOS.indexOf(p)}, 1); mostrarToast('🍾 Añadido al carrito: ${p.producto.replace(/'/g, "\\'")}');" class="w-full sm:w-auto px-4 py-2 md3-btn-filled text-xs cursor-pointer text-center">
                + Añadir al Carrito
              </button>
            </div>
          </div>
        `;
      }

      contTarjetas.innerHTML = `
        ${generarTarjetaProd(prodA, "border-t-[#784516]", "A", costoTragoA, tragosA, labelDosisA)}
        ${generarTarjetaProd(prodB, "border-t-[#753B47]", "B", costoTragoB, tragosB, labelDosisB)}
      `;

      const nPersEfectivo = COOPERADORES_TOTAL > 0 ? COOPERADORES_TOTAL : 12;
      const cantSimulada = (esVinoA || esVinoB)
        ? Math.max(3, Math.round(nPersEfectivo / 3))
        : Math.max(2, Math.round(nPersEfectivo / 4));

      const costoSimA = prodA.precio_promo * cantSimulada;
      const costoSimB = prodB.precio_promo * cantSimulada;
      const ahorroTotalSim = Math.abs(costoSimA - costoSimB);
      const ahorroPorPersona = COOPERADORES_TOTAL > 0 ? (ahorroTotalSim / COOPERADORES_TOTAL) : 0;

      const badgePersonasTexto = COOPERADORES_TOTAL > 0
        ? `Simulación activa para ${COOPERADORES_TOTAL} personas · ${cantSimulada} botellas`
        : `Simulación base (${cantSimulada} botellas) · Escribe personas arriba para personalizar`;

      impactoBox.innerHTML = `
        <div class="space-y-4 min-w-0">
          <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-[#DFD5C7] pb-4">
            <div class="space-y-1 min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="badge bg-[#F8E2C8] text-[#784516] border border-[#E5C8A3] text-xs whitespace-normal text-left">
                  ${badgePersonasTexto}
                </span>
              </div>
              <h4 class="text-base font-bold font-display-md3 text-[#1F1B16] mt-1 break-words">
                Simulación de Impacto en la Cuenta
              </h4>
            </div>

            <div class="grid grid-cols-2 sm:grid-cols-3 gap-3 w-full sm:w-auto text-center">
              <div class="md3-surface-low p-2.5">
                <div class="text-[10px] text-[#574A3D] uppercase">${cantSimulada}× Opción A vs B</div>
                <div class="text-xs font-mono font-bold text-[#1F1B16] mt-0.5">$${costoSimA.toFixed(0)} vs $${costoSimB.toFixed(0)}</div>
              </div>
              <div class="md3-surface-low p-2.5">
                <div class="text-[10px] text-[#486355] uppercase font-bold">Ahorro Total</div>
                <div class="text-sm font-mono font-black text-[#486355] mt-0.5">$${ahorroTotalSim.toFixed(2)}</div>
              </div>
              <div class="md3-surface-low p-2.5 col-span-2 sm:col-span-1">
                <div class="text-[10px] text-[#784516] uppercase font-bold">Ahorro / Persona</div>
                <div class="text-sm font-mono font-black text-[#784516] mt-0.5">${COOPERADORES_TOTAL > 0 ? '-$' + ahorroPorPersona.toFixed(2) + ' c/u' : 'Ingresa personas'}</div>
              </div>
            </div>
          </div>

          ${generarTipFamiliar(prodA, prodB, ahorroTotalSim, ahorroPorPersona, cantSimulada, nPersEfectivo)}
        </div>
      `;

      const ganadorLitro = prodA.precio_por_litro <= prodB.precio_por_litro ? prodA : prodB;
      const perdedorLitro = prodA.precio_por_litro <= prodB.precio_por_litro ? prodB : prodA;
      const difLitro = Math.abs(prodA.precio_por_litro - prodB.precio_por_litro);
      const pctLitro = ((difLitro / perdedorLitro.precio_por_litro) * 100).toFixed(1);

      veredictoBox.innerHTML = `
        <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div class="space-y-1.5 min-w-0 flex-1">
            <span class="badge bg-[#D3E8DC] text-[#0B2016] border border-[#B7D6C5] uppercase">Veredicto de Compra</span>
            <h3 class="text-lg sm:text-xl font-bold font-display-md3 text-[#1F1B16] break-words">
              🏆 Mejor Rendimiento $/Litro: <span class="text-[#784516]">${ganadorLitro.producto} (${ganadorLitro.tienda})</span>
            </h3>
            <p class="text-xs text-[#574A3D] max-w-3xl leading-relaxed break-words">
              Ofrece un costo estandarizado de <strong class="text-[#1F1B16]">$${ganadorLitro.precio_por_litro.toFixed(2)} por litro</strong> frente a
              <strong>$${perdedorLitro.precio_por_litro.toFixed(2)}/L</strong> de ${perdedorLitro.producto} (${perdedorLitro.tienda}),
              lo que equivale a un ahorro real de <strong class="text-[#486355]">$${difLitro.toFixed(2)} por cada litro (${pctLitro}%)</strong>.
            </p>
          </div>
          <div class="flex items-center gap-2 flex-wrap w-full sm:w-auto pt-2 sm:pt-0">
            <a href="${ganadorLitro.url}" target="_blank" rel="noopener noreferrer"
               class="flex-1 sm:flex-initial px-4 py-2.5 md3-btn-tonal text-xs whitespace-normal sm:whitespace-nowrap inline-flex items-center justify-center gap-1.5 text-center"
               title="Abrir ${ganadorLitro.producto} en ${ganadorLitro.tienda}">
              <span>Ver en ${ganadorLitro.tienda}</span> <span>↗</span>
            </a>
            <button onclick="modificarCantidad(${DATOS_COMPLETOS.indexOf(ganadorLitro)}, 1); mostrarToast('🏆 Ganador añadido al carrito: ${ganadorLitro.producto.replace(/'/g, "\\'")}');" class="flex-1 sm:flex-initial px-5 py-2.5 md3-btn-filled text-xs whitespace-normal sm:whitespace-nowrap cursor-pointer text-center">
              + Agregar Ganador al Carrito
            </button>
          </div>
        </div>
      `;
    }
