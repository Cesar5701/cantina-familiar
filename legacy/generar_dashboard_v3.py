"""
Generador del Dashboard BI interactivo v3.
Incluye:
- Corrección de categorías (Gran Centenario Ultra en Reposado Cristalino).
- Controles interactivos de Presupuesto ($ MXN) y Cooperadores (N personas).
- Módulo 'Optimizador de Canastas por Presupuesto' con presets y constructor libre.
- Medidor de presupuesto en tiempo real y cálculo de cuota familiar.
- Pestañas: Rankings $/L, Head-to-Head VERSUS, Optimizador/Simulador, Guía de Clases NOM.
"""

import os
import json

ARTIFACT_DIR = "/home/cesar/.gemini/antigravity/brain/cf5b6fe1-c31f-46a0-a350-06d6d2e984ca"
HTML_ARTIFACT_PATH = os.path.join(ARTIFACT_DIR, "dashboard_bi.html")
LOCAL_HTML_PATH = "data/dashboard_bi.html"

with open("data/dashboard_data.json", "r", encoding="utf-8") as f:
    datos_json_str = f.read()

html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Cantina Familiar 2026 · BI Decision Platform</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{ background: var(--border, #cbd5e1); border-radius: 3px; }}
    .badge {{ display: inline-flex; align-items: center; padding: 0.125rem 0.5rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 500; }}
  </style>
</head>
<body class="bg-[var(--background,#0f172a)] text-[var(--foreground,#f8fafc)] antialiased p-3 sm:p-6 min-h-screen">

  <div class="max-w-7xl mx-auto space-y-6">

    <!-- HEADER / BANNER CON CONTROLES DE PRESUPUESTO Y COOPERADORES -->
    <header class="bg-[var(--card,#1e293b)] border border-[var(--border,#334155)] rounded-2xl p-6 shadow-sm flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6">
      <div class="space-y-1.5">
        <div class="flex flex-wrap items-center gap-2">
          <span class="badge bg-amber-500/20 text-amber-400 border border-amber-500/30">Navidad 2026</span>
          <span class="badge bg-blue-500/20 text-blue-400 border border-blue-500/30">San Pedro Xalcaltzinco (CP 90180)</span>
          <span class="badge bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">Clasificación Estricta NOM</span>
        </div>
        <h1 class="text-2xl sm:text-3xl font-bold tracking-tight text-[var(--foreground,#f8fafc)]">
          Cantina Familiar 2026 · BI Decision Platform
        </h1>
        <p class="text-[var(--muted-foreground,#94a3b8)] text-sm">
          Simulador dinámico de canasta familiar, optimizador por presupuesto y benchmarking por categoría comparable.
        </p>
      </div>

      <!-- CONTROLES REACTIVOS: PRESUPUESTO Y COOPERADORES -->
      <div class="flex flex-wrap sm:flex-nowrap items-center gap-4 bg-[var(--background,#0f172a)] p-3.5 rounded-xl border border-[var(--border,#334155)] w-full lg:w-auto justify-between lg:justify-end">
        <div>
          <label class="block text-xs font-semibold text-emerald-400 uppercase">Presupuesto ($ MXN):</label>
          <div class="flex items-center gap-1 mt-0.5">
            <span class="text-sm font-bold text-emerald-400">$</span>
            <input type="number" id="input-presupuesto" value="9000" min="1000" step="500" oninput="actualizarParametrosGlobales()"
                   class="w-24 bg-transparent font-black text-lg text-emerald-400 border-b border-emerald-500/40 focus:outline-none focus:border-emerald-400">
          </div>
        </div>
        <div class="h-8 w-px bg-[var(--border,#334155)] hidden sm:block"></div>
        <div>
          <label class="block text-xs font-semibold text-amber-400 uppercase">Cooperadores:</label>
          <div class="flex items-center gap-1 mt-0.5">
            <input type="number" id="input-cooperadores" value="14" min="1" max="50" oninput="actualizarParametrosGlobales()"
                   class="w-16 bg-transparent font-black text-lg text-amber-400 border-b border-amber-500/40 focus:outline-none focus:border-amber-400">
            <span class="text-xs text-[var(--muted-foreground,#94a3b8)]">personas</span>
          </div>
        </div>
      </div>
    </header>

    <!-- ALERTA DE RIGOR CATEGÓRICO -->
    <div class="bg-blue-950/40 border border-blue-500/30 rounded-xl p-3.5 text-xs text-blue-200 flex items-start gap-3">
      <span class="text-lg">⚖️</span>
      <div class="leading-relaxed">
        <strong class="text-blue-300">Auditoría de Categorías Completada:</strong>
        Se rectificó la clasificación según la NOM-006-SCFI: <em>Gran Centenario Ultra</em> es un <strong>Reposado Cristalino</strong> (madurado de 2 a 11 meses), por lo que no compite deslealmente contra los <strong>Añejos Cristalinos</strong> (&ge; 12 meses como 1800 Cristalino, Maestro Dobel Diamante o Don Julio 70).
      </div>
    </div>

    <!-- KPI STRIP REACTIVO -->
    <section class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="bg-[var(--card,#1e293b)] border border-[var(--border,#334155)] rounded-xl p-4 shadow-sm">
        <div class="text-xs text-[var(--muted-foreground,#94a3b8)] uppercase font-semibold">Tequilas Añejos Cristalinos</div>
        <div class="text-2xl font-bold text-[var(--foreground,#f8fafc)] mt-1">32 opciones</div>
        <div class="text-xs text-blue-400 mt-1">1800, Dobel, Don Julio 70, Ultra</div>
      </div>
      <div class="bg-[var(--card,#1e293b)] border border-[var(--border,#334155)] rounded-xl p-4 shadow-sm">
        <div class="text-xs text-[var(--muted-foreground,#94a3b8)] uppercase font-semibold">Tequilas Añejos Tradicionales</div>
        <div class="text-2xl font-bold text-amber-400 mt-1">27 opciones</div>
        <div class="text-xs text-[var(--muted-foreground,#94a3b8)] mt-1">Tres Generaciones, 1800, Herradura</div>
      </div>
      <div class="bg-[var(--card,#1e293b)] border border-[var(--border,#334155)] rounded-xl p-4 shadow-sm">
        <div class="text-xs text-[var(--muted-foreground,#94a3b8)] uppercase font-semibold">Cuota / Cooperador</div>
        <div class="text-2xl font-bold text-amber-400 mt-1" id="kpi-cuota-global">$474.89</div>
        <div class="text-xs text-emerald-400 mt-1" id="kpi-sobrante-global">Sobrante: +$2,351.55 MXN</div>
      </div>
      <div class="bg-[var(--card,#1e293b)] border border-[var(--border,#334155)] rounded-xl p-4 shadow-sm">
        <div class="text-xs text-[var(--muted-foreground,#94a3b8)] uppercase font-semibold">Uso del Presupuesto</div>
        <div class="text-2xl font-bold text-emerald-400 mt-1" id="kpi-porcentaje-uso">73.9%</div>
        <div class="w-full bg-[var(--background,#0f172a)] h-1.5 rounded-full overflow-hidden mt-2">
          <div id="kpi-barra-presupuesto" class="bg-emerald-500 h-full rounded-full transition-all duration-300" style="width: 73.9%"></div>
        </div>
      </div>
    </section>

    <!-- NAVIGATION TABS -->
    <div class="flex border-b border-[var(--border,#334155)] gap-2 overflow-x-auto pb-1">
      <button onclick="cambiarTab('tab-simulador')" id="btn-tab-simulador" class="tab-btn px-4 py-2 text-sm font-semibold rounded-t-lg border-b-2 border-emerald-500 text-emerald-400 bg-[var(--card,#1e293b)]">
        🧮 Optimizador y Simulador por Presupuesto
      </button>
      <button onclick="cambiarTab('tab-rankings')" id="btn-tab-rankings" class="tab-btn px-4 py-2 text-sm font-semibold rounded-t-lg border-b-2 border-transparent text-[var(--muted-foreground,#94a3b8)] hover:text-[var(--foreground,#f8fafc)]">
        📊 Rankings por Categoría Comparable
      </button>
      <button onclick="cambiarTab('tab-versus')" id="btn-tab-versus" class="tab-btn px-4 py-2 text-sm font-semibold rounded-t-lg border-b-2 border-transparent text-[var(--muted-foreground,#94a3b8)] hover:text-[var(--foreground,#f8fafc)]">
        ⚔️ Head-to-Head VERSUS (Comparador de Decisión)
      </button>
      <button onclick="cambiarTab('tab-matriz')" id="btn-tab-matriz" class="tab-btn px-4 py-2 text-sm font-semibold rounded-t-lg border-b-2 border-transparent text-[var(--muted-foreground,#94a3b8)] hover:text-[var(--foreground,#f8fafc)]">
        🎯 Rúbrica & Guía de Clases (NOM)
      </button>
    </div>

    <!-- ========================================================================================= -->
    <!-- TAB 1: OPTIMIZADOR Y SIMULADOR POR PRESUPUESTO (NUEVA PESTAÑA PRINCIPAL) -->
    <!-- ========================================================================================= -->
    <div id="tab-simulador" class="tab-content space-y-6">

      <!-- PRESETS DE CANASTAS RECOMENDADAS POR PRESUPUESTO -->
      <div class="bg-[var(--card,#1e293b)] border border-[var(--border,#334155)] rounded-xl p-5 shadow-sm space-y-4">
        <div>
          <h3 class="font-bold text-base text-[var(--foreground,#f8fafc)]">
            🎯 Canastas Pre-optimizadas según tu Presupuesto
          </h3>
          <p class="text-xs text-[var(--muted-foreground,#94a3b8)] mt-0.5">
            Selecciona un perfil pre-armado con un solo clic para cargar sus botellas directamente en el simulador interactivo:
          </p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <!-- Preset 1: Ahorro Máximo -->
          <div class="bg-[var(--background,#0f172a)] border border-emerald-500/30 rounded-xl p-4 flex flex-col justify-between hover:border-emerald-500/60 transition-colors">
            <div>
              <span class="badge bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs font-semibold">Perfil 1: Ahorro Máximo</span>
              <div class="text-xl font-bold text-emerald-400 mt-2">$5,983.85</div>
              <div class="text-xs text-[var(--muted-foreground,#94a3b8)] mt-1" id="preset-1-cuota">~$427 por persona</div>
              <ul class="text-[11px] text-[var(--muted-foreground,#94a3b8)] space-y-1 mt-3 border-t border-[var(--border,#334155)] pt-2">
                <li>• 3× 1800 Cristalino ($600 c/u)</li>
                <li>• 1× Tres Generaciones Añejo ($567)</li>
                <li>• Canasta A Mezcal ($1,674)</li>
                <li>• 1× JW Red Label 1.75L Sam's ($627)</li>
                <li>• 2× Honey 700ml ($756)</li>
                <li>• 5× California Tetra Pak ($415)</li>
              </ul>
            </div>
            <button onclick="cargarPreset('ahorro')" class="mt-4 w-full py-1.5 px-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-semibold text-white transition-colors">
              Cargar en Constructor
            </button>
          </div>

          <!-- Preset 2: Balanceada Recomendada -->
          <div class="bg-[var(--background,#0f172a)] border border-amber-500/30 rounded-xl p-4 flex flex-col justify-between hover:border-amber-500/60 transition-colors">
            <div>
              <span class="badge bg-amber-500/20 text-amber-400 border border-amber-500/30 text-xs font-semibold">Perfil 2: Balanceada (Recomendada)</span>
              <div class="text-xl font-bold text-amber-400 mt-2">$6,648.45</div>
              <div class="text-xs text-[var(--muted-foreground,#94a3b8)] mt-1" id="preset-2-cuota">~$475 por persona</div>
              <ul class="text-[11px] text-[var(--muted-foreground,#94a3b8)] space-y-1 mt-3 border-t border-[var(--border,#334155)] pt-2">
                <li>• 3× 1800 Cristalino ($600 c/u)</li>
                <li>• 1× 1800 Añejo Tradicional ($599)</li>
                <li>• Canasta A Mezcal ($1,674)</li>
                <li>• 1× JW Red Label 1.75L Sam's ($627)</li>
                <li>• 2× Honey 700ml ($756)</li>
                <li>• 5× California Tetra Pak ($415)</li>
              </ul>
            </div>
            <button onclick="cargarPreset('balanceada')" class="mt-4 w-full py-1.5 px-3 rounded-lg bg-amber-600 hover:bg-amber-500 text-xs font-semibold text-white transition-colors">
              Cargar en Constructor
            </button>
          </div>

          <!-- Preset 3: Silvestre & 3 Honey -->
          <div class="bg-[var(--background,#0f172a)] border border-blue-500/30 rounded-xl p-4 flex flex-col justify-between hover:border-blue-500/60 transition-colors">
            <div>
              <span class="badge bg-blue-500/20 text-blue-400 border border-blue-500/30 text-xs font-semibold">Perfil 3: Silvestre & 3 Honey</span>
              <div class="text-xl font-bold text-blue-400 mt-2">$7,078.35</div>
              <div class="text-xs text-[var(--muted-foreground,#94a3b8)] mt-1" id="preset-3-cuota">~$506 por persona</div>
              <ul class="text-[11px] text-[var(--muted-foreground,#94a3b8)] space-y-1 mt-3 border-t border-[var(--border,#334155)] pt-2">
                <li>• 3× 1800 Cristalino ($600 c/u)</li>
                <li>• 1× 1800 Añejo Tradicional ($599)</li>
                <li>• Canasta B Silvestre Cupreata ($1,890)</li>
                <li>• 1× JW Red Label 1.75L Sam's ($627)</li>
                <li>• 3× Honey 700ml ($1,134)</li>
                <li>• 5× California Tetra Pak ($415)</li>
              </ul>
            </div>
            <button onclick="cargarPreset('silvestre')" class="mt-4 w-full py-1.5 px-3 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white transition-colors">
              Cargar en Constructor
            </button>
          </div>

          <!-- Preset 4: Gala Premium -->
          <div class="bg-[var(--background,#0f172a)] border border-purple-500/30 rounded-xl p-4 flex flex-col justify-between hover:border-purple-500/60 transition-colors">
            <div>
              <span class="badge bg-purple-500/20 text-purple-400 border border-purple-500/30 text-xs font-semibold">Perfil 4: Gala Premium</span>
              <div class="text-xl font-bold text-purple-400 mt-2">$7,613.35</div>
              <div class="text-xs text-[var(--muted-foreground,#94a3b8)] mt-1" id="preset-4-cuota">~$544 por persona</div>
              <ul class="text-[11px] text-[var(--muted-foreground,#94a3b8)] space-y-1 mt-3 border-t border-[var(--border,#334155)] pt-2">
                <li>• 2× 1800 Crist + 1× Don Julio 70 ($1,978)</li>
                <li>• 1× Herradura Añejo ($777)</li>
                <li>• Canasta B Silvestre Cupreata ($1,890)</li>
                <li>• 1× JW Red Label 1.75L Sam's ($627)</li>
                <li>• 3× Honey 700ml ($1,134)</li>
                <li>• 1× Garrafa Carlo Rossi 4L + 1 TP ($521)</li>
              </ul>
            </div>
            <button onclick="cargarPreset('gala')" class="mt-4 w-full py-1.5 px-3 rounded-lg bg-purple-600 hover:bg-purple-500 text-xs font-semibold text-white transition-colors">
              Cargar en Constructor
            </button>
          </div>
        </div>
      </div>

      <!-- CONSTRUCTOR LIBRE DE CANASTA INTERACTIVO -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

        <!-- SELECTORES DE BOTELLAS (2 COLUMNAS) -->
        <div class="lg:col-span-2 space-y-4">
          <div class="bg-[var(--card,#1e293b)] border border-[var(--border,#334155)] rounded-xl p-5 shadow-sm space-y-4">
            <div class="flex justify-between items-center border-b border-[var(--border,#334155)] pb-3">
              <h3 class="font-bold text-base text-[var(--foreground,#f8fafc)]">
                Constructor de Canasta Personalizada
              </h3>
              <span class="text-xs text-[var(--muted-foreground,#94a3b8)]">Cambia cualquier botella y evalúa el impacto</span>
            </div>

            <!-- 1. Tequila Añejo Cristalino (3 Botellas) -->
            <div>
              <div class="flex justify-between items-center mb-1">
                <label class="text-xs font-semibold text-amber-400">1. Tequila Añejo Cristalino (3 Botellas):</label>
                <span class="text-xs font-mono text-emerald-400" id="costo-item-cristalino">$1,800.00</span>
              </div>
              <select id="sim-cristalino" onchange="recalcularSimulador()" class="w-full bg-[var(--background,#0f172a)] border border-[var(--border,#334155)] rounded-lg p-2 text-sm text-[var(--foreground,#f8fafc)]">
                <option value="1800_cristalino">3 × Tequila 1800 Añejo Cristalino ($600 c/u) = $1,800.00</option>
                <option value="dobel_diamante">3 × Maestro Dobel Diamante ($655 c/u) = $1,965.00</option>
                <option value="herradura_ultra">3 × Herradura Ultra Añejo Cristalino ($623 c/u) = $1,869.00</option>
                <option value="don_julio_70">3 × Don Julio 70 Cristalino ($778 c/u) = $2,334.00</option>
                <option value="mix_2_1800_1_dj70">2 × 1800 Cristalino + 1 × Don Julio 70 = $1,978.00</option>
                <option value="tezona_cristalino">3 × Tezón Añejo Cristalino ($553 c/u) = $1,659.00</option>
              </select>
            </div>

            <!-- 2. Tequila Añejo Tradicional (1 Botella) -->
            <div>
              <div class="flex justify-between items-center mb-1">
                <label class="text-xs font-semibold text-amber-400">2. Tequila Añejo Tradicional (1 Botella base de madera):</label>
                <span class="text-xs font-mono text-emerald-400" id="costo-item-anejo">$599.25</span>
              </div>
              <select id="sim-anejo" onchange="recalcularSimulador()" class="w-full bg-[var(--background,#0f172a)] border border-[var(--border,#334155)] rounded-lg p-2 text-sm text-[var(--foreground,#f8fafc)]">
                <option value="1800_anejo">1 × 1800 Añejo Tradicional 700ml ($599.25)</option>
                <option value="tres_generaciones">1 × Tres Generaciones Añejo 750ml ($567.00) [Triple Destilación]</option>
                <option value="hornitos_black">1 × Hornitos Black Barrel Añejo 750ml ($451.50)</option>
                <option value="herradura_anejo">1 × Herradura Añejo 750ml ($777.00)</option>
                <option value="jimador_anejo">1 × El Jimador Añejo 700ml ($357.00)</option>
              </select>
            </div>

            <!-- 3. Mezcales (Canasta de 3 Botellas) -->
            <div>
              <div class="flex justify-between items-center mb-1">
                <label class="text-xs font-semibold text-emerald-400">3. Canasta de Mezcales (3 Botellas):</label>
                <span class="text-xs font-mono text-emerald-400" id="costo-item-mezcal">$1,674.10</span>
              </div>
              <select id="sim-mezcal" onchange="recalcularSimulador()" class="w-full bg-[var(--background,#0f172a)] border border-[var(--border,#334155)] rounded-lg p-2 text-sm text-[var(--foreground,#f8fafc)]">
                <option value="canasta_a">Canasta A: 2 × Amarás Reposado + 1 × 400 Conejos Añejo = $1,674.10</option>
                <option value="canasta_b">Canasta B: 1 × Amarás Rep. + 1 × 400 Conejos Añejo + 1 × Amarás Cupreata Silvestre = $1,890.00</option>
                <option value="canasta_c">Canasta C (Ojo de Tigre): 2 × Ojo de Tigre Reposado + 1 × 400 Conejos Añejo = $1,900.00</option>
                <option value="canasta_d">Canasta D (Silvestre Económica): 1 × Amarás Rep. + 1 × 400 Conejos Añejo + 1 × Tierra Mestiza Tobalá = $1,569.80</option>
              </select>
            </div>

            <!-- 4. Whisky Blended (1 Botella de alta capacidad) -->
            <div>
              <div class="flex justify-between items-center mb-1">
                <label class="text-xs font-semibold text-blue-400">4. Whisky Blended Scotch:</label>
                <span class="text-xs font-mono text-emerald-400" id="costo-item-whisky">$627.10</span>
              </div>
              <select id="sim-whisky" onchange="recalcularSimulador()" class="w-full bg-[var(--background,#0f172a)] border border-[var(--border,#334155)] rounded-lg p-2 text-sm text-[var(--foreground,#f8fafc)]">
                <option value="jw_red_175_sams">1 × Johnnie Walker Red Label 1.75 L (Sam's Club) = $627.10</option>
                <option value="jw_red_700_alianza">2 × Johnnie Walker Red Label 700 ml (Alianza) = $550.00</option>
                <option value="ballantines_2x">2 × Ballantine's Finest 700 ml (Alianza) = $457.50</option>
                <option value="william_lawsons_2l">1 × William Lawson's 2.0 L (Alianza) = $470.00</option>
              </select>
            </div>

            <!-- 5. Jack Daniel's Honey -->
            <div>
              <div class="flex justify-between items-center mb-1">
                <label class="text-xs font-semibold text-purple-400">5. Jack Daniel's Tennessee Honey:</label>
                <span class="text-xs font-mono text-emerald-400" id="costo-item-honey">$756.00</span>
              </div>
              <select id="sim-honey" onchange="recalcularSimulador()" class="w-full bg-[var(--background,#0f172a)] border border-[var(--border,#334155)] rounded-lg p-2 text-sm text-[var(--foreground,#f8fafc)]">
                <option value="honey_2_alianza">2 × Jack Daniel's Honey 700 ml (Alianza) = $756.00</option>
                <option value="honey_3_alianza">3 × Jack Daniel's Honey 700 ml (Alianza) = $1,134.00</option>
                <option value="honey_2_sams">2 × Jack Daniel's Honey 1.0 L (Sam's Club) = $1,125.30</option>
              </select>
            </div>

            <!-- 6. Vino Tinto para Clericot (~4.5 a 5 Litros) -->
            <div>
              <div class="flex justify-between items-center mb-1">
                <label class="text-xs font-semibold text-red-400">6. Vino Tinto para Clericot:</label>
                <span class="text-xs font-mono text-emerald-400" id="costo-item-vino">$415.00</span>
              </div>
              <select id="sim-vino" onchange="recalcularSimulador()" class="w-full bg-[var(--background,#0f172a)] border border-[var(--border,#334155)] rounded-lg p-2 text-sm text-[var(--foreground,#f8fafc)]">
                <option value="tetra_california">5 × Tetra Pak California 946 ml (4.73 L) = $415.00</option>
                <option value="carlo_rossi_combo">1 × Garrafa Carlo Rossi 4L (Sam's) + 1 × Tetra Pak California = $520.83</option>
                <option value="concha_toro_5x">5 × Concha y Toro Reservado Cabernet 750 ml (3.75 L) = $451.50</option>
              </select>
            </div>

          </div>
        </div>

        <!-- PANEL DE CONTROL FINANCIERO Y CUOTA (1 COLUMNA) -->
        <div class="space-y-4">
          <div class="bg-[var(--card,#1e293b)] border border-emerald-500/40 rounded-xl p-5 shadow-sm space-y-4 sticky top-6">
            <div class="flex items-center justify-between border-b border-[var(--border,#334155)] pb-3">
              <h3 class="font-bold text-base text-[var(--foreground,#f8fafc)]">Control de Presupuesto</h3>
              <span class="badge bg-emerald-500/20 text-emerald-400 border border-emerald-500/30" id="badge-cooperadores-resumen">14 Cooperadores</span>
            </div>

            <!-- BARRA DE CONSUMO DE PRESUPUESTO -->
            <div class="space-y-1.5">
              <div class="flex justify-between text-xs">
                <span class="text-[var(--muted-foreground,#94a3b8)]">Consumo del presupuesto:</span>
                <span class="font-bold font-mono" id="sim-porcentaje-barra">65.2%</span>
              </div>
              <div class="w-full bg-[var(--background,#0f172a)] h-2.5 rounded-full overflow-hidden border border-[var(--border,#334155)]">
                <div id="sim-barra-dinamica" class="bg-emerald-500 h-full rounded-full transition-all duration-300" style="width: 65.2%"></div>
              </div>
            </div>

            <!-- CUOTA EXACTA POR PERSONA -->
            <div class="bg-[var(--background,#0f172a)] border border-[var(--border,#334155)] rounded-xl p-4 text-center">
              <div class="text-xs text-[var(--muted-foreground,#94a3b8)] uppercase font-semibold">Cuota por Cooperador</div>
              <div class="text-3xl font-black text-amber-400 mt-1 font-mono" id="sim-cuota-persona">$474.89</div>
              <div class="text-xs text-[var(--muted-foreground,#94a3b8)] mt-1" id="sim-subtitulo-cuota">Dividido exactamente entre 14 personas</div>
            </div>

            <!-- TOTALES Y DESGLOSE LOGÍSTICO -->
            <div class="space-y-2 border-t border-[var(--border,#334155)] pt-3 text-xs">
              <div class="flex justify-between">
                <span class="text-[var(--muted-foreground,#94a3b8)]">Bodegas Alianza (Online/PayPal):</span>
                <span class="font-semibold font-mono" id="sim-total-alianza">$5,244.35</span>
              </div>
              <div class="flex justify-between">
                <span class="text-[var(--muted-foreground,#94a3b8)]">Sam's Club (Pickup Club):</span>
                <span class="font-semibold font-mono" id="sim-total-sams">$627.10</span>
              </div>
              <div class="flex justify-between text-sm font-bold pt-2 border-t border-[var(--border,#334155)]">
                <span>Costo Total Canasta:</span>
                <span class="text-emerald-400 font-mono text-base" id="sim-gran-total">$5,871.45</span>
              </div>
            </div>

            <!-- DINERO SOBRANTE O EXCEDENTE -->
            <div id="sim-alerta-sobrante" class="p-3 rounded-lg flex items-center justify-between text-xs bg-emerald-950/30 border border-emerald-500/30">
              <span class="text-emerald-300 font-medium" id="sim-label-sobrante">Dinero Sobrante:</span>
              <span class="text-emerald-400 font-bold text-sm font-mono" id="sim-sobrante">+$3,128.55</span>
            </div>

            <!-- NOTA LOGÍSTICA -->
            <div class="text-[11px] text-[var(--muted-foreground,#94a3b8)] space-y-1 border-t border-[var(--border,#334155)] pt-3">
              <p>• <strong>Alianza:</strong> Envío directo a CP 90180 (PayPal).</p>
              <p>• <strong>Sam's:</strong> Pickup Gran Patio Tlaxcala o CAPU Puebla.</p>
            </div>

          </div>
        </div>

      </div>
    </div>

    <!-- ========================================================================================= -->
    <!-- TAB 2: RANKINGS Y EXPLORADOR POR CATEGORÍA COMPARABLE -->
    <!-- ========================================================================================= -->
    <div id="tab-rankings" class="tab-content space-y-6 hidden">

      <!-- CONTROLES Y FILTROS -->
      <div class="bg-[var(--card,#1e293b)] border border-[var(--border,#334155)] rounded-xl p-4 shadow-sm flex flex-col md:flex-row gap-4 justify-between items-center">
        <div class="flex flex-wrap items-center gap-3 w-full md:w-auto">
          <!-- Búsqueda -->
          <div class="relative flex-1 sm:w-60">
            <input type="text" id="filtro-busqueda" oninput="aplicarFiltros()" placeholder="Buscar producto o marca..."
                   class="w-full bg-[var(--background,#0f172a)] border border-[var(--border,#334155)] rounded-lg px-3 py-1.5 text-sm text-[var(--foreground,#f8fafc)] focus:outline-none focus:border-emerald-500">
          </div>

          <!-- Selector de Categoría Comparable (Estricta) -->
          <select id="filtro-categoria" onchange="aplicarFiltros()" class="bg-[var(--background,#0f172a)] border border-[var(--border,#334155)] rounded-lg px-3 py-1.5 text-sm text-[var(--foreground,#f8fafc)] font-medium">
            <option value="Tequila - Añejo Cristalino" selected>Tequila: Añejo Cristalino (32)</option>
            <option value="Tequila - Añejo Tradicional">Tequila: Añejo Tradicional (27)</option>
            <option value="Tequila - Reposado Cristalino">Tequila: Reposado Cristalino (28)</option>
            <option value="Mezcal - Reposado">Mezcal: Reposado (17)</option>
            <option value="Mezcal - Añejo">Mezcal: Añejo (6)</option>
            <option value="Mezcal - Silvestre">Mezcal: Silvestre (24)</option>
            <option value="Whisky - Blended Scotch">Whisky: Blended Scotch (55)</option>
            <option value="Licor de Whisky - Honey">Licor de Whisky: Honey (4)</option>
            <option value="Vino - Tinto Clericot">Vino: Tinto Clericot (85)</option>
            <option value="Todas">Mostrar Todo el Catálogo (286)</option>
          </select>

          <!-- Tienda -->
          <select id="filtro-tienda" onchange="aplicarFiltros()" class="bg-[var(--background,#0f172a)] border border-[var(--border,#334155)] rounded-lg px-3 py-1.5 text-sm text-[var(--foreground,#f8fafc)]">
            <option value="Todas">Todas las Tiendas</option>
            <option value="Bodegas Alianza">Bodegas Alianza</option>
            <option value="Sam's Club">Sam's Club</option>
          </select>

          <!-- Checkbox Descuento -->
          <label class="flex items-center gap-1.5 text-xs text-[var(--muted-foreground,#94a3b8)] cursor-pointer">
            <input type="checkbox" id="filtro-descuento" onchange="aplicarFiltros()" class="rounded border-[var(--border,#334155)] text-emerald-500">
            <span>Solo ofertas</span>
          </label>
        </div>

        <div class="text-xs text-[var(--muted-foreground,#94a3b8)]" id="contador-filtrados">
          Mostrando productos
        </div>
      </div>

      <!-- GRÁFICO SVG TOP RANKING $/LITRO DE LA CATEGORÍA COMPARABLE -->
      <div class="bg-[var(--card,#1e293b)] border border-[var(--border,#334155)] rounded-xl p-5 shadow-sm">
        <div class="flex flex-col sm:flex-row justify-between sm:items-center gap-2 mb-4">
          <div>
            <h3 class="font-semibold text-base text-[var(--foreground,#f8fafc)] flex items-center gap-2">
              <span id="chart-titulo">Ranking $/Litro: Tequila - Añejo Cristalino</span>
            </h3>
            <p class="text-xs text-[var(--muted-foreground,#94a3b8)]">Comparativa estricta normalizada a 1,000 ml dentro de la misma clase</p>
          </div>
          <span class="badge bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs self-start sm:self-auto">Menor $/L = Mayor Rendimiento</span>
        </div>
        <div id="chart-container" class="w-full overflow-x-auto">
          <!-- Renderizado dinámico de barras SVG -->
        </div>
      </div>

      <!-- TABLA DINÁMICA DE PRODUCTOS -->
      <div class="bg-[var(--card,#1e293b)] border border-[var(--border,#334155)] rounded-xl shadow-sm overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-left text-sm">
            <thead class="bg-[var(--background,#0f172a)] text-[var(--muted-foreground,#94a3b8)] text-xs uppercase border-b border-[var(--border,#334155)]">
              <tr>
                <th class="p-3">Producto</th>
                <th class="p-3">Categoría Comparable</th>
                <th class="p-3">Presentación</th>
                <th class="p-3 cursor-pointer hover:text-emerald-400" onclick="ordenarPor('precio_promo')">Precio Promo ↕</th>
                <th class="p-3 cursor-pointer hover:text-emerald-400" onclick="ordenarPor('precio_por_litro')">Precio / Litro ↕</th>
                <th class="p-3">Ahorro</th>
                <th class="p-3">Tienda</th>
                <th class="p-3 text-center">Acción</th>
              </tr>
            </thead>
            <tbody id="tabla-productos-body" class="divide-y divide-[var(--border,#334155)]">
              <!-- Filas generadas por JS -->
            </tbody>
          </table>
        </div>
        <div class="p-3 border-t border-[var(--border,#334155)] flex justify-between items-center text-xs text-[var(--muted-foreground,#94a3b8)]">
          <div id="info-paginacion">Mostrando 1 a 20</div>
          <div class="flex gap-2">
            <button onclick="cambiarPagina(-1)" id="btn-prev" class="px-2.5 py-1 rounded bg-[var(--background,#0f172a)] border border-[var(--border,#334155)] disabled:opacity-40">Anterior</button>
            <button onclick="cambiarPagina(1)" id="btn-next" class="px-2.5 py-1 rounded bg-[var(--background,#0f172a)] border border-[var(--border,#334155)] disabled:opacity-40">Siguiente</button>
          </div>
        </div>
      </div>

    </div>

    <!-- ========================================================================================= -->
    <!-- TAB 3: HEAD-TO-HEAD VERSUS (CON DETECCIÓN DE COMPATIBILIDAD) -->
    <!-- ========================================================================================= -->
    <div id="tab-versus" class="tab-content space-y-6 hidden">

      <!-- DUELOS RÁPIDOS CLAVE ORGANIZADOS POR CATEGORÍA -->
      <div class="bg-[var(--card,#1e293b)] border border-[var(--border,#334155)] rounded-xl p-4 shadow-sm space-y-3">
        <div class="text-xs text-[var(--muted-foreground,#94a3b8)] font-semibold uppercase">Duelos Clave de la Reunión Familiar (Misma Categoría):</div>
        
        <div class="space-y-2">
          <div class="flex items-center gap-2 text-xs text-amber-400 font-semibold">
            <span>🥃 Duelos de Tequila Añejo Cristalino (Base &ge;12m):</span>
          </div>
          <div class="flex flex-wrap gap-2">
            <button onclick="cargarDuelo(0)" class="badge bg-amber-500/20 text-amber-300 border border-amber-500/40 hover:bg-amber-500/30 p-2 text-xs">
              1800 Cristalino ($600) vs Maestro Dobel Diamante ($655)
            </button>
            <button onclick="cargarDuelo(1)" class="badge bg-amber-500/20 text-amber-300 border border-amber-500/40 hover:bg-amber-500/30 p-2 text-xs">
              1800 Cristalino ($600) vs Don Julio 70 ($778)
            </button>
            <button onclick="cargarDuelo(6)" class="badge bg-amber-500/20 text-amber-300 border border-amber-500/40 hover:bg-amber-500/30 p-2 text-xs">
              Herradura Ultra ($623) vs Don Julio 70 ($778)
            </button>
          </div>
        </div>

        <div class="space-y-2 pt-1 border-t border-[var(--border,#334155)]">
          <div class="flex items-center gap-2 text-xs text-amber-400 font-semibold">
            <span>🪵 Duelos de Tequila Añejo Tradicional (Madera Natural):</span>
          </div>
          <div class="flex flex-wrap gap-2">
            <button onclick="cargarDuelo(2)" class="badge bg-amber-500/20 text-amber-300 border border-amber-500/40 hover:bg-amber-500/30 p-2 text-xs">
              1800 Añejo Tradicional ($599) vs Tres Generaciones Añejo ($567)
            </button>
            <button onclick="cargarDuelo(7)" class="badge bg-amber-500/20 text-amber-300 border border-amber-500/40 hover:bg-amber-500/30 p-2 text-xs">
              Tres Generaciones Añejo ($567) vs Herradura Añejo ($777)
            </button>
          </div>
        </div>

        <div class="space-y-2 pt-1 border-t border-[var(--border,#334155)]">
          <div class="flex items-center gap-2 text-xs text-emerald-400 font-semibold">
            <span>🌵 Duelos de Mezcal:</span>
          </div>
          <div class="flex flex-wrap gap-2">
            <button onclick="cargarDuelo(3)" class="badge bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 hover:bg-emerald-500/30 p-2 text-xs">
              Amarás Reposado ($503) vs 400 Conejos Reposado ($650)
            </button>
            <button onclick="cargarDuelo(8)" class="badge bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 hover:bg-emerald-500/30 p-2 text-xs">
              Ojo de Tigre Reposado ($616) vs 400 Conejos Reposado ($650)
            </button>
          </div>
        </div>

        <div class="space-y-2 pt-1 border-t border-[var(--border,#334155)]">
          <div class="flex items-center gap-2 text-xs text-blue-400 font-semibold">
            <span>🥃 Whisky y Vino:</span>
          </div>
          <div class="flex flex-wrap gap-2">
            <button onclick="cargarDuelo(4)" class="badge bg-blue-500/20 text-blue-300 border border-blue-500/40 hover:bg-blue-500/30 p-2 text-xs">
              JW Red Label 1.75L (Sam's $627) vs 700ml (Alianza $275)
            </button>
            <button onclick="cargarDuelo(5)" class="badge bg-red-500/20 text-red-300 border border-red-500/40 hover:bg-red-500/30 p-2 text-xs">
              California Tetra Pak ($83) vs Carlo Rossi Garrafa 4L ($437)
            </button>
          </div>
        </div>

      </div>

      <!-- SELECTORES MANUALES -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="bg-[var(--card,#1e293b)] border border-blue-500/30 rounded-xl p-4 shadow-sm">
          <label class="block text-xs font-semibold text-blue-400 mb-1">Seleccionar Producto A:</label>
          <select id="select-versus-a" onchange="actualizarVersusManual()" class="w-full bg-[var(--background,#0f172a)] border border-[var(--border,#334155)] rounded-lg p-2 text-sm text-[var(--foreground,#f8fafc)]">
          </select>
        </div>
        <div class="bg-[var(--card,#1e293b)] border border-purple-500/30 rounded-xl p-4 shadow-sm">
          <label class="block text-xs font-semibold text-purple-400 mb-1">Seleccionar Producto B:</label>
          <select id="select-versus-b" onchange="actualizarVersusManual()" class="w-full bg-[var(--background,#0f172a)] border border-[var(--border,#334155)] rounded-lg p-2 text-sm text-[var(--foreground,#f8fafc)]">
          </select>
        </div>
      </div>

      <!-- BANNER DE COMPATIBILIDAD CATEGÓRICA -->
      <div id="versus-alerta-compatibilidad">
      </div>

      <!-- TARJETAS LADO A LADO -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6" id="versus-tarjetas-container">
      </div>

      <!-- VEREDICTO DE INTELIGENCIA DE NEGOCIO (BI VERDICT) -->
      <div id="versus-veredicto-box" class="bg-[var(--card,#1e293b)] border border-emerald-500/40 rounded-2xl p-6 shadow-sm">
      </div>

    </div>

    <!-- ========================================================================================= -->
    <!-- TAB 4: RÚBRICA Y GUÍA DE CLASES NORMATIVAS (NOM) -->
    <!-- ========================================================================================= -->
    <div id="tab-matriz" class="tab-content space-y-6 hidden">
      <div class="bg-[var(--card,#1e293b)] border border-[var(--border,#334155)] rounded-xl p-6 shadow-sm space-y-6">
        <div>
          <h3 class="text-xl font-bold text-[var(--foreground,#f8fafc)]">Guía Técnica de Clases: ¿Por qué NO Comparar por Precio entre Ellas?</h3>
          <p class="text-sm text-[var(--muted-foreground,#94a3b8)] mt-1">
            Diferencias normativas y de costo de barrica según la NOM-006-SCFI-2012 y NOM-070-SCFI-2016.
          </p>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-left text-sm">
            <thead class="bg-[var(--background,#0f172a)] text-[var(--muted-foreground,#94a3b8)] text-xs uppercase border-b border-[var(--border,#334155)]">
              <tr>
                <th class="p-3">Clase Normativa</th>
                <th class="p-3">Tiempo en Barrica</th>
                <th class="p-3">Proceso de Filtración</th>
                <th class="p-3">Costo de Producción</th>
                <th class="p-3">Perfil Sensorial</th>
                <th class="p-3">Ejemplos Emblemáticos</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-[var(--border,#334155)] text-xs">
              <tr>
                <td class="p-3 font-semibold text-amber-400">Tequila Añejo Cristalino</td>
                <td class="p-3">&ge; 12 meses en barricas de roble de máx. 600L</td>
                <td class="p-3">Filtración con carbón activado para retirar pigmentos</td>
                <td class="p-3 text-red-400 font-medium">Alto (12m barrica + merma + filtración)</td>
                <td class="p-3">Transparente, sumamente suave, notas de vainilla y madera sutil</td>
                <td class="p-3">1800 Cristalino, Maestro Dobel Diamante, Don Julio 70, Herradura Ultra</td>
              </tr>
              <tr>
                <td class="p-3 font-semibold text-amber-400">Tequila Añejo Tradicional</td>
                <td class="p-3">&ge; 12 meses en barricas de roble de máx. 600L</td>
                <td class="p-3">Sin clarificar (filtración estándar por celulosa)</td>
                <td class="p-3 text-amber-400 font-medium">Alto (12m barrica + merma de evaporación)</td>
                <td class="p-3">Color ámbar profundo, taninos directos, madera, frutos secos</td>
                <td class="p-3">Tres Generaciones Añejo, 1800 Añejo, Herradura Añejo</td>
              </tr>
              <tr>
                <td class="p-3 font-semibold text-blue-400">Tequila Reposado Cristalino</td>
                <td class="p-3">2 a 11 meses en pipones o barricas</td>
                <td class="p-3">Filtración con carbón activado</td>
                <td class="p-3 text-emerald-400 font-medium">Medio-Bajo (Ahorro de 10 meses de barrica)</td>
                <td class="p-3">Transparente, ligero, menor complejidad de madera</td>
                <td class="p-3">Gran Centenario Ultra Reposado, Cuervo Tradicional Cristalino, Mayorazgo</td>
              </tr>
              <tr>
                <td class="p-3 font-semibold text-emerald-400">Mezcal Reposado</td>
                <td class="p-3">2 a 11 meses en recipientes de madera</td>
                <td class="p-3">Artesanal / Tradicional</td>
                <td class="p-3 text-emerald-400 font-medium">Medio</td>
                <td class="p-3">Humo suave, agave cocido matizado con roble ligero</td>
                <td class="p-3">Amarás Reposado, 400 Conejos Reposado, Ojo de Tigre Reposado</td>
              </tr>
              <tr>
                <td class="p-3 font-semibold text-emerald-400">Mezcal Añejo</td>
                <td class="p-3">&ge; 12 meses en recipientes de madera de máx. 1000L</td>
                <td class="p-3">Artesanal / Tradicional</td>
                <td class="p-3 text-red-400 font-medium">Alto (Merma prolongada en palenque)</td>
                <td class="p-3">Madera profunda, tabaco, cacao, humo elegante</td>
                <td class="p-3">400 Conejos Añejo, Benevá Añejo, Señorío Añejo</td>
              </tr>
              <tr>
                <td class="p-3 font-semibold text-purple-400">Mezcal Silvestre</td>
                <td class="p-3">Joven (sin barrica, maduración en planta de 12 a 25 años)</td>
                <td class="p-3">Horno cónico de tierra y alambique de cobre/barro</td>
                <td class="p-3 text-purple-400 font-medium">Muy Alto en materia prima silvestre</td>
                <td class="p-3">Notas minerales, herbales, terrosas e intensas</td>
                <td class="p-3">Amarás Cupreata, 400 Conejos Tobalá/Cuishe, Tierra Mestiza Tepeztate</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="pt-4 border-t border-[var(--border,#334155)] space-y-4">
          <h4 class="font-bold text-base text-[var(--foreground,#f8fafc)]">Ponderación de la Rúbrica Familiar</h4>
          <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div class="bg-[var(--background,#0f172a)] border border-[var(--border,#334155)] rounded-xl p-4">
              <div class="text-amber-400 text-2xl font-bold">30%</div>
              <div class="font-semibold text-sm mt-1">Afinidad Familiar</div>
              <p class="text-xs text-[var(--muted-foreground,#94a3b8)] mt-1">Aceptación de los ~60 asistentes en mesa navideña.</p>
            </div>
            <div class="bg-[var(--background,#0f172a)] border border-[var(--border,#334155)] rounded-xl p-4">
              <div class="text-blue-400 text-2xl font-bold">30%</div>
              <div class="font-semibold text-sm mt-1">Pureza y Proceso</div>
              <p class="text-xs text-[var(--muted-foreground,#94a3b8)] mt-1">Ausencia de aditivos artificiales, triple destilación o métodos tradicionales.</p>
            </div>
            <div class="bg-[var(--border,#334155)] border border-[var(--border,#334155)] rounded-xl p-4">
              <div class="text-emerald-400 text-2xl font-bold">20%</div>
              <div class="font-semibold text-sm mt-1">Precio por Litro ($/L)</div>
              <p class="text-xs text-[var(--muted-foreground,#94a3b8)] mt-1">Evaluado <strong>estrictamente dentro de su misma clase</strong>.</p>
            </div>
            <div class="bg-[var(--background,#0f172a)] border border-[var(--border,#334155)] rounded-xl p-4">
              <div class="text-purple-400 text-2xl font-bold">20%</div>
              <div class="font-semibold text-sm mt-1">Reputación y Prestigio</div>
              <p class="text-xs text-[var(--muted-foreground,#94a3b8)] mt-1">Seriedad de la destilería y presencia en mesa.</p>
            </div>
          </div>
        </div>

      </div>
    </div>

  </div>

  <!-- SCRIPT REACTIVO DEL DASHBOARD -->
  <script>
    const DATOS_COMPLETOS = {datos_json_str};

    let datosFiltrados = [...DATOS_COMPLETOS];
    let paginaActual = 1;
    const itemsPorPagina = 20;
    let columnaOrden = 'precio_por_litro';
    let ordenAsc = true;

    // Presupuesto y cooperadores reactivos
    let PRESUPUESTO_OBJETIVO = 9000.00;
    let COOPERADORES_TOTAL = 14;

    const DUELOS_PRECARGADOS = [
      {{ a: "Tequila 1800 Añejo Cristalino 100% 700 ml", b: "Tequila Cristalino Maestro Dobel Diamante 700 ml" }},
      {{ a: "Tequila 1800 Añejo Cristalino 100% 700 ml", b: "Tequila Añejo Cristalino Don Julio 70 700 ml" }},
      {{ a: "Tequila 1800 Añejo 100% Agave", b: "Tequila Tres Generaciones Añejo 750 ml 100% Agave Azul" }},
      {{ a: "Mezcal Amarás Rep Espadín 750 ml", b: "Mezcal 400 Conejos Reposado 700 ml" }},
      {{ a: "Whisky Johnnie Walker Red Label", b: "Whisky Johnnie Walker Red Label Blended Scotch 700 ml" }},
      {{ a: "Vino Tinto California (Tetra Pak)", b: "Vino Tinto Carlo Rossi Red Blend" }},
      {{ a: "Tequila Herradura Ultra Añejo Cristalino 700 ml", b: "Tequila Añejo Cristalino Don Julio 70 700 ml" }},
      {{ a: "Tequila Tres Generaciones Añejo 750 ml 100% Agave Azul", b: "Tequila Herradura Añejo 750ml 100% Agave Azul" }},
      {{ a: "Mezcal Artesanal Ojo De Tigre Reposado 750 ml", b: "Mezcal 400 Conejos Reposado 700 ml" }}
    ];

    document.addEventListener("DOMContentLoaded", () => {{
      poblarSelectoresVersus();
      aplicarFiltros();
      cargarDuelo(0);
      actualizarParametrosGlobales();
    }});

    function actualizarParametrosGlobales() {{
      const p = parseFloat(document.getElementById("input-presupuesto").value);
      const c = parseInt(document.getElementById("input-cooperadores").value);

      if (p && p > 0) PRESUPUESTO_OBJETIVO = p;
      if (c && c > 0) COOPERADORES_TOTAL = c;

      // Actualizar badges
      document.getElementById("badge-cooperadores-resumen").innerText = `${{COOPERADORES_TOTAL}} Cooperadores`;
      document.getElementById("sim-subtitulo-cuota").innerText = `Dividido exactamente entre ${{COOPERADORES_TOTAL}} personas`;

      // Actualizar cuotas de presets
      document.getElementById("preset-1-cuota").innerText = `~$${{(5983.85 / COOPERADORES_TOTAL).toFixed(2)}} por persona`;
      document.getElementById("preset-2-cuota").innerText = `~$${{(6648.45 / COOPERADORES_TOTAL).toFixed(2)}} por persona`;
      document.getElementById("preset-3-cuota").innerText = `~$${{(7078.35 / COOPERADORES_TOTAL).toFixed(2)}} por persona`;
      document.getElementById("preset-4-cuota").innerText = `~$${{(7613.35 / COOPERADORES_TOTAL).toFixed(2)}} por persona`;

      recalcularSimulador();
    }}

    function cargarPreset(tipo) {{
      if (tipo === 'ahorro') {{
        document.getElementById("sim-cristalino").value = "1800_cristalino";
        document.getElementById("sim-anejo").value = "tres_generaciones";
        document.getElementById("sim-mezcal").value = "canasta_a";
        document.getElementById("sim-whisky").value = "jw_red_175_sams";
        document.getElementById("sim-honey").value = "honey_2_alianza";
        document.getElementById("sim-vino").value = "tetra_california";
      }} else if (tipo === 'balanceada') {{
        document.getElementById("sim-cristalino").value = "1800_cristalino";
        document.getElementById("sim-anejo").value = "1800_anejo";
        document.getElementById("sim-mezcal").value = "canasta_a";
        document.getElementById("sim-whisky").value = "jw_red_175_sams";
        document.getElementById("sim-honey").value = "honey_2_alianza";
        document.getElementById("sim-vino").value = "tetra_california";
      }} else if (tipo === 'silvestre') {{
        document.getElementById("sim-cristalino").value = "1800_cristalino";
        document.getElementById("sim-anejo").value = "1800_anejo";
        document.getElementById("sim-mezcal").value = "canasta_b";
        document.getElementById("sim-whisky").value = "jw_red_175_sams";
        document.getElementById("sim-honey").value = "honey_3_alianza";
        document.getElementById("sim-vino").value = "tetra_california";
      }} else if (tipo === 'gala') {{
        document.getElementById("sim-cristalino").value = "mix_2_1800_1_dj70";
        document.getElementById("sim-anejo").value = "herradura_anejo";
        document.getElementById("sim-mezcal").value = "canasta_b";
        document.getElementById("sim-whisky").value = "jw_red_175_sams";
        document.getElementById("sim-honey").value = "honey_3_alianza";
        document.getElementById("sim-vino").value = "carlo_rossi_combo";
      }}
      recalcularSimulador();
    }}

    function recalcularSimulador() {{
      const selCristalino = document.getElementById("sim-cristalino").value;
      const selAnejo = document.getElementById("sim-anejo").value;
      const selMezcal = document.getElementById("sim-mezcal").value;
      const selWhisky = document.getElementById("sim-whisky").value;
      const selHoney = document.getElementById("sim-honey").value;
      const selVino = document.getElementById("sim-vino").value;

      let subAlianza = 0;
      let subSams = 0;

      let costoCrist = 0;
      let costoAnejo = 0;
      let costoMezcal = 0;
      let costoWhisky = 0;
      let costoHoney = 0;
      let costoVino = 0;

      // 1. Cristalino
      if (selCristalino === "1800_cristalino") costoCrist = 1800.00;
      else if (selCristalino === "dobel_diamante") costoCrist = 1965.00;
      else if (selCristalino === "herradura_ultra") costoCrist = 1869.00;
      else if (selCristalino === "don_julio_70") costoCrist = 2334.00;
      else if (selCristalino === "mix_2_1800_1_dj70") costoCrist = 1978.00;
      else if (selCristalino === "tezona_cristalino") costoCrist = 1659.00;
      subAlianza += costoCrist;
      document.getElementById("costo-item-cristalino").innerText = `$${{costoCrist.toFixed(2)}}`;

      // 2. Añejo
      if (selAnejo === "1800_anejo") costoAnejo = 599.25;
      else if (selAnejo === "tres_generaciones") costoAnejo = 567.00;
      else if (selAnejo === "hornitos_black") costoAnejo = 451.50;
      else if (selAnejo === "herradura_anejo") costoAnejo = 777.00;
      else if (selAnejo === "jimador_anejo") costoAnejo = 357.00;
      subAlianza += costoAnejo;
      document.getElementById("costo-item-anejo").innerText = `$${{costoAnejo.toFixed(2)}}`;

      // 3. Mezcal
      if (selMezcal === "canasta_a") costoMezcal = 1674.10;
      else if (selMezcal === "canasta_b") costoMezcal = 1890.00;
      else if (selMezcal === "canasta_c") costoMezcal = 1900.00;
      else if (selMezcal === "canasta_d") costoMezcal = 1569.80;
      subAlianza += costoMezcal;
      document.getElementById("costo-item-mezcal").innerText = `$${{costoMezcal.toFixed(2)}}`;

      // 4. Whisky
      if (selWhisky === "jw_red_175_sams") {{ costoWhisky = 627.10; subSams += costoWhisky; }}
      else if (selWhisky === "jw_red_700_alianza") {{ costoWhisky = 550.00; subAlianza += costoWhisky; }}
      else if (selWhisky === "ballantines_2x") {{ costoWhisky = 457.50; subAlianza += costoWhisky; }}
      else if (selWhisky === "william_lawsons_2l") {{ costoWhisky = 470.00; subAlianza += costoWhisky; }}
      document.getElementById("costo-item-whisky").innerText = `$${{costoWhisky.toFixed(2)}}`;

      // 5. Honey
      if (selHoney === "honey_2_alianza") {{ costoHoney = 756.00; subAlianza += costoHoney; }}
      else if (selHoney === "honey_3_alianza") {{ costoHoney = 1134.00; subAlianza += costoHoney; }}
      else if (selHoney === "honey_2_sams") {{ costoHoney = 1125.30; subSams += costoHoney; }}
      document.getElementById("costo-item-honey").innerText = `$${{costoHoney.toFixed(2)}}`;

      // 6. Vino
      if (selVino === "tetra_california") {{ costoVino = 415.00; subAlianza += costoVino; }}
      else if (selVino === "carlo_rossi_combo") {{ costoVino = 520.83; subSams += 437.83; subAlianza += 83.00; }}
      else if (selVino === "concha_toro_5x") {{ costoVino = 451.50; subAlianza += costoVino; }}
      document.getElementById("costo-item-vino").innerText = `$${{costoVino.toFixed(2)}}`;

      const granTotal = subAlianza + subSams;
      const cuota = granTotal / COOPERADORES_TOTAL;
      const sobrante = PRESUPUESTO_OBJETIVO - granTotal;
      const porcentajeUso = Math.min(100, (granTotal / PRESUPUESTO_OBJETIVO) * 100);

      document.getElementById("sim-total-alianza").innerText = `$${{subAlianza.toLocaleString('es-MX', {{minimumFractionDigits: 2, maximumFractionDigits: 2}})}}`;
      document.getElementById("sim-total-sams").innerText = `$${{subSams.toLocaleString('es-MX', {{minimumFractionDigits: 2, maximumFractionDigits: 2}})}}`;
      document.getElementById("sim-gran-total").innerText = `$${{granTotal.toLocaleString('es-MX', {{minimumFractionDigits: 2, maximumFractionDigits: 2}})}}`;
      document.getElementById("sim-cuota-persona").innerText = `$${{cuota.toLocaleString('es-MX', {{minimumFractionDigits: 2, maximumFractionDigits: 2}})}}`;
      
      // Barra y KPI
      document.getElementById("sim-porcentaje-barra").innerText = `${{porcentajeUso.toFixed(1)}}%`;
      document.getElementById("sim-barra-dinamica").style.width = `${{porcentajeUso}}%`;
      document.getElementById("kpi-cuota-global").innerText = `$${{cuota.toFixed(2)}}`;
      document.getElementById("kpi-porcentaje-uso").innerText = `${{porcentajeUso.toFixed(1)}}%`;
      document.getElementById("kpi-barra-presupuesto").style.width = `${{porcentajeUso}}%`;

      const alertaBox = document.getElementById("sim-alerta-sobrante");
      const labelSobrante = document.getElementById("sim-label-sobrante");
      const valSobrante = document.getElementById("sim-sobrante");

      if (sobrante >= 0) {{
        alertaBox.className = "p-3 rounded-lg flex items-center justify-between text-xs bg-emerald-950/30 border border-emerald-500/30";
        labelSobrante.innerText = "Dinero Sobrante del Presupuesto:";
        labelSobrante.className = "text-emerald-300 font-medium";
        valSobrante.innerText = `+$${{sobrante.toLocaleString('es-MX', {{minimumFractionDigits: 2, maximumFractionDigits: 2}})}}`;
        valSobrante.className = "text-emerald-400 font-bold text-sm font-mono";
        document.getElementById("kpi-sobrante-global").innerText = `Sobrante: +$${{sobrante.toFixed(2)}} MXN`;
        document.getElementById("kpi-sobrante-global").className = "text-xs text-emerald-400 mt-1";
      }} else {{
        alertaBox.className = "p-3 rounded-lg flex items-center justify-between text-xs bg-red-950/40 border border-red-500/50";
        labelSobrante.innerText = "⚠️ Excede el Presupuesto por:";
        labelSobrante.className = "text-red-300 font-bold";
        valSobrante.innerText = `-$${{Math.abs(sobrante).toLocaleString('es-MX', {{minimumFractionDigits: 2, maximumFractionDigits: 2}})}}`;
        valSobrante.className = "text-red-400 font-black text-sm font-mono";
        document.getElementById("kpi-sobrante-global").innerText = `Excede por: -$${{Math.abs(sobrante).toFixed(2)}} MXN`;
        document.getElementById("kpi-sobrante-global").className = "text-xs text-red-400 mt-1";
      }}
    }}

    function cambiarTab(idTab) {{
      document.querySelectorAll(".tab-content").forEach(el => el.classList.add("hidden"));
      document.querySelectorAll(".tab-btn").forEach(el => {{
        el.classList.remove("border-emerald-500", "text-emerald-400", "bg-[var(--card,#1e293b)]");
        el.classList.add("border-transparent", "text-[var(--muted-foreground,#94a3b8)]");
      }});

      document.getElementById(idTab).classList.remove("hidden");
      const btn = document.getElementById("btn-" + idTab);
      btn.classList.add("border-emerald-500", "text-emerald-400", "bg-[var(--card,#1e293b)]");
      btn.classList.remove("border-transparent", "text-[var(--muted-foreground,#94a3b8)]");

      if (idTab === 'tab-rankings') {{
        renderizarGraficoTop10();
      }}
    }}

    function aplicarFiltros() {{
      const busq = document.getElementById("filtro-busqueda").value.toLowerCase();
      const catComp = document.getElementById("filtro-categoria").value;
      const tienda = document.getElementById("filtro-tienda").value;
      const soloDesc = document.getElementById("filtro-descuento").checked;

      datosFiltrados = DATOS_COMPLETOS.filter(item => {{
        const matchBusq = !busq || item.producto.toLowerCase().includes(busq) || item.marca.toLowerCase().includes(busq);
        const matchCat = (catComp === 'Todas') || (item.categoria_comparable === catComp);
        const matchTienda = (tienda === 'Todas') || (item.tienda === tienda);
        const matchDesc = !soloDesc || (item.ahorro_verificable > 0);
        return matchBusq && matchCat && matchTienda && matchDesc;
      }});

      datosFiltrados.sort((a, b) => {{
        let vA = a[columnaOrden] || 0;
        let vB = b[columnaOrden] || 0;
        return ordenAsc ? vA - vB : vB - vA;
      }});

      paginaActual = 1;
      renderizarTabla();
      renderizarGraficoTop10();
      document.getElementById("contador-filtrados").innerText = `Mostrando ${{datosFiltrados.length}} productos validados`;
      document.getElementById("chart-titulo").innerText = `Ranking $/Litro: ${{catComp}}`;
    }}

    function ordenarPor(col) {{
      if (columnaOrden === col) ordenAsc = !ordenAsc;
      else {{ columnaOrden = col; ordenAsc = true; }}
      aplicarFiltros();
    }}

    function renderizarTabla() {{
      const tbody = document.getElementById("tabla-productos-body");
      tbody.innerHTML = "";

      const inicio = (paginaActual - 1) * itemsPorPagina;
      const fin = Math.min(inicio + itemsPorPagina, datosFiltrados.length);
      const paginaItems = datosFiltrados.slice(inicio, fin);

      if (paginaItems.length === 0) {{
        tbody.innerHTML = `<tr><td colspan="8" class="p-8 text-center text-[var(--muted-foreground,#94a3b8)]">No se encontraron productos en esta categoría comparable.</td></tr>`;
        return;
      }}

      paginaItems.forEach(item => {{
        const tr = document.createElement("tr");
        tr.className = "hover:bg-[var(--background,#0f172a)]/50 transition-colors";

        const ahorroBadge = item.ahorro_verificable > 0 
          ? `<span class="badge bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">-$${{item.ahorro_verificable.toFixed(2)}} (${{item.porcentaje_ahorro}}%)</span>`
          : `<span class="text-[var(--muted-foreground,#94a3b8)] text-xs">Regular</span>`;

        const tiendaBadge = item.tienda === "Sam's Club"
          ? `<span class="badge bg-blue-500/10 text-blue-400 border border-blue-500/20">Sam's Club</span>`
          : `<span class="badge bg-amber-500/10 text-amber-400 border border-amber-500/20">Alianza</span>`;

        tr.innerHTML = `
          <td class="p-3 font-medium text-[var(--foreground,#f8fafc)]">
            <div class="line-clamp-1">${{item.producto}}</div>
            <div class="text-xs text-[var(--muted-foreground,#94a3b8)]">${{item.marca}}</div>
          </td>
          <td class="p-3 text-xs">
            <span class="badge bg-[var(--background,#0f172a)] border border-[var(--border,#334155)] text-[var(--foreground,#f8fafc)]">${{item.categoria_comparable}}</span>
          </td>
          <td class="p-3 text-xs font-mono">${{item.ml}} ml</td>
          <td class="p-3 font-semibold text-emerald-400 font-mono">$${{item.precio_promo.toFixed(2)}}</td>
          <td class="p-3 font-bold text-amber-400 font-mono">$${{item.precio_por_litro.toFixed(2)}}</td>
          <td class="p-3">${{ahorroBadge}}</td>
          <td class="p-3">${{tiendaBadge}}</td>
          <td class="p-3 text-center">
            <a href="${{item.url}}" target="_blank" class="px-2 py-1 text-xs rounded bg-[var(--background,#0f172a)] border border-[var(--border,#334155)] hover:border-emerald-500 text-[var(--foreground,#f8fafc)]">
              Ver ↗
            </a>
          </td>
        `;
        tbody.appendChild(tr);
      }});

      document.getElementById("info-paginacion").innerText = `Mostrando ${{inicio + 1}} - ${{fin}} de ${{datosFiltrados.length}}`;
      document.getElementById("btn-prev").disabled = paginaActual === 1;
      document.getElementById("btn-next").disabled = fin >= datosFiltrados.length;
    }}

    function cambiarPagina(delta) {{
      paginaActual += delta;
      renderizarTabla();
    }}

    function renderizarGraficoTop10() {{
      const container = document.getElementById("chart-container");
      const top10 = datosFiltrados.slice(0, 10);
      if (top10.length === 0) {{
        container.innerHTML = "<div class='text-xs text-[var(--muted-foreground,#94a3b8)] p-4'>Sin datos para graficar</div>";
        return;
      }}

      const maxLitro = Math.max(...top10.map(d => d.precio_por_litro));

      let svgHtml = `<div class="space-y-2 py-2">`;
      top10.forEach((item, idx) => {{
        const anchoPorcentaje = Math.max(15, (item.precio_por_litro / maxLitro) * 100);
        const colorBarra = idx === 0 ? "bg-emerald-500" : (idx < 3 ? "bg-emerald-400/80" : "bg-blue-400/70");

        svgHtml += `
          <div class="space-y-0.5">
            <div class="flex justify-between text-xs">
              <span class="font-medium truncate max-w-md">${{idx + 1}}. ${{item.producto}} (${{item.tienda}})</span>
              <span class="font-bold font-mono text-amber-300">$${{item.precio_por_litro.toFixed(2)}} / L</span>
            </div>
            <div class="w-full bg-[var(--background,#0f172a)] h-3 rounded-full overflow-hidden border border-[var(--border,#334155)]/50">
              <div class="${{colorBarra}} h-full rounded-full transition-all duration-500" style="width: ${{anchoPorcentaje}}%"></div>
            </div>
          </div>
        `;
      }});
      svgHtml += `</div>`;
      container.innerHTML = svgHtml;
    }}

    function poblarSelectoresVersus() {{
      const selA = document.getElementById("select-versus-a");
      const selB = document.getElementById("select-versus-b");
      selA.innerHTML = "";
      selB.innerHTML = "";

      DATOS_COMPLETOS.forEach((item, idx) => {{
        const label = `[${{item.categoria_comparable}}] ${{item.producto}} ($${{item.precio_promo.toFixed(2)}} | $${{item.precio_por_litro.toFixed(2)}}/L)`;
        const optA = new Option(label, idx);
        const optB = new Option(label, idx);
        selA.add(optA);
        selB.add(optB);
      }});
    }}

    function cargarDuelo(indexDuelo) {{
      const duelo = DUELOS_PRECARGADOS[indexDuelo];
      if (!duelo) return;

      const idxA = DATOS_COMPLETOS.findIndex(d => d.producto.includes(duelo.a) || duelo.a.includes(d.producto));
      const idxB = DATOS_COMPLETOS.findIndex(d => d.producto.includes(duelo.b) || duelo.b.includes(d.producto));

      if (idxA !== -1) document.getElementById("select-versus-a").value = idxA;
      if (idxB !== -1) document.getElementById("select-versus-b").value = idxB;

      renderizarVersus();
    }}

    function actualizarVersusManual() {{
      renderizarVersus();
    }}

    function renderizarVersus() {{
      const idxA = parseInt(document.getElementById("select-versus-a").value) || 0;
      const idxB = parseInt(document.getElementById("select-versus-b").value) || 1;

      const itemA = DATOS_COMPLETOS[idxA];
      const itemB = DATOS_COMPLETOS[idxB];

      const bannerAlerta = document.getElementById("versus-alerta-compatibilidad");
      if (itemA.categoria_comparable === itemB.categoria_comparable) {{
        bannerAlerta.innerHTML = `
          <div class="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 text-xs font-semibold flex items-center gap-2">
            <span>✅ Comparación Homogénea (Regla 6 Cumplida):</span>
            <span class="text-[var(--foreground,#f8fafc)]">Ambos pertenecen a '${{itemA.categoria_comparable}}'. La diferencia en $/L refleja eficiencia directa de precio.</span>
          </div>
        `;
      }} else {{
        bannerAlerta.innerHTML = `
          <div class="p-4 bg-amber-500/15 border border-amber-500/40 rounded-xl text-amber-200 text-xs leading-relaxed space-y-1">
            <div class="font-bold flex items-center gap-1.5 text-amber-300">
              <span>⚠️ ALERTA METODOLÓGICA: Comparación entre Categorías Técnicamente Distintas</span>
            </div>
            <div>
              Estás comparando <strong>${{itemA.categoria_comparable}}</strong> frente a <strong>${{itemB.categoria_comparable}}</strong>.
              El menor precio de uno no indica necesariamente mayor ahorro comercial, sino <strong>menor tiempo de barrica o proceso diferente</strong> (ej. 2 a 11 meses de barrica vs más de 12 meses).
            </div>
          </div>
        `;
      }}

      const cont = document.getElementById("versus-tarjetas-container");
      cont.innerHTML = `
        <div class="bg-[var(--card,#1e293b)] border-2 border-blue-500/50 rounded-2xl p-6 shadow-sm space-y-4 relative">
          <div class="flex justify-between items-start">
            <div>
              <span class="badge bg-blue-500/20 text-blue-400 border border-blue-500/30 text-[11px]">${{itemA.categoria_comparable}}</span>
              <h4 class="text-xl font-bold text-[var(--foreground,#f8fafc)] mt-2">${{itemA.producto}}</h4>
              <div class="text-xs text-blue-400 mt-0.5">${{itemA.tienda}} (${{itemA.condiciones || 'Catálogo regular'}})</div>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3 bg-[var(--background,#0f172a)] p-3 rounded-xl border border-[var(--border,#334155)]">
            <div>
              <div class="text-xs text-[var(--muted-foreground,#94a3b8)]">Precio Botella</div>
              <div class="text-2xl font-black text-emerald-400 font-mono">$${{itemA.precio_promo.toFixed(2)}}</div>
              <div class="text-[11px] text-[var(--muted-foreground,#94a3b8)]">Reg: $${{itemA.precio_regular.toFixed(2)}}</div>
            </div>
            <div>
              <div class="text-xs text-[var(--muted-foreground,#94a3b8)]">Precio / Litro</div>
              <div class="text-2xl font-black text-amber-400 font-mono">$${{itemA.precio_por_litro.toFixed(2)}}</div>
              <div class="text-[11px] text-[var(--muted-foreground,#94a3b8)] font-mono">${{itemA.ml}} ml</div>
            </div>
          </div>

          <div class="space-y-2 text-xs pt-2 border-t border-[var(--border,#334155)]">
            <div class="font-semibold text-[var(--foreground,#f8fafc)]">Evaluación Técnica de Calidad:</div>
            ${{generarBarrasRubrica(itemA)}}
          </div>
        </div>

        <div class="bg-[var(--card,#1e293b)] border-2 border-purple-500/50 rounded-2xl p-6 shadow-sm space-y-4 relative">
          <div class="flex justify-between items-start">
            <div>
              <span class="badge bg-purple-500/20 text-purple-400 border border-purple-500/30 text-[11px]">${{itemB.categoria_comparable}}</span>
              <h4 class="text-xl font-bold text-[var(--foreground,#f8fafc)] mt-2">${{itemB.producto}}</h4>
              <div class="text-xs text-purple-400 mt-0.5">${{itemB.tienda}} (${{itemB.condiciones || 'Catálogo regular'}})</div>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3 bg-[var(--background,#0f172a)] p-3 rounded-xl border border-[var(--border,#334155)]">
            <div>
              <div class="text-xs text-[var(--muted-foreground,#94a3b8)]">Precio Botella</div>
              <div class="text-2xl font-black text-emerald-400 font-mono">$${{itemB.precio_promo.toFixed(2)}}</div>
              <div class="text-[11px] text-[var(--muted-foreground,#94a3b8)]">Reg: $${{itemB.precio_regular.toFixed(2)}}</div>
            </div>
            <div>
              <div class="text-xs text-[var(--muted-foreground,#94a3b8)]">Precio / Litro</div>
              <div class="text-2xl font-black text-amber-400 font-mono">$${{itemB.precio_por_litro.toFixed(2)}}</div>
              <div class="text-[11px] text-[var(--muted-foreground,#94a3b8)] font-mono">${{itemB.ml}} ml</div>
            </div>
          </div>

          <div class="space-y-2 text-xs pt-2 border-t border-[var(--border,#334155)]">
            <div class="font-semibold text-[var(--foreground,#f8fafc)]">Evaluación Técnica de Calidad:</div>
            ${{generarBarrasRubrica(itemB)}}
          </div>
        </div>
      `;

      generarVeredictoBI(itemA, itemB);
    }}

    function generarBarrasRubrica(item) {{
      const nom = item.producto.toLowerCase();
      let pureza = 85;
      let afinidad = 85;
      let prestigio = 85;

      if (nom.includes("tres generaciones")) {{ pureza = 95; afinidad = 80; prestigio = 90; }}
      else if (nom.includes("don julio 70")) {{ pureza = 85; afinidad = 95; prestigio = 98; }}
      else if (nom.includes("1800 cristalino")) {{ pureza = 85; afinidad = 92; prestigio = 90; }}
      else if (nom.includes("1800 añejo") || nom.includes("1800 anejo")) {{ pureza = 85; afinidad = 90; prestigio = 90; }}
      else if (nom.includes("herradura ultra")) {{ pureza = 90; afinidad = 90; prestigio = 92; }}
      else if (nom.includes("dobel diamante")) {{ pureza = 85; afinidad = 88; prestigio = 90; }}
      else if (nom.includes("amaras")) {{ pureza = 94; afinidad = 80; prestigio = 88; }}
      else if (nom.includes("400 conejos")) {{ pureza = 82; afinidad = 90; prestigio = 85; }}
      else if (nom.includes("ojo de tigre")) {{ pureza = 90; afinidad = 85; prestigio = 85; }}
      else if (nom.includes("red label")) {{ pureza = 80; afinidad = 95; prestigio = 88; }}
      else if (nom.includes("ballantine")) {{ pureza = 88; afinidad = 82; prestigio = 85; }}
      else if (nom.includes("california")) {{ pureza = 75; afinidad = 90; prestigio = 75; }}
      else if (nom.includes("concha y toro")) {{ pureza = 88; afinidad = 85; prestigio = 85; }}
      else if (nom.includes("carlo rossi")) {{ pureza = 80; afinidad = 90; prestigio = 82; }}

      const scorePrecio = Math.min(100, Math.max(50, Math.round(100 - (item.precio_por_litro / 15))));

      return `
        <div>
          <div class="flex justify-between"><span>Afinidad Familiar (30%):</span><span class="font-bold">${{afinidad}}/100</span></div>
          <div class="w-full bg-[var(--background,#0f172a)] h-1.5 rounded-full overflow-hidden mt-0.5"><div class="bg-amber-400 h-full" style="width:${{afinidad}}%"></div></div>
        </div>
        <div>
          <div class="flex justify-between"><span>Pureza y Proceso (30%):</span><span class="font-bold">${{pureza}}/100</span></div>
          <div class="w-full bg-[var(--background,#0f172a)] h-1.5 rounded-full overflow-hidden mt-0.5"><div class="bg-blue-400 h-full" style="width:${{pureza}}%"></div></div>
        </div>
        <div>
          <div class="flex justify-between"><span>Rendimiento $/L (20%):</span><span class="font-bold">${{scorePrecio}}/100</span></div>
          <div class="w-full bg-[var(--background,#0f172a)] h-1.5 rounded-full overflow-hidden mt-0.5"><div class="bg-emerald-400 h-full" style="width:${{scorePrecio}}%"></div></div>
        </div>
        <div>
          <div class="flex justify-between"><span>Reputación de Marca (20%):</span><span class="font-bold">${{prestigio}}/100</span></div>
          <div class="w-full bg-[var(--background,#0f172a)] h-1.5 rounded-full overflow-hidden mt-0.5"><div class="bg-purple-400 h-full" style="width:${{prestigio}}%"></div></div>
        </div>
      `;
    }}

    function generarVeredictoBI(itemA, itemB) {{
      const diffLitro = itemA.precio_por_litro - itemB.precio_por_litro;
      const ganadorPrecio = diffLitro < 0 ? itemA : itemB;
      const perdedorPrecio = diffLitro < 0 ? itemB : itemA;
      const ahorroLitroAbs = Math.abs(diffLitro);
      const porcentajeDiff = ((ahorroLitroAbs / perdedorPrecio.precio_por_litro) * 100).toFixed(1);

      let razonamiento = "";
      const pairKey = [itemA.producto, itemB.producto].join(" ").toLowerCase();
      const mismaCategoria = (itemA.categoria_comparable === itemB.categoria_comparable);

      if (!mismaCategoria) {{
        razonamiento = `
          <strong>Aviso de Comparabilidad:</strong> Estás comparando <em>${{itemA.categoria_comparable}}</em> frente a <em>${{itemB.categoria_comparable}}</em>.
          <br><br>
          ${{ganadorPrecio.producto}} cuesta <strong>$${{ahorroLitroAbs.toFixed(2)}} menos por litro</strong> ($${{ganadorPrecio.precio_por_litro.toFixed(2)}}/L vs $${{perdedorPrecio.precio_por_litro.toFixed(2)}}/L). Sin embargo, <strong>esta diferencia se debe al tiempo y costo de barrica</strong>. Si la reunión busca notas de madera complejas de más de 1 año, un Reposado no es un sustituto organoléptico directo de un Añejo.
        `;
      }} else if (pairKey.includes("1800") && pairKey.includes("don julio 70")) {{
        razonamiento = `
          <strong>Análisis Homogéneo (Añejos Cristalinos &ge;12m):</strong> El <strong>1800 Cristalino ($600)</strong> gana en eficiencia financiera con un ahorro de <strong>$254.29 por litro (22.9% de ahorro)</strong> frente a Don Julio 70 ($778).
          Ambos cumplen el estándar de añejamiento y filtración con carbón activado. En una compra familiar de 3 botellas, elegir 1800 Cristalino genera un <strong>ahorro directo de $534.00 MXN</strong>, suficiente para costear todo el vino tinto de la reunión sin perder el perfil suave que busca la familia.
        `;
      }} else if (pairKey.includes("1800") && pairKey.includes("dobel")) {{
        razonamiento = `
          <strong>Análisis Homogéneo (Añejos Cristalinos &ge;12m):</strong> Ambos provienen de Casa Cuervo (NOM 1122). El <strong>1800 Cristalino ($600)</strong> ofrece una ventaja de <strong>$78.57 por litro (8.4% de ahorro)</strong> frente a Maestro Dobel Diamante ($655). 
          Dobel Diamante ofrece una presentación estéticamente más estilizada, pero la maduración base de 1800 Cristalino es igualmente robusta. 1800 Cristalino es la opción óptima por presupuesto.
        `;
      }} else if (pairKey.includes("1800") && pairKey.includes("tres generaciones")) {{
        razonamiento = `
          <strong>Análisis Homogéneo (Añejos Tradicionales &ge;12m):</strong> <strong>Tres Generaciones Añejo ($567.00 / 750ml)</strong> es superior en relación calidad-precio frente a 1800 Añejo Tradicional ($599.25 / 700ml). Es <strong>$100.07 más barato por litro</strong> y cuenta con <strong>triple destilación en alambique de cobre</strong> (frente a la doble destilación de 1800). Mayor pureza y mayor rendimiento por mililitro.
        `;
      }} else if (pairKey.includes("amaras") && pairKey.includes("400 conejos") && pairKey.includes("rep")) {{
        razonamiento = `
          <strong>Análisis Homogéneo (Mezcales Reposados Artesanales):</strong> <strong>Amarás Reposado Espadín ($503.30)</strong> supera contundentemente a 400 Conejos Reposado ($650.00). Ofrece un <strong>ahorro directo de $257.50 por litro (27.7%)</strong> y proviene de un palenque artesanal independiente en San Juan del Río. Amarás supera a 400 Conejos tanto en sabor como en rentabilidad.
        `;
      }} else if (pairKey.includes("herradura ultra") && pairKey.includes("don julio 70")) {{
        razonamiento = `
          <strong>Análisis Homogéneo (Añejos Cristalinos &ge;12m):</strong> <strong>Herradura Ultra Añejo Cristalino ($623.00)</strong> compite al tú por tú en prestigio frente a Don Julio 70 ($778.00). Ahorra <strong>$221.43 por litro (19.9%)</strong>. Su ensamble de añejo y extra añejo le da un toque sumamente amigable para los asistentes que prefieren bebidas no rasposas.
        `;
      }} else {{
        razonamiento = `
          <strong>Comparativa Dentro de la Categoría:</strong> <strong>${{ganadorPrecio.producto}}</strong> ofrece una ventaja de <strong>$${{ahorroLitroAbs.toFixed(2)}} por litro (${{porcentajeDiff}}% de ahorro)</strong> frente a ${{perdedorPrecio.producto}}.
          <br><br>
          <strong>Recomendación BI:</strong> Dado que ambos pertenecen a la categoría '${{itemA.categoria_comparable}}', ${{ganadorPrecio.producto}} maximiza el retorno por peso invertido sin sacrificar el estándar de maduración requerido.
        `;
      }}

      document.getElementById("versus-veredicto-box").innerHTML = `
        <div class="flex items-start gap-4">
          <div class="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-2xl">💡</div>
          <div class="space-y-2">
            <h4 class="font-bold text-lg text-emerald-400">Veredicto de Inteligencia de Negocio</h4>
            <div class="text-sm text-[var(--foreground,#f8fafc)] leading-relaxed">${{razonamiento}}</div>
          </div>
        </div>
      `;
    }}

  </script>
</body>
</html>
"""

# Guardar en artifact dir y en workspace data/
with open(HTML_ARTIFACT_PATH, "w", encoding="utf-8") as f:
    f.write(html_content)

with open(LOCAL_HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"[OK] Dashboard v3 generado exitosamente:")
print(f"  • Artifact: {HTML_ARTIFACT_PATH}")
print(f"  • Workspace: {LOCAL_HTML_PATH}")
