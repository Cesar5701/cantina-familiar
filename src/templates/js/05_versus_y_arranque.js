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
        btn.className = "w-full sm:w-auto text-left whitespace-normal break-words rounded px-3 py-1.5 text-xs font-mono font-semibold border border-outline-variant bg-surface-container-lowest text-on-surface hover:bg-secondary-container/70 hover:border-secondary transition-all cursor-pointer shadow-2xs leading-snug";
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
          <div class="bg-surface-container p-4 rounded border border-outline-variant/70 text-xs space-y-1.5 text-on-surface">
            <div class="font-mono font-bold text-primary uppercase tracking-wider text-[11px]">
              Nota Forense de Arbitraje · Añejo Cristalino
            </div>
            <p class="text-on-surface-variant leading-relaxed">
              <strong>Maestro Dobel Diamante en Sam's Club ($574.93)</strong>, <strong>1800 Cristalino en Alianza ($600)</strong> y <strong>Don Julio 70 en Walmart ($699)</strong> lideran cada segmento. Elegir la opción de mejor precio en ${cantBotellas} botellas representa un ahorro directo de <strong class="text-on-surface">$${ahorroTotal.toFixed(2)} MXN</strong> ${textoCuota}.
            </p>
          </div>
        `;
      }

      if (catA.includes("Mezcal") && catB.includes("Mezcal")) {
        return `
          <div class="bg-surface-container p-4 rounded border border-outline-variant/70 text-xs space-y-1.5 text-on-surface">
            <div class="font-mono font-bold text-[#2d6a36] uppercase tracking-wider text-[11px]">
              Nota Forense de Arbitraje · Mezcal Artesanal
            </div>
            <p class="text-on-surface-variant leading-relaxed">
              La línea <strong>400 Conejos en Chedraui ($520 en Reposado, Tobalá y Cuishe)</strong> tiene un descuento de $130 por botella frente a Bodegas Alianza ($650), mientras que <strong>Amarás Reposado en Alianza ($503.30)</strong> es el campeón en relación suavidad-precio.
            </p>
          </div>
        `;
      }

      return `
        <div class="bg-surface-container p-4 rounded border border-outline-variant/70 text-xs text-on-surface-variant leading-relaxed">
          <strong class="text-on-surface font-mono uppercase text-[11px]">Dictamen de Volumen:</strong> Optar por la presentación de menor $/Litro dentro del mismo tipo de bebida ahorra <strong class="text-primary">$${ahorroTotal.toFixed(2)} MXN</strong> en una compra de ${cantBotellas} unidades ${textoCuota}.
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
          <div class="bg-error-container border border-[#e0a8a1] rounded-lg p-3.5 flex items-start gap-2.5 text-xs text-on-error-container">
            <span class="material-symbols-outlined text-[18px] mt-0.5">warning</span>
            <div>
              <strong class="font-mono font-bold uppercase text-[11px]">Comparando Escalafones de Maduración Distintos:</strong>
              <p class="mt-0.5">
                Estás enfrentando <strong>${prodA.categoria_comparable}</strong> contra <strong>${prodB.categoria_comparable}</strong>.
                Para una comparativa equivalente en tiempo de barrica, selecciona un subtipo específico arriba.
              </p>
            </div>
          </div>
        `;
      } else {
        alertaCompat.innerHTML = `
          <div class="bg-[#eaf4ec] border border-[#c5dfc9] rounded-lg p-3 flex items-center gap-2 text-xs text-[#24592a]">
            <span class="material-symbols-outlined text-[18px]">verified</span>
            <span class="font-mono text-[11px]"><strong>Paridad Categórica Verificada:</strong> Ambos contendientes pertenecen al escalafón <strong>${prodA.categoria_comparable}</strong>.</span>
          </div>
        `;
      }

      const esVinoA = prodA.categoria_comparable.includes("Vino");
      const esVinoB = prodB.categoria_comparable.includes("Vino");
      const dosisA = esVinoA ? 150 : 45;
      const dosisB = esVinoB ? 150 : 45;
      const labelDosisA = esVinoA ? "Copa (150 mL)" : "Trago (45 mL)";
      const labelDosisB = esVinoB ? "Copa (150 mL)" : "Trago (45 mL)";

      const costoTragoA = (prodA.precio_promo / prodA.ml) * dosisA;
      const costoTragoB = (prodB.precio_promo / prodB.ml) * dosisB;
      const tragosA = Math.floor(prodA.ml / dosisA);
      const tragosB = Math.floor(prodB.ml / dosisB);
      const ganadorLitro = prodA.precio_por_litro <= prodB.precio_por_litro ? prodA : prodB;
      const perdedorLitro = prodA.precio_por_litro <= prodB.precio_por_litro ? prodB : prodA;

      function generarTarjetaProd(p, colorBorder, letra, costoTrago, tragosTotales, labelDosis) {
        const esGanador = p === ganadorLitro;
        const ahorro = p.ahorro_verificable > 0
          ? `<span class="badge bg-[#eaf4ec] text-[#24592a] border border-[#c5dfc9] whitespace-normal text-left">-$${p.ahorro_verificable.toFixed(2)} (${p.porcentaje_ahorro}%)</span>`
          : `<span class="font-mono text-[11px] text-outline">Precio Regular</span>`;

        const tiendaBadge = getBadgeTienda(p.tienda, false);

        return `
          <div class="bg-surface-container-lowest rounded-lg border border-outline-variant/80 border-t-4 ${colorBorder} p-5 space-y-4 min-w-0 overflow-hidden shadow-xs">
            <div class="flex flex-wrap justify-between items-start gap-2 pb-3 border-b border-outline-variant/50">
              <div class="flex items-center gap-2">
                <span class="badge bg-surface-container border border-outline-variant/80 font-bold text-xs text-on-surface">Contendiente ${letra}</span>
                ${esGanador ? `<span class="badge bg-[#eaf4ec] text-[#24592a] border border-[#c5dfc9] text-[10px]">★ Óptimo $/L</span>` : ''}
              </div>
              <div class="flex flex-wrap gap-1.5 items-center">${tiendaBadge}${ahorro}</div>
            </div>

            <div class="min-w-0">
              <span class="archival-badge text-primary">${p.categoria_comparable}</span>
              <h4 class="text-lg sm:text-xl font-bold font-headline text-on-surface mt-1 leading-snug break-words">${p.producto}</h4>
              <p class="font-mono text-xs text-on-surface-variant mt-1 break-words">${p.marca} · ${p.ml} mL · ${getABV(p)}</p>
            </div>

            <!-- Métricas Volumétricas Primarias -->
            <div class="grid grid-cols-2 gap-3 bg-surface-container-low p-3.5 rounded border border-outline-variant/50">
              <div>
                <span class="font-mono text-[10px] uppercase tracking-wider text-on-surface-variant block">Precio Botella</span>
                <div class="text-xl sm:text-2xl font-bold font-mono text-on-surface mt-0.5">$${p.precio_promo.toFixed(2)}</div>
              </div>
              <div class="border-l border-outline-variant/50 pl-3">
                <span class="font-mono text-[10px] uppercase tracking-wider text-primary font-bold block">$/Litro Auditado</span>
                <div class="text-xl sm:text-2xl font-bold font-mono text-primary mt-0.5">$${p.precio_por_litro.toFixed(2)}</div>
              </div>
            </div>

            <!-- Rendimiento por Servicio -->
            <div class="grid grid-cols-2 gap-3 bg-surface-container p-3 rounded border border-outline-variant/50 text-xs">
              <div>
                <span class="font-mono text-[10px] uppercase text-on-surface-variant block">Costo / ${labelDosis}</span>
                <div class="text-sm sm:text-base font-bold font-mono text-[#2d6a36] mt-0.5">$${costoTrago.toFixed(2)} MXN</div>
              </div>
              <div class="border-l border-outline-variant/50 pl-3">
                <span class="font-mono text-[10px] uppercase text-on-surface-variant block">Servicios / Envase</span>
                <div class="text-sm sm:text-base font-bold font-mono text-on-surface mt-0.5">~${tragosTotales} ${p.categoria_comparable.includes("Vino") ? "copas" : "tragos"}</div>
              </div>
            </div>

            <div class="text-xs bg-surface-container-low p-3 rounded border border-outline-variant/40 text-on-surface-variant leading-relaxed break-words">
              <strong class="font-mono text-[11px] uppercase text-on-surface">Nota de Guarda:</strong> ${getMaduracionInfo(p)}
            </div>

            <div class="pt-3 flex flex-col sm:flex-row justify-between items-stretch sm:items-center gap-2.5 text-xs border-t border-outline-variant/60">
              <a href="${p.url}" target="_blank" rel="noopener noreferrer" class="font-mono text-xs font-semibold text-primary hover:underline text-center sm:text-left py-1">
                Ficha en ${p.tienda} ↗
              </a>
              <button onclick="modificarCantidad(${DATOS_COMPLETOS.indexOf(p)}, 1); mostrarToast('Añadido al carrito: ${p.producto.replace(/'/g, "\\'")}');" class="w-full sm:w-auto px-4 py-2 md3-btn-filled text-xs cursor-pointer text-center">
                + Añadir al Carrito
              </button>
            </div>
          </div>
        `;
      }

      contTarjetas.innerHTML = `
        ${generarTarjetaProd(prodA, "border-t-primary", "Alpha [A]", costoTragoA, tragosA, labelDosisA)}
        ${generarTarjetaProd(prodB, "border-t-secondary", "Beta [B]", costoTragoB, tragosB, labelDosisB)}
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
          <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-outline-variant/60 pb-4">
            <div class="space-y-1 min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="badge bg-secondary-container text-on-secondary-fixed border border-outline-variant/70 text-xs whitespace-normal text-left">
                  ${badgePersonasTexto}
                </span>
              </div>
              <h4 class="text-lg font-bold font-headline text-on-surface mt-1 break-words">
                Proyección de Impacto en Cooperación Familiar
              </h4>
            </div>

            <div class="grid grid-cols-2 sm:grid-cols-3 gap-3 w-full sm:w-auto text-center">
              <div class="bg-surface-container-lowest p-3 rounded border border-outline-variant/60">
                <div class="font-mono text-[10px] text-on-surface-variant uppercase">${cantSimulada}× Alpha vs Beta</div>
                <div class="text-xs font-mono font-bold text-on-surface mt-0.5">$${costoSimA.toFixed(0)} vs $${costoSimB.toFixed(0)}</div>
              </div>
              <div class="bg-surface-container-lowest p-3 rounded border border-outline-variant/60">
                <div class="font-mono text-[10px] text-[#2d6a36] uppercase font-bold">Ahorro Total</div>
                <div class="text-sm font-mono font-black text-[#2d6a36] mt-0.5">$${ahorroTotalSim.toFixed(2)}</div>
              </div>
              <div class="bg-surface-container-lowest p-3 rounded border border-outline-variant/60 col-span-2 sm:col-span-1">
                <div class="font-mono text-[10px] text-primary uppercase font-bold">Ahorro / Persona</div>
                <div class="text-sm font-mono font-black text-primary mt-0.5">${COOPERADORES_TOTAL > 0 ? '-$' + ahorroPorPersona.toFixed(2) + ' c/u' : 'Ingresa personas'}</div>
              </div>
            </div>
          </div>

          ${generarTipFamiliar(prodA, prodB, ahorroTotalSim, ahorroPorPersona, cantSimulada, nPersEfectivo)}
        </div>
      `;

      const difLitro = Math.abs(prodA.precio_por_litro - prodB.precio_por_litro);
      const pctLitro = ((difLitro / perdedorLitro.precio_por_litro) * 100).toFixed(1);

      veredictoBox.innerHTML = `
        <div class="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-5 relative z-10">
          <div class="space-y-2 min-w-0 flex-1">
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-[#ffd6ab] text-[20px]">gavel</span>
              <span class="px-2 py-0.5 rounded bg-[#52443c] text-[#ffd6ab] font-mono text-[10px] font-bold uppercase tracking-widest">
                Veredicto Forense de Compra
              </span>
            </div>
            <h3 class="text-xl sm:text-2xl font-bold font-headline text-[#fdefdb] break-words leading-snug">
              Campeón Volumétrico $/Litro: <span class="text-[#ffd6ab]">${ganadorLitro.producto} (${ganadorLitro.tienda})</span>
            </h3>
            <p class="text-xs sm:text-sm text-[#fdefdb]/85 max-w-3xl leading-relaxed break-words">
              Registra un costo estandarizado de <strong class="text-white font-mono">$${ganadorLitro.precio_por_litro.toFixed(2)} / L</strong> frente a
              <strong class="font-mono">$${perdedorLitro.precio_por_litro.toFixed(2)} / L</strong> de ${perdedorLitro.producto} (${perdedorLitro.tienda}),
              generando un diferencial verificable de <strong class="text-[#ffd6ab] font-mono">$${difLitro.toFixed(2)} por litro (${pctLitro}% de ahorro)</strong>.
            </p>
          </div>
          <div class="flex items-center gap-2.5 flex-wrap w-full lg:w-auto pt-2 lg:pt-0">
            <a href="${ganadorLitro.url}" target="_blank" rel="noopener noreferrer"
               class="flex-1 sm:flex-initial px-4 py-2.5 rounded bg-[#52443c] hover:bg-[#67574d] text-[#fdefdb] border border-[#85746b] font-mono text-xs font-semibold whitespace-normal sm:whitespace-nowrap inline-flex items-center justify-center gap-1.5 text-center transition-colors"
               title="Abrir ${ganadorLitro.producto} en ${ganadorLitro.tienda}">
              <span>Ver en ${ganadorLitro.tienda}</span> <span>↗</span>
            </a>
            <button onclick="modificarCantidad(${DATOS_COMPLETOS.indexOf(ganadorLitro)}, 1); mostrarToast('Ganador añadido al carrito: ${ganadorLitro.producto.replace(/'/g, "\\'")}');" class="flex-1 sm:flex-initial px-5 py-2.5 rounded bg-[#ffd6ab] hover:bg-[#f3c491] text-[#2b1700] font-mono font-bold text-xs whitespace-normal sm:whitespace-nowrap cursor-pointer text-center transition-colors shadow-sm">
              + Agregar Ganador al Carrito
            </button>
          </div>
        </div>
      `;
    }
