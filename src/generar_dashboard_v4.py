"""
Generador Maestro del Dashboard BI interactivo v6.0 para Cantina Familiar 2026.
Diseño Híbrido:
- Paleta clara Almendrada / Alabastro Cálido (Cero sobresaturación, descanso visual).
- Sistema de Diseño Material 3 Expressive (MD3): Superficies tonales (Surface Containers), bordes redondeados expresivos (24px-28px), chips tonales en cápsula, botones segmentados y transiciones enfatizadas.
- Pautas Apple Human Interface Guidelines (HIG) en Móvil: Barra de pestañas inferior translúcida (iOS Tab Bar con blur), objetivos táctiles >= 44pt, fuentes de inputs >= 16px en móvil para evitar zoom automático en Safari, y listas agrupadas estilo iOS Inset Grouped.
"""

import os
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
LOCAL_HTML_PATH = ROOT_DIR / "data" / "dashboard_bi.html"
INDEX_HTML_PATH = ROOT_DIR / "index.html"
DATA_JSON_PATH = ROOT_DIR / "data" / "dashboard_data.json"

# Ruta opcional de artefactos de entorno asistido (solo si está definida en variables de entorno)
ARTIFACT_DIR = os.environ.get("ANTIGRAVITY_ARTIFACT_DIR")
HTML_ARTIFACT_PATH = Path(ARTIFACT_DIR) / "dashboard_bi.html" if ARTIFACT_DIR else None


# Cargar los datos auditados (653 productos en 5 tiendas)
with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
    datos_json_str = f.read()

# =====================================================================
# MATRIZ OFICIAL DE VIGENCIAS Y PROMOCIONES MULTITIENDA (OCTUBRE 2026)
# =====================================================================
VIGENCIAS_TIENDAS = {
    "alianza": "25 de octubre 2026 (Aniversario Web)",
    "sams": "2 de noviembre 2026 (Cuponera Octubre / Día de Muertos)",
    "chedraui": "31 de octubre 2026 (Quincena MiChedraui)",
    "soriana": "22 de octubre 2026 (Folleto Semanal de Licores)",
    "walmart": "31 de octubre 2026 (Rebajas de Temporada en Línea)"
}

CONFIG_VIGENCIA = {
    "corte_auditoria": "Octubre 2026",
    "resumen_whatsapp": (
        "🟠 Bodegas Alianza: hasta 25 Oct (Aniversario)\n"
        "🔵 Sam's Club: hasta 2 Nov (Cuponera)\n"
        "🟧 Chedraui: hasta 31 Oct (Quincena)\n"
        "🔴 Soriana: hasta 22 Oct (Folleto semanal)\n"
        "🩵 Walmart: hasta 31 Oct (Rebajas)"
    )
}

html_template = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>Cantina Familiar 2026</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=JetBrains+Mono:wght@500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      /* Material 3 Expressive · Warm Almond & Alabaster Tonal Palette */
      --md-bg: #FAF6F0;
      --md-surface: #F4EFE6;
      --md-surface-lowest: #FFFFFF;
      --md-surface-low: #F7F2EA;
      --md-surface-container: #EFE8DC;
      --md-surface-high: #E6DDD0;
      --md-on-surface: #1F1B16;
      --md-on-surface-variant: #574A3D;
      --md-outline: #8A7B6B;
      --md-outline-variant: #DFD5C7;

      /* Tonal Accents (Soft, low-saturation expressive containers) */
      --md-primary: #784516;
      --md-on-primary: #FFFFFF;
      --md-primary-container: #F8E2C8;
      --md-on-primary-container: #2B1500;

      --md-secondary: #486355;
      --md-secondary-container: #D3E8DC;
      --md-on-secondary-container: #0B2016;

      --md-tertiary: #753B47;
      --md-tertiary-container: #FAD9DF;
      --md-on-tertiary-container: #2C0811;

      --md-ease-expressive: cubic-bezier(0.2, 0, 0, 1);
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Plus Jakarta Sans', 'SF Pro Text', sans-serif;
      background-color: var(--md-bg);
      color: var(--md-on-surface);
      -webkit-font-smoothing: antialiased;
      padding-bottom: 5.5rem; /* Espacio para iOS Bottom Tab Bar en móvil */
    }

    @media (min-width: 768px) {
      body {
        padding-bottom: 2.5rem;
      }
    }

    .font-display-md3 {
      font-family: 'Fraunces', Georgia, serif;
      letter-spacing: -0.02em;
    }

    .font-mono {
      font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, monospace;
    }

    /* Scrollbar sutil tono almendra */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #F4EFE6; }
    ::-webkit-scrollbar-thumb { background: #C8B9A6; border-radius: 9999px; }
    ::-webkit-scrollbar-thumb:hover { background: #9C8A74; }

    /* Material 3 Expressive Surface Cards */
    .md3-card {
      background-color: var(--md-surface-lowest);
      border: 1px solid var(--md-outline-variant);
      border-radius: 24px;
      box-shadow: 0 2px 12px rgba(31, 27, 22, 0.04);
      transition: transform 0.25s var(--md-ease-expressive), box-shadow 0.25s var(--md-ease-expressive);
      min-width: 0;
      max-width: 100%;
      box-sizing: border-box;
    }

    .md3-surface-tonal {
      background-color: var(--md-surface-container);
      border: 1px solid var(--md-outline-variant);
      border-radius: 18px;
      min-width: 0;
      max-width: 100%;
      box-sizing: border-box;
    }

    .md3-surface-low {
      background-color: var(--md-surface-low);
      border: 1px solid var(--md-outline-variant);
      border-radius: 18px;
      min-width: 0;
      max-width: 100%;
      box-sizing: border-box;
    }

    /* Inputs con soporte Apple HIG (16px en móvil para evitar auto-zoom de iOS Safari, 44px altura táctil) */
    .md3-input {
      background-color: var(--md-surface-lowest);
      border: 1.5px solid #CFC2B2;
      border-radius: 14px;
      color: var(--md-on-surface);
      min-height: 44px;
      font-size: 16px;
      transition: all 0.2s var(--md-ease-expressive);
      min-width: 0;
      max-width: 100%;
      box-sizing: border-box;
    }
    @media (min-width: 640px) {
      .md3-input {
        font-size: 0.875rem;
        min-height: 40px;
      }
    }
    .md3-input:focus {
      outline: none;
      border-color: var(--md-primary);
      box-shadow: 0 0 0 3px rgba(120, 69, 22, 0.14);
    }
    .md3-input::placeholder {
      color: #9A8B7A;
    }

    /* Regla para evitar que los select y picklists desborden tarjetas */
    select.md3-input {
      text-overflow: ellipsis;
      overflow: hidden;
      white-space: nowrap;
      max-width: 100%;
      width: 100%;
    }
    select.md3-input option {
      font-size: 13px;
      color: #1F1B16;
      background-color: #FFFFFF;
    }

    /* Botones MD3 Expressive Pill */
    .md3-btn-filled {
      background-color: var(--md-primary);
      color: var(--md-on-primary);
      border-radius: 9999px;
      min-height: 44px;
      font-weight: 600;
      transition: all 0.2s var(--md-ease-expressive);
      box-shadow: 0 2px 6px rgba(120, 69, 22, 0.18);
    }
    @media (min-width: 640px) {
      .md3-btn-filled {
        min-height: 38px;
      }
    }
    .md3-btn-filled:hover {
      background-color: #63370F;
      box-shadow: 0 4px 12px rgba(120, 69, 22, 0.26);
      transform: translateY(-1px);
    }
    .md3-btn-filled:active {
      transform: scale(0.98);
    }

    .md3-btn-tonal {
      background-color: var(--md-primary-container);
      color: var(--md-on-primary-container);
      border: 1px solid #E5C8A3;
      border-radius: 9999px;
      min-height: 44px;
      font-weight: 600;
      transition: all 0.2s var(--md-ease-expressive);
    }
    @media (min-width: 640px) {
      .md3-btn-tonal {
        min-height: 36px;
      }
    }
    .md3-btn-tonal:hover {
      background-color: #F2D5B3;
    }

    /* Chips Tonales MD3 (Baja saturación) */
    .badge {
      display: inline-flex;
      align-items: center;
      padding: 0.2rem 0.65rem;
      border-radius: 9999px;
      font-size: 0.72rem;
      font-weight: 600;
      letter-spacing: 0.01em;
    }

    /* Apple HIG Frosted Glass Bottom Bar en Móvil */
    .ios-tab-bar {
      background: rgba(250, 246, 240, 0.86);
      -webkit-backdrop-filter: blur(20px) saturate(180%);
      backdrop-filter: blur(20px) saturate(180%);
      border-top: 0.5px solid rgba(138, 123, 107, 0.3);
      padding-bottom: env(safe-area-inset-bottom, 0px);
    }

    /* Toast MD3 Snackbar */
    .toast {
      position: fixed;
      bottom: 5.25rem;
      right: 1rem;
      left: 1rem;
      max-width: 24rem;
      margin: 0 auto;
      padding: 0.85rem 1.25rem;
      background: #2C251E;
      color: #FAF6F0;
      border-radius: 16px;
      font-size: 0.85rem;
      font-weight: 600;
      box-shadow: 0 10px 25px -5px rgba(31, 27, 22, 0.28);
      z-index: 9999;
      opacity: 0;
      transform: translateY(1rem);
      transition: all 0.3s var(--md-ease-expressive);
      pointer-events: none;
    }
    @media (min-width: 768px) {
      .toast {
        bottom: 1.5rem;
        left: auto;
        margin: 0;
      }
    }
    .toast.show {
      opacity: 1;
      transform: translateY(0);
      pointer-events: auto;
    }

    input[type=number]::-webkit-inner-spin-button, 
    input[type=number]::-webkit-outer-spin-button { 
      -webkit-appearance: none; 
      margin: 0; 
    }
    input[type=number] {
      -moz-appearance: textfield;
    }
  </style>
</head>
<body class="p-3 sm:p-6">

  <!-- SNACKBAR / TOAST MD3 -->
  <div id="toast-notif" class="toast">🍾 Producto añadido al carrito</div>

  <div class="max-w-7xl mx-auto space-y-5 sm:space-y-6">

    <!-- HEADER MD3 EXPRESSIVE (SUPERFICIE ALMENDRADA CLARA, INPUTS EN BLANCO AL INICIAR) -->
    <header class="md3-card p-5 sm:p-7 flex flex-col lg:flex-row justify-between items-start lg:items-center gap-5">
      <div class="space-y-1">
        <div class="flex items-center gap-3">
          <div class="w-11 h-11 rounded-2xl bg-[#F8E2C8] border border-[#E5C8A3] flex items-center justify-center text-2xl shadow-sm">
            🥃
          </div>
          <h1 class="text-2xl sm:text-3xl font-bold font-display-md3 text-[#1F1B16]">
            Cantina Familiar 2026
          </h1>
        </div>
        <p class="text-[#574A3D] text-xs sm:text-sm max-w-2xl pt-0.5">
          Comparador multitienda de tequilas, mezcales, whiskies y vinos con cálculo en vivo por litro y por persona.
        </p>
      </div>

      <!-- CONTROLES GLOBALES EN BLANCO AL INICIAR -->
      <div class="grid grid-cols-2 sm:flex sm:flex-nowrap items-center gap-3 sm:gap-4 md3-surface-tonal p-3.5 sm:p-4 w-full lg:w-auto">
        <div class="flex-1 sm:flex-initial">
          <label for="input-presupuesto-global" class="block text-[11px] font-bold text-[#784516] uppercase tracking-wider">
            Presupuesto ($ MXN)
          </label>
          <div class="flex items-center gap-1.5 mt-1">
            <span class="text-sm font-bold text-[#784516] font-mono">$</span>
            <input type="number" id="input-presupuesto-global" value="" min="0" max="200000" step="100"
                   placeholder="Ej. 8500"
                   oninput="actualizarParametrosGlobales()"
                   class="w-full sm:w-32 md3-input px-3 py-1.5 font-mono font-bold text-[#1F1B16]">
          </div>
        </div>

        <div class="h-10 w-px bg-[#D6C8B8] hidden sm:block"></div>

        <div class="flex-1 sm:flex-initial">
          <label for="input-cooperadores-global" class="block text-[11px] font-bold text-[#486355] uppercase tracking-wider">
            Personas (N)
          </label>
          <div class="flex items-center gap-1.5 mt-1">
            <input type="number" id="input-cooperadores-global" value="" min="1" max="200" step="1"
                   placeholder="Ej. 14"
                   oninput="actualizarParametrosGlobales()"
                   class="w-full sm:w-24 md3-input px-3 py-1.5 font-mono font-bold text-[#1F1B16] text-center">
            <span class="text-xs text-[#574A3D] hidden sm:inline">pers.</span>
          </div>
        </div>
    </header>

    <!-- BANNER MULTITIENDA DE VIGENCIAS Y AUDITORÍA DE PROMOCIONES -->
    <div class="md3-surface-tonal p-3.5 sm:p-4 rounded-2xl space-y-2.5 text-xs border border-[#DFD5C7]">
      <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 border-b border-[#DFD5C7]/70 pb-2">
        <div class="flex items-center gap-2 font-bold text-[#1F1B16]">
          <span class="text-base">📅</span>
          <span>Vigencias de Ofertas y Promociones por Tienda (Octubre 2026):</span>
        </div>
        <span class="badge bg-[#D3E8DC] text-[#0B2016] border border-[#B7D6C5] font-mono text-[11px]">
          Auditoría: __CORTE_AUDITORIA__
        </span>
      </div>
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2 font-mono text-[11px]">
        <div class="p-2.5 rounded-xl bg-white/90 border border-[#E5C8A3] flex flex-col justify-between">
          <span class="font-bold text-[#784516]">🟠 Bodegas Alianza</span>
          <span class="text-[10px] text-[#574A3D] truncate">Aniversario Web</span>
          <span class="font-extrabold text-[#784516] mt-0.5">Hasta 25 Oct 2026</span>
        </div>
        <div class="p-2.5 rounded-xl bg-white/90 border border-[#BFDBFE] flex flex-col justify-between">
          <span class="font-bold text-[#1E3A8A]">🔵 Sam's Club</span>
          <span class="text-[10px] text-[#574A3D] truncate">Cuponera de Octubre</span>
          <span class="font-extrabold text-[#1E3A8A] mt-0.5">Hasta 2 Nov 2026</span>
        </div>
        <div class="p-2.5 rounded-xl bg-white/90 border border-[#FED7AA] flex flex-col justify-between">
          <span class="font-bold text-[#7C2D12]">🟧 Chedraui</span>
          <span class="text-[10px] text-[#574A3D] truncate">Quincena MiChedraui</span>
          <span class="font-extrabold text-[#7C2D12] mt-0.5">Hasta 31 Oct 2026</span>
        </div>
        <div class="p-2.5 rounded-xl bg-white/90 border border-[#FECDD3] flex flex-col justify-between">
          <span class="font-bold text-[#881337]">🔴 Soriana</span>
          <span class="text-[10px] text-[#574A3D] truncate">Folleto Licores</span>
          <span class="font-extrabold text-[#881337] mt-0.5">Hasta 22 Oct 2026</span>
        </div>
        <div class="p-2.5 rounded-xl bg-white/90 border border-[#BAE6FD] flex flex-col justify-between col-span-2 sm:col-span-1">
          <span class="font-bold text-[#0C4A6E]">🩵 Walmart</span>
          <span class="text-[10px] text-[#574A3D] truncate">Rebajas en Línea</span>
          <span class="font-extrabold text-[#0C4A6E] mt-0.5">Hasta 31 Oct 2026</span>
        </div>
      </div>
    </div>

    <!-- NAVEGACIÓN DESKTOP MD3 SEGMENTED PILL BAR (OCULTA EN MÓVIL, VISIBLE EN >=768px) -->
    <nav class="hidden md:flex md3-surface-tonal p-1.5 gap-1.5 text-sm font-semibold">
      <button onclick="cambiarTab('tab-rankings')" id="btn-tab-rankings" class="tab-btn flex-1 py-2.5 px-4 rounded-2xl bg-white text-[#1F1B16] shadow-sm flex items-center justify-center gap-2 transition-all cursor-pointer">
        <span>🍾 1. Catálogo & Rankings $/L</span>
      </button>

      <button onclick="cambiarTab('tab-versus')" id="btn-tab-versus" class="tab-btn flex-1 py-2.5 px-4 rounded-2xl text-[#574A3D] hover:text-[#1F1B16] hover:bg-white/50 flex items-center justify-center gap-2 transition-all cursor-pointer">
        <span>⚔️ 2. Duelo Head-to-Head</span>
      </button>

      <button onclick="cambiarTab('tab-carrito')" id="btn-tab-carrito" class="tab-btn flex-1 py-2.5 px-4 rounded-2xl text-[#574A3D] hover:text-[#1F1B16] hover:bg-white/50 flex items-center justify-center gap-2 transition-all cursor-pointer">
        <span>🛒 3. Carrito & Armador</span>
        <span class="badge bg-[#F8E2C8] text-[#784516] border border-[#E5C8A3] text-[11px] ml-1 font-mono" id="badge-nav-carrito-count">0</span>
      </button>

      <button onclick="cambiarTab('tab-matriz')" id="btn-tab-matriz" class="tab-btn flex-1 py-2.5 px-4 rounded-2xl text-[#574A3D] hover:text-[#1F1B16] hover:bg-white/50 flex items-center justify-center gap-2 transition-all cursor-pointer">
        <span>📜 4. Guía de Barricas</span>
      </button>
    </nav>

    <!-- ========================================================================================= -->
    <!-- PESTAÑA 1: CATÁLOGO & RANKINGS $/LITRO (SEGMENTACIÓN EN 2 PASOS: CATEGORÍA -> TIPO) -->
    <!-- ========================================================================================= -->
    <div id="tab-rankings" class="tab-content space-y-5">

      <!-- BARRA DE FILTROS EN 2 NIVELES SEPARADOS (MD3 SURFACE) -->
      <div class="md3-card p-5 space-y-4">
        <div class="flex flex-col sm:flex-row justify-between sm:items-center gap-2 border-b border-[#DFD5C7] pb-3">
          <div>
            <h2 class="text-lg font-bold font-display-md3 text-[#1F1B16]">
              Explorador de Catálogo Multitienda
            </h2>
            <p class="text-xs text-[#574A3D]">
              Paso 1: Elige la categoría de bebida · Paso 2: Filtra por el tipo de añejamiento o estilo.
            </p>
          </div>
          <div class="badge bg-[#D3E8DC] text-[#0B2016] border border-[#B7D6C5] font-mono text-xs self-start sm:self-auto px-3 py-1" id="contador-filtrados">
            653 botellas verificadas (5 tiendas)
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
          <!-- 1. Menú de Categoría Principal -->
          <div>
            <label class="block text-xs font-bold text-[#784516] mb-1.5">1. Categoría de Bebida:</label>
            <select id="filtro-macro-categoria" onchange="actualizarSubtiposCatalogo()" class="w-full md3-input px-3 py-2 font-semibold">
              <option value="Todas" selected>🍾 Todas las Bebidas (653)</option>
              <option value="Tequila">🥃 Tequila (209)</option>
              <option value="Mezcal">🌵 Mezcal (119)</option>
              <option value="Whisky">🥃 Whisky Escocés (168)</option>
              <option value="Licor de Whisky">🍯 Licor Whisky Honey (12)</option>
              <option value="Vino">🍷 Vino Tinto (145)</option>
            </select>
          </div>

          <!-- 2. Menú de Tipo de Bebida / Subcategoría -->
          <div>
            <label class="block text-xs font-bold text-[#486355] mb-1.5">2. Tipo de Bebida:</label>
            <select id="filtro-categoria" onchange="aplicarFiltros()" class="w-full md3-input px-3 py-2 font-medium">
            </select>
          </div>

          <!-- 3. Selector de Tienda -->
          <div>
            <label class="block text-xs font-bold text-[#574A3D] mb-1.5">3. Tienda / Comercio:</label>
            <select id="filtro-tienda" onchange="aplicarFiltros()" class="w-full md3-input px-3 py-2">
              <option value="Todas">🏬 Todas las Tiendas (5)</option>
              <option value="Bodegas Alianza">🟠 Bodegas Alianza (270)</option>
              <option value="Chedraui">🟧 Chedraui (115)</option>
              <option value="Soriana">🔴 Soriana (112)</option>
              <option value="Walmart">🩵 Walmart (87)</option>
              <option value="Sam's Club">🔵 Sam's Club (69)</option>
            </select>
          </div>

          <!-- 4. Búsqueda por palabras clave -->
          <div>
            <label class="block text-xs font-bold text-[#574A3D] mb-1.5">4. Buscar Etiqueta o Marca:</label>
            <input type="text" id="filtro-busqueda" oninput="aplicarFiltros()" placeholder="Ej. Dobel, 1800, Amarás, Red Label..."
                   class="w-full md3-input px-3 py-2">
          </div>

          <!-- 5. Casilla Solo Ofertas -->
          <div class="flex items-end">
            <label class="flex items-center gap-2.5 text-xs text-[#1F1B16] cursor-pointer md3-surface-low hover:bg-[#EFE8DC] px-3.5 py-2.5 w-full transition-colors min-h-[44px] sm:min-h-[40px]">
              <input type="checkbox" id="filtro-descuento" onchange="aplicarFiltros()" class="w-4 h-4 rounded accent-[#784516]">
              <span class="font-semibold truncate">🏷️ Solo en oferta</span>
            </label>
          </div>
        </div>
      </div>

      <!-- TABLA / LISTA DE PRODUCTOS (ADAPTATIVA DESKTOP + APPLE HIG CARDS EN MÓVIL) -->
      <div class="md3-card overflow-hidden">
        <div class="p-4 sm:p-5 border-b border-[#DFD5C7] flex flex-col sm:flex-row justify-between sm:items-center gap-3 bg-[#F7F2EA]">
          <div>
            <h3 class="font-bold text-base sm:text-lg font-display-md3 text-[#1F1B16]">Catálogo General Normalizado</h3>
            <p class="text-xs text-[#574A3D]">Pulsa <strong>+ Carrito</strong> para sumar cualquier botella a tu cuenta</p>
          </div>
          <div class="flex items-center gap-2 text-xs">
            <span class="text-[#574A3D] font-medium">Ordenar:</span>
            <button onclick="ordenarPor('precio_por_litro')" class="md3-btn-tonal px-3 py-1.5 text-xs cursor-pointer">
              Menor $/Litro ↕
            </button>
            <button onclick="ordenarPor('precio_promo')" class="px-3 py-1.5 rounded-full bg-white border border-[#D6C8B8] text-[#1F1B16] hover:bg-[#EFE8DC] font-semibold text-xs transition-colors cursor-pointer min-h-[36px]">
              Precio Botella ↕
            </button>
          </div>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-left text-sm">
            <thead class="bg-[#EFE8DC] text-[#574A3D] text-xs uppercase border-b border-[#DFD5C7]">
              <tr>
                <th class="p-3.5">Botella / Marca</th>
                <th class="p-3.5 hidden sm:table-cell">Categoría & Tipo</th>
                <th class="p-3.5 hidden md:table-cell">Volumen</th>
                <th class="p-3.5 cursor-pointer hover:text-[#784516]" onclick="ordenarPor('precio_promo')">Precio ↕</th>
                <th class="p-3.5 cursor-pointer hover:text-[#784516]" onclick="ordenarPor('precio_por_litro')">$/Litro ↕</th>
                <th class="p-3.5 hidden lg:table-cell">Promoción</th>
                <th class="p-3.5">Tienda</th>
                <th class="p-3.5 text-center">Acción</th>
              </tr>
            </thead>
            <tbody id="tabla-productos-body" class="divide-y divide-[#EAE0D3]">
              <!-- Filas generadas por JS -->
            </tbody>
          </table>
        </div>

        <div class="p-4 border-t border-[#DFD5C7] flex justify-between items-center text-xs text-[#574A3D] bg-[#F7F2EA]">
          <div id="info-paginacion" class="font-medium">Mostrando 1 a 20 de 653</div>
          <div class="flex gap-2">
            <button onclick="cambiarPagina(-1)" id="btn-prev" class="px-4 py-2 rounded-full bg-white border border-[#D6C8B8] hover:bg-[#EFE8DC] disabled:opacity-40 transition-colors text-[#1F1B16] font-semibold cursor-pointer min-h-[40px]">← Anterior</button>
            <button onclick="cambiarPagina(1)" id="btn-next" class="px-4 py-2 rounded-full bg-white border border-[#D6C8B8] hover:bg-[#EFE8DC] disabled:opacity-40 transition-colors text-[#1F1B16] font-semibold cursor-pointer min-h-[40px]">Siguiente →</button>
          </div>
        </div>
      </div>

      <!-- GRÁFICO TOP 10 RENDIMIENTO $/LITRO (PALETA SUAVE MD3) -->
      <div class="md3-card p-5 space-y-3">
        <div class="flex flex-col sm:flex-row justify-between sm:items-center gap-2 border-b border-[#DFD5C7] pb-3">
          <div>
            <h3 class="font-bold text-lg font-display-md3 text-[#1F1B16]" id="chart-titulo">
              Top 10 Rendimiento $/Litro del Catálogo
            </h3>
            <p class="text-xs text-[#574A3D]">Comparativa volumétrica estandarizada a 1,000 ml entre las 5 cadenas</p>
          </div>
          <span class="badge bg-[#F8E2C8] text-[#784516] border border-[#E5C8A3] text-xs self-start sm:self-auto">Barra más corta = Mejor precio por litro</span>
        </div>
        <div id="chart-container" class="w-full overflow-x-auto">
        </div>
      </div>

    </div>

    <!-- ========================================================================================= -->
    <!-- PESTAÑA 2: HEAD-TO-HEAD VERSUS (SEGMENTADO EN CATEGORÍA Y TIPO + SIMULACIÓN REACTIVA) -->
    <!-- ========================================================================================= -->
    <div id="tab-versus" class="tab-content space-y-5 hidden">

      <!-- FILTRO EN 2 PASOS PARA EL VERSUS: 1. CATEGORÍA -> 2. TIPO DE BEBIDA -->
      <div class="md3-card p-5 space-y-4">
        <div class="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 border-b border-[#DFD5C7] pb-4">
          <div>
            <h3 class="font-bold text-lg font-display-md3 text-[#1F1B16]">
              Selector de Categoría y Tipo para el Duelo
            </h3>
            <p class="text-xs text-[#574A3D]">
              Elige primero la bebida y luego el tipo exacto para enfrentar etiquetas equivalentes.
            </p>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full lg:w-auto">
            <div>
              <label class="block text-[11px] font-bold text-[#784516] uppercase mb-1">1. Categoría de Bebida:</label>
              <select id="select-versus-macro" onchange="actualizarSubtiposVersus()" class="w-full sm:w-52 md3-input px-3 py-2 text-xs font-semibold">
                <option value="Tequila" selected>🥃 Tequila</option>
                <option value="Mezcal">🌵 Mezcal</option>
                <option value="Whisky">🥃 Whisky Escocés</option>
                <option value="Licor de Whisky">🍯 Licor Whisky Honey</option>
                <option value="Vino">🍷 Vino Tinto</option>
                <option value="Todas">🔓 Comparativa Libre</option>
              </select>
            </div>

            <div>
              <label class="block text-[11px] font-bold text-[#486355] uppercase mb-1">2. Tipo de Bebida:</label>
              <select id="select-versus-categoria-filtro" onchange="filtrarSelectoresVersusPorCategoria()" class="w-full sm:w-64 md3-input px-3 py-2 text-xs font-semibold">
              </select>
            </div>
          </div>
        </div>

        <!-- SUGERENCIAS DINÁMICAS DE DUELOS SEGÚN EL TIPO ESCOGIDO -->
        <div class="space-y-2 pt-1">
          <div class="flex justify-between items-center text-xs">
            <span class="text-[#574A3D] font-bold uppercase tracking-wider">
              Duelos Sugeridos en este Tipo:
            </span>
            <span class="text-[#784516] font-mono font-semibold text-[11px]" id="versus-sugerencias-info">Duelos clave</span>
          </div>
          <div class="flex flex-wrap gap-2" id="versus-sugerencias-container">
          </div>
        </div>
      </div>

      <!-- SELECTORES MANUALES A Y B -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 min-w-0">
        <div class="md3-card p-4 space-y-1.5 border-l-4 border-l-[#784516] min-w-0 overflow-hidden">
          <label class="block text-xs font-bold text-[#784516] uppercase tracking-wider">Contendiente A:</label>
          <select id="select-versus-a" onchange="actualizarVersusManual('A')" class="w-full min-w-0 max-w-full md3-input p-2.5 text-xs sm:text-sm truncate">
          </select>
        </div>
        <div class="md3-card p-4 space-y-1.5 border-l-4 border-l-[#753B47] min-w-0 overflow-hidden">
          <label class="block text-xs font-bold text-[#753B47] uppercase tracking-wider">Contendiente B:</label>
          <select id="select-versus-b" onchange="actualizarVersusManual('B')" class="w-full min-w-0 max-w-full md3-input p-2.5 text-xs sm:text-sm truncate">
          </select>
        </div>
      </div>

      <!-- BANNER DE COMPATIBILIDAD CATEGÓRICA -->
      <div id="versus-alerta-compatibilidad">
      </div>

      <!-- TARJETAS COMPARATIVAS LADO A LADO -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-5" id="versus-tarjetas-container">
      </div>

      <!-- SIMULACIÓN DE COMPRA REACTIVA Y TIPS DE DECISIÓN -->
      <div id="versus-impacto-familiar-box" class="md3-card p-5 space-y-4">
      </div>

      <!-- VEREDICTO DE INTELIGENCIA DE COMPRA -->
      <div id="versus-veredicto-box" class="md3-card p-6 bg-[#F7F2EA]">
      </div>

    </div>

    <!-- ========================================================================================= -->
    <!-- PESTAÑA 3: CARRITO DE COMPRAS & GENERADOR DINÁMICO DE CANASTAS -->
    <!-- ========================================================================================= -->
    <div id="tab-carrito" class="tab-content space-y-5 hidden">

      <!-- GENERADOR DINÁMICO DE CANASTA (CALCULADO EN TIEMPO REAL SEGÚN PRESUPUESTO Y PERSONAS) -->
      <div class="md3-card p-5 space-y-4">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 border-b border-[#DFD5C7] pb-3">
          <div>
            <h2 class="text-lg font-bold font-display-md3 text-[#1F1B16]">
              ✨ Armador Dinámico de Canastas
            </h2>
            <p class="text-xs text-[#574A3D]" id="subtitulo-generador-dinamico">
              Calcula automáticamente cuántas botellas comprar y en qué tienda según el presupuesto y número de personas que ingreses arriba.
            </p>
          </div>
          <div class="flex items-center gap-2">
            <button onclick="vaciarCarrito()" class="px-4 py-2 rounded-full bg-[#FAD9DF] hover:bg-[#F5C2CB] border border-[#E5B3BC] text-xs font-bold text-[#753B47] transition-colors flex items-center gap-1.5 cursor-pointer min-h-[40px]">
              <span>🗑️ Vaciar Carrito</span>
            </button>
          </div>
        </div>

        <!-- Contenedor de 3 propuestas generadas dinámicamente por JS -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4" id="contenedor-canastas-dinamicas">
        </div>
      </div>

      <!-- CONSTRUCTOR GRANULAR DIVIDIDO POR CATEGORÍA CON BALANCE FINANCIERO -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 min-w-0">

        <!-- COLUMNA PRINCIPAL (2 COLUMNAS): CATEGORÍAS SEPARADAS -->
        <div class="lg:col-span-2 space-y-4 min-w-0">

          <!-- 1. CATEGORÍA: TEQUILAS -->
          <div class="md3-card p-5 space-y-4 min-w-0 overflow-hidden">
            <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 border-b border-[#DFD5C7] pb-3">
              <div class="flex items-center gap-2.5">
                <span class="text-2xl">🥃</span>
                <div>
                  <h3 class="font-bold text-base font-display-md3 text-[#1F1B16]">
                    1. Tequilas (Añejo Cristalino, Reposado Cristalino, Añejo Tradicional)
                  </h3>
                  <p class="text-xs text-[#574A3D]">Solo etiquetas con maduración en barrica o cristalinos</p>
                </div>
              </div>
              <div class="flex items-center gap-2 text-xs font-mono">
                <span class="badge bg-[#F8E2C8] text-[#784516] border border-[#E5C8A3]" id="subtotal-cant-tequila">0 botellas</span>
                <span class="font-bold text-[#784516] text-sm" id="subtotal-precio-tequila">$0.00</span>
              </div>
            </div>

            <div id="lista-botellas-tequila" class="space-y-2.5"></div>

            <div class="pt-2 border-t border-[#DFD5C7] flex flex-col sm:flex-row gap-2 min-w-0 w-full items-stretch sm:items-center">
              <select id="select-agregar-tequila" class="flex-1 min-w-0 w-full max-w-full md3-input px-3 py-2 text-xs truncate" style="min-width: 0; max-width: 100%;"></select>
              <button onclick="agregarBotellaDesdeSelect('Tequila')" class="sm:flex-shrink-0 px-5 py-2 md3-btn-filled text-xs cursor-pointer whitespace-nowrap">
                + Añadir Tequila
              </button>
            </div>
          </div>

          <!-- 2. CATEGORÍA: MEZCALES -->
          <div class="md3-card p-5 space-y-4 min-w-0 overflow-hidden">
            <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 border-b border-[#DFD5C7] pb-3">
              <div class="flex items-center gap-2.5">
                <span class="text-2xl">🌵</span>
                <div>
                  <h3 class="font-bold text-base font-display-md3 text-[#1F1B16]">
                    2. Mezcales (Silvestres, Reposado, Reposado Cristalino, Añejo, Joven)
                  </h3>
                  <p class="text-xs text-[#574A3D]">Agaves Tobalá, Cupreata, Cuishe y Espadín artesanal</p>
                </div>
              </div>
              <div class="flex items-center gap-2 text-xs font-mono">
                <span class="badge bg-[#D3E8DC] text-[#0B2016] border border-[#B7D6C5]" id="subtotal-cant-mezcal">0 botellas</span>
                <span class="font-bold text-[#486355] text-sm" id="subtotal-precio-mezcal">$0.00</span>
              </div>
            </div>

            <div id="lista-botellas-mezcal" class="space-y-2.5"></div>

            <div class="pt-2 border-t border-[#DFD5C7] flex flex-col sm:flex-row gap-2 min-w-0 w-full items-stretch sm:items-center">
              <select id="select-agregar-mezcal" class="flex-1 min-w-0 w-full max-w-full md3-input px-3 py-2 text-xs truncate" style="min-width: 0; max-width: 100%;"></select>
              <button onclick="agregarBotellaDesdeSelect('Mezcal')" class="sm:flex-shrink-0 px-5 py-2 md3-btn-filled text-xs cursor-pointer whitespace-nowrap">
                + Añadir Mezcal
              </button>
            </div>
          </div>

          <!-- 3. CATEGORÍA: WHISKIES -->
          <div class="md3-card p-5 space-y-4 min-w-0 overflow-hidden">
            <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 border-b border-[#DFD5C7] pb-3">
              <div class="flex items-center gap-2.5">
                <span class="text-2xl">🥃</span>
                <div>
                  <h3 class="font-bold text-base font-display-md3 text-[#1F1B16]">
                    3. Whisky Blended Scotch
                  </h3>
                  <p class="text-xs text-[#574A3D]">Formatos de 700 ml, 1 L y presentaciones de 1.75 L</p>
                </div>
              </div>
              <div class="flex items-center gap-2 text-xs font-mono">
                <span class="badge bg-[#F8E2C8] text-[#784516] border border-[#E5C8A3]" id="subtotal-cant-whisky">0 botellas</span>
                <span class="font-bold text-[#784516] text-sm" id="subtotal-precio-whisky">$0.00</span>
              </div>
            </div>

            <div id="lista-botellas-whisky" class="space-y-2.5"></div>

            <div class="pt-2 border-t border-[#DFD5C7] flex flex-col sm:flex-row gap-2 min-w-0 w-full items-stretch sm:items-center">
              <select id="select-agregar-whisky" class="flex-1 min-w-0 w-full max-w-full md3-input px-3 py-2 text-xs truncate" style="min-width: 0; max-width: 100%;"></select>
              <button onclick="agregarBotellaDesdeSelect('Whisky')" class="sm:flex-shrink-0 px-5 py-2 md3-btn-filled text-xs cursor-pointer whitespace-nowrap">
                + Añadir Whisky
              </button>
            </div>
          </div>

          <!-- 4. CATEGORÍA: LICOR HONEY -->
          <div class="md3-card p-5 space-y-4 min-w-0 overflow-hidden">
            <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 border-b border-[#DFD5C7] pb-3">
              <div class="flex items-center gap-2.5">
                <span class="text-2xl">🍯</span>
                <div>
                  <h3 class="font-bold text-base font-display-md3 text-[#1F1B16]">
                    4. Licor de Whisky Honey (Miel)
                  </h3>
                  <p class="text-xs text-[#574A3D]">Jack Daniel's Tennessee Honey y Passport Honey verificados</p>
                </div>
              </div>
              <div class="flex items-center gap-2 text-xs font-mono">
                <span class="badge bg-[#F8E2C8] text-[#784516] border border-[#E5C8A3]" id="subtotal-cant-honey">0 botellas</span>
                <span class="font-bold text-[#784516] text-sm" id="subtotal-precio-honey">$0.00</span>
              </div>
            </div>

            <div id="lista-botellas-honey" class="space-y-2.5"></div>

            <div class="pt-2 border-t border-[#DFD5C7] flex flex-col sm:flex-row gap-2 min-w-0 w-full items-stretch sm:items-center">
              <select id="select-agregar-honey" class="flex-1 min-w-0 w-full max-w-full md3-input px-3 py-2 text-xs truncate" style="min-width: 0; max-width: 100%;"></select>
              <button onclick="agregarBotellaDesdeSelect('Honey')" class="sm:flex-shrink-0 px-5 py-2 md3-btn-filled text-xs cursor-pointer whitespace-nowrap">
                + Añadir Honey
              </button>
            </div>
          </div>

          <!-- 5. CATEGORÍA: VINOS PARA CLERICOT -->
          <div class="md3-card p-5 space-y-4 min-w-0 overflow-hidden">
            <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 border-b border-[#DFD5C7] pb-3">
              <div class="flex items-center gap-2.5">
                <span class="text-2xl">🍷</span>
                <div>
                  <h3 class="font-bold text-base font-display-md3 text-[#1F1B16]">
                    5. Vinos Tintos para Clericot y Mesa
                  </h3>
                  <p class="text-xs text-[#574A3D]">Garrafas de 4L y 5L, Tetra Pak de 946 ml y botellas de 750 ml</p>
                </div>
              </div>
              <div class="flex items-center gap-2 text-xs font-mono">
                <span class="badge bg-[#FAD9DF] text-[#753B47] border border-[#E5B3BC]" id="subtotal-cant-vino">0 piezas</span>
                <span class="font-bold text-[#753B47] text-sm" id="subtotal-precio-vino">$0.00</span>
              </div>
            </div>

            <div id="lista-botellas-vino" class="space-y-2.5"></div>

            <div class="pt-2 border-t border-[#DFD5C7] flex flex-col sm:flex-row gap-2 min-w-0 w-full items-stretch sm:items-center">
              <select id="select-agregar-vino" class="flex-1 min-w-0 w-full max-w-full md3-input px-3 py-2 text-xs truncate" style="min-width: 0; max-width: 100%;"></select>
              <button onclick="agregarBotellaDesdeSelect('Vino')" class="sm:flex-shrink-0 px-5 py-2 md3-btn-filled text-xs cursor-pointer whitespace-nowrap">
                + Añadir Vino
              </button>
            </div>
          </div>

        </div>

        <!-- COLUMNA LATERAL STICKY: RESUMEN FINANCIERO Y DESGLOSE POR TIENDA -->
        <div class="space-y-4">
          <div class="md3-card p-5 space-y-4 sticky top-6">
            <div class="flex items-center justify-between border-b border-[#DFD5C7] pb-3">
              <h3 class="font-bold text-lg font-display-md3 text-[#1F1B16]">Resumen de Cuenta</h3>
              <span class="badge bg-[#F8E2C8] text-[#784516] border border-[#E5C8A3]" id="badge-sidebar-cooperadores">Sin cooperadores</span>
            </div>

            <!-- BARRA DE CONSUMO DE PRESUPUESTO -->
            <div class="space-y-1.5">
              <div class="flex justify-between text-xs">
                <span class="text-[#574A3D]">Uso de presupuesto:</span>
                <span class="font-bold font-mono text-[#784516]" id="sim-porcentaje-barra">Sin presupuesto</span>
              </div>
              <div class="w-full bg-[#EFE8DC] h-2.5 rounded-full overflow-hidden border border-[#DFD5C7]">
                <div id="sim-barra-dinamica" class="bg-[#784516] h-full rounded-full transition-all duration-300" style="width: 0%"></div>
              </div>
            </div>

            <!-- CUOTA EXACTA POR PERSONA -->
            <div class="md3-surface-tonal p-4 text-center">
              <div class="text-[11px] text-[#574A3D] uppercase font-bold tracking-wider">Cooperación por Persona</div>
              <div class="text-3xl font-extrabold text-[#784516] mt-1 font-mono" id="sim-cuota-persona">—</div>
              <div class="text-xs text-[#574A3D] mt-1" id="sim-subtitulo-cuota">Ingresa el N° de personas arriba</div>
            </div>

            <!-- TOTALES Y DESGLOSE MULTITIENDA -->
            <div class="space-y-2 border-t border-[#DFD5C7] pt-3 text-xs">
              <div class="flex justify-between">
                <span class="text-[#574A3D]">Botellas / Envases:</span>
                <span class="font-semibold font-mono text-[#1F1B16]" id="sim-total-piezas">0 unidades</span>
              </div>
              <div class="flex justify-between">
                <span class="text-[#574A3D]">Volumen Líquido Total:</span>
                <span class="font-semibold font-mono text-[#1F1B16]" id="sim-total-volumen">0.00 Litros</span>
              </div>
              <div class="flex justify-between pt-1">
                <span class="text-[#574A3D]">🟠 Bodegas Alianza:</span>
                <span class="font-semibold font-mono text-[#784516]" id="sim-total-alianza">$0.00</span>
              </div>
              <div class="flex justify-between">
                <span class="text-[#574A3D]">🔵 Sam's Club:</span>
                <span class="font-semibold font-mono text-[#1E40AF]" id="sim-total-sams">$0.00</span>
              </div>
              <div class="flex justify-between">
                <span class="text-[#574A3D]">🩵 Walmart:</span>
                <span class="font-semibold font-mono text-[#0369A1]" id="sim-total-walmart">$0.00</span>
              </div>
              <div class="flex justify-between">
                <span class="text-[#574A3D]">🟧 Chedraui:</span>
                <span class="font-semibold font-mono text-[#C2410C]" id="sim-total-chedraui">$0.00</span>
              </div>
              <div class="flex justify-between">
                <span class="text-[#574A3D]">🔴 Soriana:</span>
                <span class="font-semibold font-mono text-[#9F1239]" id="sim-total-soriana">$0.00</span>
              </div>
              <div class="flex justify-between text-sm font-bold pt-2 border-t border-[#DFD5C7]">
                <span class="text-[#1F1B16]">Total Acumulado:</span>
                <span class="text-[#784516] font-mono text-base" id="sim-gran-total">$0.00</span>
              </div>
            </div>

            <!-- BALANCE CONTRA PRESUPUESTO -->
            <div id="sim-alerta-sobrante" class="p-3 rounded-xl flex items-center justify-between text-xs md3-surface-low">
              <span class="text-[#574A3D] font-medium" id="sim-label-sobrante">Balance de Presupuesto:</span>
              <span class="text-[#784516] font-bold text-xs font-mono" id="sim-sobrante">Ingresa monto arriba</span>
            </div>

            <!-- NOTA DE VIGENCIA DE PRECIOS EN CARRITO -->
            <div class="p-3 rounded-xl bg-[#FAF6F0] border border-[#DFD5C7] text-[11px] text-[#574A3D] space-y-1.5">
              <div class="font-bold text-[#1F1B16] flex items-center justify-between">
                <span class="flex items-center gap-1"><span>⚠️</span> <span>Vigencias de Ofertas:</span></span>
                <span class="text-[10px] text-[#784516] font-mono">5 tiendas</span>
              </div>
              <ul class="space-y-0.5 text-[10px] font-mono">
                <li>• 🟠 Alianza: <strong class="text-[#784516]">25 Oct</strong> (Aniversario)</li>
                <li>• 🔵 Sam's: <strong class="text-[#1E3A8A]">2 Nov</strong> (Cuponera)</li>
                <li>• 🟧 Chedraui: <strong class="text-[#7C2D12]">31 Oct</strong> (Quincena)</li>
                <li>• 🔴 Soriana: <strong class="text-[#881337]">22 Oct</strong> (Folleto)</li>
                <li>• 🩵 Walmart: <strong class="text-[#0C4A6E]">31 Oct</strong> (Rebajas)</li>
              </ul>
            </div>

            <!-- BOTONES DE ACCIÓN RÁPIDA -->
            <div class="grid grid-cols-2 gap-2 pt-2 border-t border-[#DFD5C7]">
              <button onclick="vaciarCarrito()" class="py-2 px-3 rounded-full bg-[#FAD9DF] hover:bg-[#F5C2CB] text-xs text-[#753B47] font-bold transition-colors text-center flex items-center justify-center gap-1 cursor-pointer min-h-[42px]">
                <span>🗑️ Vaciar</span>
              </button>
              <button onclick="copiarListaCompra()" class="py-2 px-3 md3-btn-filled text-xs text-center flex items-center justify-center gap-1 cursor-pointer">
                <span>📋 Copiar Lista</span>
              </button>
            </div>
          </div>
        </div>

      </div>

    </div>

    <!-- ========================================================================================= -->
    <!-- PESTAÑA 4: GUÍA DE BARRICAS Y MADURACIÓN -->
    <!-- ========================================================================================= -->
    <div id="tab-matriz" class="tab-content space-y-6 hidden">
      <div class="md3-card p-6 space-y-5">
        <div>
          <h3 class="text-xl sm:text-2xl font-bold font-display-md3 text-[#1F1B16]">Guía de Maduración en Barrica y Tipos Seleccionados</h3>
          <p class="text-sm text-[#574A3D] mt-1">
            Referencia técnica de las categorías incluidas en la cava (excluyendo tequilas blancos y reposados tradicionales).
          </p>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-left text-sm">
            <thead class="bg-[#EFE8DC] text-[#574A3D] text-xs uppercase border-b border-[#DFD5C7]">
              <tr>
                <th class="p-3.5">Categoría & Tipo</th>
                <th class="p-3.5">Guarda en Roble</th>
                <th class="p-3.5">Proceso Distintivo</th>
                <th class="p-3.5">Referencia Líder Multitienda</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-[#EAE0D3] text-xs">
              <tr class="hover:bg-[#F7F2EA]">
                <td class="p-3.5 font-bold text-[#784516]">Tequila · Añejo Cristalino</td>
                <td class="p-3.5 font-mono">&ge; 12 meses</td>
                <td class="p-3.5">Filtrado en carbón activado tras guarda en roble</td>
                <td class="p-3.5 text-[#574A3D]">Maestro Dobel Diamante ($574.93 en Sam's), 1800 Cristalino ($600 en Alianza) y Don Julio 70 ($699 en Walmart).</td>
              </tr>
              <tr class="hover:bg-[#F7F2EA]">
                <td class="p-3.5 font-bold text-[#9A3412]">Tequila · Reposado Cristalino</td>
                <td class="p-3.5 font-mono">2 a 11 meses</td>
                <td class="p-3.5">Clarificación suave ideal para mezcladores y palomas</td>
                <td class="p-3.5 text-[#574A3D]">Member's Mark 1.75L ($664.93 en Sam's), Cuervo Tradicional Cristalino ($390 en Alianza) y Centenario Ultra ($440).</td>
              </tr>
              <tr class="hover:bg-[#F7F2EA]">
                <td class="p-3.5 font-bold text-[#854D0E]">Tequila · Añejo Tradicional</td>
                <td class="p-3.5 font-mono">&ge; 12 meses</td>
                <td class="p-3.5">Sin filtración; conserva color ámbar y notas intensas de madera</td>
                <td class="p-3.5 text-[#574A3D]">Tres Generaciones Añejo ($567 en Alianza) y 1800 Añejo ($585 en Chedraui / $599 en Alianza).</td>
              </tr>
              <tr class="hover:bg-[#F7F2EA]">
                <td class="p-3.5 font-bold text-[#486355]">Mezcal · Silvestre</td>
                <td class="p-3.5 font-mono">Agaves de 8 a 15 años</td>
                <td class="p-3.5">Destilación artesanal de Tobalá, Cupreata, Cuishe y Ensambles</td>
                <td class="p-3.5 text-[#574A3D]">400 Conejos Tobalá o Cuishe ($520 en Chedraui vs $650 en Alianza) y Amarás Cupreata ($719.20 en Alianza).</td>
              </tr>
              <tr class="hover:bg-[#F7F2EA]">
                <td class="p-3.5 font-bold text-[#2E5A44]">Mezcal · Reposado y Añejo</td>
                <td class="p-3.5 font-mono">2 a &ge;12 meses</td>
                <td class="p-3.5">Maduración en barrica de roble americano o encino</td>
                <td class="p-3.5 text-[#574A3D]">Amarás Reposado ($503.30 en Alianza), 400 Conejos Reposado ($520 en Chedraui) y 400 Conejos Añejo ($667.50).</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- FOOTER INFORMATIVO & AUDITORÍA DE DATOS -->
    <footer class="pt-6 pb-4 border-t border-[#DFD5C7] text-center text-xs text-[#574A3D] space-y-1.5">
      <p class="font-semibold text-[#1F1B16]">
        Cantina Familiar 2026 · Comparador Multitienda para Reunión Familiar
      </p>
      <p>
        Precios auditados en 5 cadenas: Bodegas Alianza, Sam's Club, Walmart, Chedraui y Soriana. Vigencias por tienda detalladas en el panel superior.
      </p>
      <p class="text-[11px] text-[#8A7B6B]">
        Corte de catálogo: __CORTE_AUDITORIA__ · Precios sujetos a cambios y existencias por tienda.
      </p>
    </footer>

  </div>

  <!-- APPLE HIG BOTTOM TAB BAR PARA MÓVIL (< 768px) -->
  <nav class="md:hidden fixed bottom-0 left-0 right-0 ios-tab-bar z-50 flex justify-around items-center h-16 px-2">
    <button onclick="cambiarTab('tab-rankings')" id="mob-btn-tab-rankings" class="mob-tab-btn flex flex-col items-center justify-center flex-1 py-1 text-[#784516] font-bold transition-colors">
      <span class="text-xl leading-none">🍾</span>
      <span class="text-[10px] mt-1">Catálogo</span>
    </button>
    <button onclick="cambiarTab('tab-versus')" id="mob-btn-tab-versus" class="mob-tab-btn flex flex-col items-center justify-center flex-1 py-1 text-[#8A7B6B] font-medium transition-colors">
      <span class="text-xl leading-none">⚔️</span>
      <span class="text-[10px] mt-1">Versus</span>
    </button>
    <button onclick="cambiarTab('tab-carrito')" id="mob-btn-tab-carrito" class="mob-tab-btn flex flex-col items-center justify-center flex-1 py-1 text-[#8A7B6B] font-medium transition-colors relative">
      <span class="text-xl leading-none">🛒</span>
      <span class="text-[10px] mt-1">Carrito</span>
      <span id="mob-badge-carrito" class="absolute top-0.5 right-5 bg-[#784516] text-white text-[9px] font-mono font-bold px-1.5 py-0.2 rounded-full">0</span>
    </button>
    <button onclick="cambiarTab('tab-matriz')" id="mob-btn-tab-matriz" class="mob-tab-btn flex flex-col items-center justify-center flex-1 py-1 text-[#8A7B6B] font-medium transition-colors">
      <span class="text-xl leading-none">📜</span>
      <span class="text-[10px] mt-1">Guía</span>
    </button>
  </nav>

  <!-- SCRIPT DE INTELIGENCIA DE NEGOCIO Y REACTIVIDAD -->
  <script>
    // 1. CARGA DE DATOS AUDITADOS (653 PRODUCTOS MULTITIENDA)
    const DATOS_COMPLETOS = __DATA_JSON__;

    // PARÁMETROS GLOBALES REACTIVOS (INICIAN EN 0 / EN BLANCO)
    let PRESUPUESTO_OBJETIVO = 0;
    let COOPERADORES_TOTAL = 0;

    // ESTADO DEL CARRITO DE COMPRAS (INICIA VACÍO)
    let canastaPersonalizada = {};

    // DEFINICIÓN JERÁRQUICA DE CATEGORÍA -> SUBTIPOS
    const SUBTIPOS_POR_MACRO = {
      "Todas": [
        { value: "Todas", label: "🌐 Todos los Tipos (653)" },
        { value: "Tequila - Añejo Cristalino", label: "🥃 Tequila · Añejo Cristalino (87)" },
        { value: "Tequila - Reposado Cristalino", label: "🥃 Tequila · Reposado Cristalino (68)" },
        { value: "Tequila - Añejo Tradicional", label: "🥃 Tequila · Añejo Tradicional (54)" },
        { value: "Mezcal - Silvestre", label: "🌵 Mezcal · Silvestre (47)" },
        { value: "Mezcal - Reposado", label: "🌵 Mezcal · Reposado (32)" },
        { value: "Mezcal - Espadín Joven", label: "🌵 Mezcal · Espadín Joven (17)" },
        { value: "Mezcal - Reposado Cristalino", label: "🌵 Mezcal · Reposado Cristalino (13)" },
        { value: "Mezcal - Añejo", label: "🌵 Mezcal · Añejo (10)" },
        { value: "Whisky - Blended Scotch", label: "🥃 Whisky · Blended Scotch (168)" },
        { value: "Licor de Whisky - Honey", label: "🍯 Licor Whisky · Honey (12)" },
        { value: "Vino - Tinto Clericot", label: "🍷 Vino · Tinto Clericot (145)" }
      ],
      "Tequila": [
        { value: "Todos_Macro", label: "🥃 Todos los Tipos de Tequila (209)" },
        { value: "Tequila - Añejo Cristalino", label: "✨ Añejo Cristalino (87)" },
        { value: "Tequila - Reposado Cristalino", label: "💎 Reposado Cristalino (68)" },
        { value: "Tequila - Añejo Tradicional", label: "🪵 Añejo Tradicional (54)" }
      ],
      "Mezcal": [
        { value: "Todos_Macro", label: "🌵 Todos los Tipos de Mezcal (119)" },
        { value: "Mezcal - Silvestre", label: "🌿 Silvestre: Tobalá / Cupreata / Cuishe (47)" },
        { value: "Mezcal - Reposado", label: "🪵 Reposado en Madera (32)" },
        { value: "Mezcal - Espadín Joven", label: "🔥 Espadín Joven (17)" },
        { value: "Mezcal - Reposado Cristalino", label: "💎 Reposado Cristalino (13)" },
        { value: "Mezcal - Añejo", label: "🥃 Añejo de Barrica (10)" }
      ],
      "Whisky": [
        { value: "Whisky - Blended Scotch", label: "🥃 Blended Scotch (168)" }
      ],
      "Licor de Whisky": [
        { value: "Licor de Whisky - Honey", label: "🍯 Licor de Whisky con Miel / Honey (12)" }
      ],
      "Vino": [
        { value: "Vino - Tinto Clericot", label: "🍷 Vino Tinto para Clericot y Mesa (145)" }
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
      if (cat.startsWith('Whisky')) return 'Whisky';
      if (cat.startsWith('Licor de Whisky') || cat.includes('Honey')) return 'Honey';
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
      actualizarSubtiposCatalogo();
      actualizarSubtiposVersus();
      poblarSelectoresAgregarPorCategoria();
      renderizarCanastasDinamicas();
      renderizarConstructorCanasta();
    });

    function actualizarSubtiposCatalogo() {
      const macro = document.getElementById("filtro-macro-categoria").value;
      const selectSub = document.getElementById("filtro-categoria");
      const opciones = SUBTIPOS_POR_MACRO[macro] || SUBTIPOS_POR_MACRO["Todas"];

      selectSub.innerHTML = "";
      opciones.forEach((op, i) => {
        const opt = document.createElement("option");
        opt.value = op.value;
        opt.innerText = op.label;
        if (i === 0) opt.selected = true;
        selectSub.appendChild(opt);
      });

      aplicarFiltros();
    }

    function actualizarSubtiposVersus() {
      const macro = document.getElementById("select-versus-macro").value;
      const selectSub = document.getElementById("select-versus-categoria-filtro");

      selectSub.innerHTML = "";
      if (macro === "Todas") {
        const optLibre = document.createElement("option");
        optLibre.value = "Todas";
        optLibre.innerText = "🔓 Comparar cualquier bebida del catálogo";
        selectSub.appendChild(optLibre);
      } else {
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

    function poblarSelectoresAgregarPorCategoria() {
      const cats = ['Tequila', 'Mezcal', 'Whisky', 'Honey', 'Vino'];
      cats.forEach(macro => {
        const select = document.getElementById(`select-agregar-${macro.toLowerCase()}`);
        if (!select) return;
        select.innerHTML = `<option value="">-- Seleccionar botella de ${macro} para agregar --</option>`;

        const prods = DATOS_COMPLETOS
          .map((p, idx) => ({ ...p, originalIndex: idx }))
          .filter(p => getMacroCategoria(p) === macro)
          .sort((a, b) => a.precio_por_litro - b.precio_por_litro);

        prods.forEach(p => {
          const opt = document.createElement("option");
          opt.value = p.originalIndex;
          const tipoCorto = p.categoria_comparable.split(" - ")[1] || p.categoria_comparable;
          // Acortar nombres excesivamente largos (> 46 caracteres) para evitar desfase visual en listas nativas
          const nombreLimpio = p.producto.length > 46 ? p.producto.slice(0, 45).trim() + "…" : p.producto;
          opt.innerText = `[${tipoCorto}] ${nombreLimpio} (${p.ml}ml · ${p.tienda}) — $${p.precio_promo.toFixed(2)} [$${p.precio_por_litro.toFixed(2)}/L]`;
          opt.title = `${p.producto} (${p.ml}ml · ${p.tienda}) — $${p.precio_promo.toFixed(2)}`;
          select.appendChild(opt);
        });
      });
    }

    function agregarBotellaDesdeSelect(macro) {
      const select = document.getElementById(`select-agregar-${macro.toLowerCase()}`);
      const idx = parseInt(select.value);
      if (isNaN(idx) || idx < 0) return;
      
      modificarCantidad(idx, 1);
      mostrarToast(`🍾 Agregado: ${DATOS_COMPLETOS[idx].producto}`);
      select.value = "";
    }

    function agregarDesdeTabla(idx) {
      modificarCantidad(idx, 1);
      mostrarToast(`🍾 Añadido al carrito: ${DATOS_COMPLETOS[idx].producto}`);
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
      mostrarToast("🗑️ Carrito vaciado");
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
        sub.innerHTML = `<span class="text-[#784516] font-bold">⚡ Recalculado en vivo (${txtPres} · ${txtPers}):</span> Toca cualquiera de las 3 propuestas dinámicas para cargarla al carrito.`;
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
              ⚡ Cargar Propuesta Dinámica
            </button>
          </div>
        `;
      });

      cont.innerHTML = html;
    }

    function cargarCanastaDinamica(perfil) {
      canastaPersonalizada = construirCanastaDinamica(perfil);
      renderizarConstructorCanasta();
      mostrarToast("✨ Canasta dinámica cargada en el carrito");
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
          cont.innerHTML = `
            <div class="p-4 text-center text-xs text-[#574A3D] md3-surface-low border-dashed">
              Sin botellas de ${macro} seleccionadas. Añade una desde el selector inferior o usa el Armador Dinámico.
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

            html += `
              <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 md3-surface-low hover:border-[#8A7B6B] transition-colors min-w-0">
                <div class="space-y-1 flex-1 min-w-0">
                  <div class="flex flex-wrap items-center gap-1.5">
                    <span class="badge ${claseBadgeColor} border text-[10px]">${item.categoria_comparable}</span>
                    ${tiendaBadge}
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
                </div>

                <!-- CONTROLES DE CANTIDAD TÁCTILES (HIG 44pt) -->
                <div class="flex items-center justify-between sm:justify-end gap-3 border-t sm:border-t-0 pt-2.5 sm:pt-0 border-[#DFD5C7] sm:flex-shrink-0">
                  <div class="flex items-center gap-1 bg-white p-1 rounded-full border border-[#D6C8B8]">
                    <button onclick="modificarCantidad(${idx}, -1)" class="w-8 h-8 flex items-center justify-center rounded-full bg-[#EFE8DC] hover:bg-[#E6DDD0] text-sm font-bold text-[#1F1B16] transition-colors cursor-pointer">
                      −
                    </button>
                    <input type="number" min="0" max="99" value="${cant}" 
                           onchange="fijarCantidad(${idx}, this.value)"
                           class="w-10 text-center bg-transparent font-mono font-bold text-sm text-[#1F1B16] focus:outline-none">
                    <button onclick="modificarCantidad(${idx}, 1)" class="w-8 h-8 flex items-center justify-center rounded-full bg-[#EFE8DC] hover:bg-[#E6DDD0] text-sm font-bold text-[#1F1B16] transition-colors cursor-pointer">
                      +
                    </button>
                  </div>

                  <div class="text-right min-w-[5.5rem]">
                    <div class="text-[11px] text-[#574A3D]">Subtotal:</div>
                    <div class="font-bold font-mono text-sm text-[#784516]">$${costoLinea.toFixed(2)}</div>
                  </div>

                  <button onclick="eliminarProducto(${idx})" title="Quitar botella" class="w-8 h-8 flex items-center justify-center rounded-full text-[#8A7B6B] hover:text-[#753B47] hover:bg-[#FAD9DF] transition-colors cursor-pointer">
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
          barraEl.className = "bg-[#9F1239] h-full rounded-full transition-all duration-300";
          alertaBox.className = "p-3 rounded-xl flex items-center justify-between text-xs bg-[#FAD9DF] border border-[#E5B3BC]";
          labelSobrante.innerText = "⚠️ Excedente sobre presupuesto:";
          labelSobrante.className = "text-[#753B47] font-bold";
          valSobrante.innerText = `-$${Math.abs(sobrante).toLocaleString('es-MX', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
          valSobrante.className = "text-[#753B47] font-black text-sm font-mono";
        } else {
          barraEl.className = "bg-[#784516] h-full rounded-full transition-all duration-300";
          alertaBox.className = "p-3 rounded-xl flex items-center justify-between text-xs bg-[#D3E8DC] border border-[#B7D6C5]";
          labelSobrante.innerText = "Presupuesto Disponible:";
          labelSobrante.className = "text-[#0B2016] font-medium";
          valSobrante.innerText = `+$${sobrante.toLocaleString('es-MX', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
          valSobrante.className = "text-[#0B2016] font-bold text-sm font-mono";
        }
      } else {
        document.getElementById("sim-porcentaje-barra").innerText = `Sin tope`;
        barraEl.style.width = `0%`;
        alertaBox.className = "p-3 rounded-xl flex items-center justify-between text-xs md3-surface-low";
        labelSobrante.innerText = "Presupuesto Objetivo:";
        labelSobrante.className = "text-[#574A3D] font-medium";
        valSobrante.innerText = "Ingresa monto arriba";
        valSobrante.className = "text-[#784516] font-mono text-xs font-semibold";
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
      let texto = `🥃 LISTA DE COMPRA MULTITIENDA - CANTINA FAMILIAR 2026\n`;
      if (PRESUPUESTO_OBJETIVO > 0 || COOPERADORES_TOTAL > 0) {
        texto += `Presupuesto: ${PRESUPUESTO_OBJETIVO > 0 ? '$' + PRESUPUESTO_OBJETIVO.toFixed(2) : 'Libre'} | Personas: ${COOPERADORES_TOTAL > 0 ? COOPERADORES_TOTAL : 'Sin definir'}\n`;
      }
      texto += `--------------------------------------------------------\n`;

      let total = 0;
      let subTiendas = {
        "Bodegas Alianza": 0,
        "Sam's Club": 0,
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
            texto += `• ${cant}× ${item.producto} (${item.ml}ml) - $${item.precio_promo.toFixed(2)} c/u [Sub: $${sub.toFixed(2)}] (${item.tienda})\n  🔗 ${item.url}\n`;
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
      texto += `📅 VIGENCIAS DE OFERTAS POR TIENDA:\n__RESUMEN_WHATSAPP_VIGENCIAS__\n`;

      navigator.clipboard.writeText(texto).then(() => {
        mostrarToast("📋 ¡Lista de compras copiada al portapapeles!");
      }).catch(() => {
        mostrarToast("No se pudo copiar automáticamente.");
      });
    }

    // CAMBIAR PESTAÑA (SINCRONIZA BARRA DESKTOP MD3 Y TAB BAR MÓVIL APPLE HIG)
    function cambiarTab(idTab) {
      document.querySelectorAll(".tab-content").forEach(el => el.classList.add("hidden"));
      document.getElementById(idTab).classList.remove("hidden");

      // Desktop MD3 Segmented Bar
      document.querySelectorAll(".tab-btn").forEach(el => {
        el.classList.remove("bg-white", "text-[#1F1B16]", "shadow-sm");
        el.classList.add("text-[#574A3D]");
      });
      const btn = document.getElementById("btn-" + idTab);
      if (btn) {
        btn.classList.add("bg-white", "text-[#1F1B16]", "shadow-sm");
        btn.classList.remove("text-[#574A3D]");
      }

      // Mobile iOS HIG Bottom Tab Bar
      document.querySelectorAll(".mob-tab-btn").forEach(el => {
        el.classList.remove("text-[#784516]", "font-bold");
        el.classList.add("text-[#8A7B6B]", "font-medium");
      });
      const mobBtn = document.getElementById("mob-btn-" + idTab);
      if (mobBtn) {
        mobBtn.classList.add("text-[#784516]", "font-bold");
        mobBtn.classList.remove("text-[#8A7B6B]", "font-medium");
      }

      if (idTab === 'tab-rankings') {
        renderizarGraficoTop10();
      }
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function aplicarFiltros() {
      const busq = document.getElementById("filtro-busqueda").value.toLowerCase();
      const macroCat = document.getElementById("filtro-macro-categoria").value;
      const subCat = document.getElementById("filtro-categoria").value;
      const tienda = document.getElementById("filtro-tienda").value;
      const soloDesc = document.getElementById("filtro-descuento").checked;

      datosFiltrados = DATOS_COMPLETOS.filter(item => {
        const matchBusq = !busq || item.producto.toLowerCase().includes(busq) || item.marca.toLowerCase().includes(busq);
        const matchMacro = (macroCat === 'Todas') || (item.categoria === macroCat);
        const matchSub = (subCat === 'Todas' || subCat === 'Todos_Macro') || (item.categoria_comparable === subCat);
        const matchTienda = (tienda === 'Todas') || (item.tienda === tienda);
        const matchDesc = !soloDesc || (item.ahorro_verificable > 0);
        return matchBusq && matchMacro && matchSub && matchTienda && matchDesc;
      });

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
    }

    function ordenarPor(col) {
      if (columnaOrden === col) ordenAsc = !ordenAsc;
      else { columnaOrden = col; ordenAsc = true; }
      aplicarFiltros();
    }

    function renderizarTabla() {
      const tbody = document.getElementById("tabla-productos-body");
      tbody.innerHTML = "";

      const inicio = (paginaActual - 1) * itemsPorPagina;
      const fin = Math.min(inicio + itemsPorPagina, datosFiltrados.length);
      const paginaItems = datosFiltrados.slice(inicio, fin);

      if (paginaItems.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" class="p-8 text-center text-[#574A3D]">No se encontraron botellas con los filtros seleccionados.</td></tr>`;
        return;
      }

      paginaItems.forEach(item => {
        const tr = document.createElement("tr");
        tr.className = "hover:bg-[#F7F2EA] transition-colors";

        const ahorroBadge = item.ahorro_verificable > 0 
          ? `<span class="badge bg-[#D3E8DC] text-[#0B2016] border border-[#B7D6C5]">-$${item.ahorro_verificable.toFixed(2)} (${item.porcentaje_ahorro}%)</span>`
          : `<span class="text-[#8A7B6B] text-xs">Precio regular</span>`;

        const tiendaBadge = getBadgeTienda(item.tienda, false);
        const originalIndex = DATOS_COMPLETOS.indexOf(item);

        tr.innerHTML = `
          <td class="p-3.5 font-medium text-[#1F1B16]">
            <a href="${item.url}" target="_blank" rel="noopener noreferrer" 
               class="hover:underline text-[#1F1B16] hover:text-[#784516] flex items-center gap-1 group font-semibold" 
               title="Ver ${item.producto} en tienda oficial ${item.tienda}">
              <span class="line-clamp-1">${item.producto}</span>
              <span class="text-[10px] text-[#8A7B6B] group-hover:text-[#784516] flex-shrink-0">↗</span>
            </a>
            <div class="text-xs text-[#574A3D] flex items-center gap-1.5 mt-0.5">
              <span>${item.marca}</span>
              <span class="sm:hidden">· ${item.ml}ml</span>
            </div>
          </td>
          <td class="p-3.5 text-xs hidden sm:table-cell">
            <span class="badge bg-[#EFE8DC] border border-[#D6C8B8] text-[#574A3D]">${item.categoria_comparable}</span>
          </td>
          <td class="p-3.5 text-xs font-mono text-[#574A3D] hidden md:table-cell">${item.ml} ml</td>
          <td class="p-3.5 font-bold text-[#1F1B16] font-mono">$${item.precio_promo.toFixed(2)}</td>
          <td class="p-3.5 font-extrabold text-[#784516] font-mono">$${item.precio_por_litro.toFixed(2)}</td>
          <td class="p-3.5 hidden lg:table-cell">${ahorroBadge}</td>
          <td class="p-3.5">${tiendaBadge}</td>
          <td class="p-3.5 text-center">
            <div class="flex items-center justify-center gap-1.5">
              <button onclick="agregarDesdeTabla(${originalIndex})" class="px-3 py-1.5 text-xs md3-btn-tonal cursor-pointer whitespace-nowrap">
                + Carrito
              </button>
              <a href="${item.url}" target="_blank" rel="noopener noreferrer" 
                 class="w-7 h-7 rounded-full border border-[#D6C8B8] hover:bg-[#EFE8DC] text-[#784516] inline-flex items-center justify-center transition-colors text-xs" 
                 title="Abrir ${item.producto} en ${item.tienda}">
                ↗
              </a>
            </div>
          </td>
        `;
        tbody.appendChild(tr);
      });

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
        container.innerHTML = "<div class='text-xs text-[#574A3D] p-4'>Sin datos para graficar</div>";
        return;
      }

      const maxLitro = Math.max(...top10.map(d => d.precio_por_litro));

      let svgHtml = `<div class="space-y-2.5 py-2">`;
      top10.forEach((item, idx) => {
        const anchoPorcentaje = Math.max(15, (item.precio_por_litro / maxLitro) * 100);
        const colorBarra = idx === 0
          ? "bg-[#486355]"
          : (idx < 3 ? "bg-[#784516]" : "bg-[#B89F86]");

        svgHtml += `
          <div class="space-y-1">
            <div class="flex justify-between text-xs">
              <span class="font-semibold text-[#1F1B16] truncate max-w-md">${idx + 1}. ${item.producto} <span class="text-[#574A3D] font-normal">(${item.tienda})</span></span>
              <span class="font-bold font-mono text-[#784516]">$${item.precio_por_litro.toFixed(2)} / L</span>
            </div>
            <div class="w-full bg-[#EFE8DC] h-3 rounded-full overflow-hidden">
              <div class="${colorBarra} h-full rounded-full transition-all duration-500" style="width: ${anchoPorcentaje}%"></div>
            </div>
          </div>
        `;
      });
      svgHtml += `</div>`;
      container.innerHTML = svgHtml;
    }

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
        btn.className = "badge bg-[#F8E2C8] text-[#2B1500] border border-[#E5C8A3] hover:bg-[#F2D5B3] px-3 py-2 text-xs transition-colors cursor-pointer text-left";
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
          ? `<span class="badge bg-[#D3E8DC] text-[#0B2016] border border-[#B7D6C5]">Ahorro: -$${p.ahorro_verificable.toFixed(2)} (${p.porcentaje_ahorro}%)</span>`
          : `<span class="text-xs text-[#8A7B6B]">Precio Regular</span>`;

        const tiendaBadge = getBadgeTienda(p.tienda, false);

        return `
          <div class="md3-card border-t-4 ${colorBorder} p-5 space-y-4">
            <div class="flex justify-between items-start">
              <span class="badge bg-[#EFE8DC] border border-[#D6C8B8] font-bold text-xs text-[#1F1B16]">Contendiente ${letra}</span>
              <div class="flex gap-1.5">${tiendaBadge}${ahorro}</div>
            </div>

            <div>
              <span class="text-xs font-mono text-[#784516] font-bold">${p.categoria_comparable}</span>
              <h4 class="text-lg font-bold font-display-md3 text-[#1F1B16] mt-0.5 leading-snug">${p.producto}</h4>
              <p class="text-xs text-[#574A3D]">${p.marca} · ${p.ml} ml · ${getABV(p)}</p>
            </div>

            <div class="grid grid-cols-2 gap-3 md3-surface-low p-3.5">
              <div>
                <span class="text-[11px] text-[#574A3D]">Precio Botella:</span>
                <div class="text-xl font-bold font-mono text-[#1F1B16]">$${p.precio_promo.toFixed(2)}</div>
              </div>
              <div>
                <span class="text-[11px] text-[#574A3D]">Precio / Litro:</span>
                <div class="text-xl font-bold font-mono text-[#784516]">$${p.precio_por_litro.toFixed(2)}</div>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-3 md3-surface-low p-3 text-xs">
              <div>
                <span class="text-[11px] text-[#574A3D]">Costo por ${labelDosis}:</span>
                <div class="text-base font-bold font-mono text-[#486355] mt-0.5">$${costoTrago.toFixed(2)}</div>
              </div>
              <div>
                <span class="text-[11px] text-[#574A3D]">Rendimiento por Envase:</span>
                <div class="text-base font-bold font-mono text-[#784516] mt-0.5">~${tragosTotales} ${p.categoria_comparable.includes("Vino") ? "copas" : "tragos"}</div>
              </div>
            </div>

            <div class="text-xs md3-surface-tonal p-3 text-[#574A3D] leading-relaxed">
              <strong class="text-[#1F1B16]">Perfil de Barrica:</strong> ${getMaduracionInfo(p)}
            </div>

            <div class="pt-2 flex justify-between items-center text-xs border-t border-[#DFD5C7]">
              <a href="${p.url}" target="_blank" class="text-xs font-semibold text-[#784516] hover:underline">Ver en tienda en línea ↗</a>
              <button onclick="modificarCantidad(${DATOS_COMPLETOS.indexOf(p)}, 1); mostrarToast('🍾 Añadido al carrito: ${p.producto}');" class="px-4 py-2 md3-btn-filled text-xs cursor-pointer">
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
        <div class="space-y-4">
          <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-[#DFD5C7] pb-4">
            <div class="space-y-1">
              <div class="flex items-center gap-2">
                <span class="badge bg-[#F8E2C8] text-[#784516] border border-[#E5C8A3] text-xs">
                  ${badgePersonasTexto}
                </span>
              </div>
              <h4 class="text-base font-bold font-display-md3 text-[#1F1B16] mt-1">
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
          <div class="space-y-1.5">
            <span class="badge bg-[#D3E8DC] text-[#0B2016] border border-[#B7D6C5] uppercase">Veredicto de Compra</span>
            <h3 class="text-xl font-bold font-display-md3 text-[#1F1B16]">
              🏆 Mejor Rendimiento $/Litro: <span class="text-[#784516]">${ganadorLitro.producto} (${ganadorLitro.tienda})</span>
            </h3>
            <p class="text-xs text-[#574A3D] max-w-3xl leading-relaxed">
              Ofrece un costo estandarizado de <strong class="text-[#1F1B16]">$${ganadorLitro.precio_por_litro.toFixed(2)} por litro</strong> frente a 
              <strong>$${perdedorLitro.precio_por_litro.toFixed(2)}/L</strong> de ${perdedorLitro.producto} (${perdedorLitro.tienda}), 
              lo que equivale a un ahorro real de <strong class="text-[#486355]">$${difLitro.toFixed(2)} por cada litro (${pctLitro}%)</strong>.
            </p>
          </div>
          <div class="flex items-center gap-2 flex-wrap">
            <a href="${ganadorLitro.url}" target="_blank" rel="noopener noreferrer" 
               class="px-4 py-2.5 md3-btn-tonal text-xs whitespace-nowrap inline-flex items-center gap-1.5"
               title="Abrir ${ganadorLitro.producto} en ${ganadorLitro.tienda}">
              <span>Ver en ${ganadorLitro.tienda}</span> <span>↗</span>
            </a>
            <button onclick="modificarCantidad(${DATOS_COMPLETOS.indexOf(ganadorLitro)}, 1); mostrarToast('🏆 Ganador añadido al carrito: ${ganadorLitro.producto}');" class="px-5 py-2.5 md3-btn-filled text-xs whitespace-nowrap cursor-pointer">
              + Agregar Ganador al Carrito
            </button>
          </div>
        </div>
      `;
    }
  </script>
</body>
</html>
"""

html_final = (
    html_template
    .replace("__DATA_JSON__", datos_json_str)
    .replace("__CORTE_AUDITORIA__", CONFIG_VIGENCIA["corte_auditoria"])
    .replace("__RESUMEN_WHATSAPP_VIGENCIAS__", CONFIG_VIGENCIA["resumen_whatsapp"])
)

with open(LOCAL_HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html_final)

with open(INDEX_HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html_final)

if HTML_ARTIFACT_PATH:
    try:
        os.makedirs(HTML_ARTIFACT_PATH.parent, exist_ok=True)
        with open(HTML_ARTIFACT_PATH, "w", encoding="utf-8") as f:
            f.write(html_final)
    except Exception:
        pass

print(f"[OK] Dashboard v6.0 sincronizado exitosamente:")
print(f"  - Local:    {LOCAL_HTML_PATH} ({len(html_final):,} bytes)")
print(f"  - Root:     {INDEX_HTML_PATH} ({len(html_final):,} bytes)")
