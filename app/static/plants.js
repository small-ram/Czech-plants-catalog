const state = {
  q: "",
  seasonal: true,
  trvanlive: false,
  jadro: false,
  limit: "48",
};

let seasonalDefault = null;
let apiBase = "";
let initialSummary = null;
let initialOptions = null;

const API_BASE_CANDIDATES = ["", "http://127.0.0.1:8766"];

const els = {
  summaryStats: document.getElementById("plants-summary-stats"),
  results: document.getElementById("plants-results"),
  resultsTitle: document.getElementById("plants-results-title"),
  template: document.getElementById("plant-card-template"),
  resetBtn: document.getElementById("plants-reset-btn"),
  q: document.getElementById("plants-q"),
  seasonal: document.getElementById("plants-seasonal"),
  seasonalNote: document.getElementById("plants-seasonal-note"),
  trvanlive: document.getElementById("plants-trvanlive"),
  jadro: document.getElementById("plants-jadro"),
  limit: document.getElementById("plants-limit"),
};

function debounce(fn, delay = 220) {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
}

function pluralizePlants(count) {
  if (count === 1) return "1 rostlina";
  if (count >= 2 && count <= 4) return `${count} rostliny`;
  return `${count} rostlin`;
}

function parseInitialState() {
  const params = new URLSearchParams(window.location.search);
  state.q = params.get("q") || "";
  state.seasonal = params.has("seasonal") ? params.get("seasonal") === "1" : true;
  state.trvanlive = params.get("trvanlive") === "1";
  state.jadro = params.get("jadro") === "1";
  state.limit = params.get("limit") || state.limit;
}

function syncControls() {
  els.q.value = state.q;
  els.seasonal.checked = state.seasonal;
  els.trvanlive.checked = state.trvanlive;
  els.jadro.checked = state.jadro;
  els.limit.value = state.limit;
}

function buildSearchParams() {
  const params = new URLSearchParams();
  if (state.q) params.set("q", state.q);
  if (state.seasonal) params.set("seasonal", "1");
  if (state.trvanlive) params.set("trvanlive", "1");
  if (state.jadro) params.set("jadro", "1");
  if (state.limit) params.set("limit", state.limit);
  return params;
}

function syncUrl() {
  const params = buildSearchParams();
  const basePath = window.location.pathname === "/static/plants.html" ? "/static/plants.html" : "/plants";
  const nextUrl = params.toString() ? `${basePath}?${params.toString()}` : basePath;
  window.history.replaceState(null, "", nextUrl);
}

function apiUrl(path) {
  return apiBase ? `${apiBase}${path}` : path;
}

function appUrl(path) {
  return apiBase ? `${apiBase}${path}` : path;
}

async function fetchJsonAbsolute(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

async function fetchJson(path) {
  return fetchJsonAbsolute(apiUrl(path));
}

function isCompatibleOptions(payload) {
  return Boolean(payload && payload.seasonal_default && Array.isArray(payload.months));
}

async function discoverApiBase() {
  for (const candidate of API_BASE_CANDIDATES) {
    try {
      const [summary, options] = await Promise.all([
        fetchJsonAbsolute(candidate ? `${candidate}/api/summary` : "/api/summary"),
        fetchJsonAbsolute(candidate ? `${candidate}/api/options` : "/api/options"),
      ]);
      if (isCompatibleOptions(options)) {
        apiBase = candidate;
        initialSummary = summary;
        initialOptions = options;
        return;
      }
    } catch (_error) {
      // Try the next candidate.
    }
  }
  throw new Error("Nepodařilo se najít kompatibilní katalogové API.");
}

function renderSummary(summary) {
  els.summaryStats.innerHTML = "";
  const cards = [
    ["Rostliny", summary.counts.plants],
    ["Použití", summary.counts.uses],
    ["Trvanlivé formy", summary.counts.durable_forms],
    ["Praktické jádro", summary.counts.core_items],
  ];

  cards.forEach(([label, value]) => {
    const card = document.createElement("div");
    card.className = "stat-card";
    card.innerHTML = `<strong>${value}</strong><span>${label}</span>`;
    els.summaryStats.appendChild(card);
  });
}

function renderSeasonalNote(windowConfig = seasonalDefault) {
  if (!els.seasonalNote) return;

  if (!state.seasonal) {
    els.seasonalNote.textContent = "Sezónní filtr je vypnutý, takže galerie ukazuje všechny rostliny podle ostatních filtrů.";
    return;
  }

  if (!windowConfig) {
    els.seasonalNote.textContent = "Sezónní filtr je aktivní.";
    return;
  }

  els.seasonalNote.textContent = `Výchozí okno pro ${windowConfig.today_label}: ${windowConfig.label}. ${windowConfig.reason}.`;
}

function renderMeta(values) {
  return values
    .filter(Boolean)
    .map((value) => `<span class="meta-pill">${value}</span>`)
    .join("");
}

function renderBadges(result) {
  const badges = [];
  if (result.durable_use_count) badges.push(`<span class="badge">Trvanlivé ${result.durable_use_count}</span>`);
  if (result.core_use_count) badges.push(`<span class="badge core">Jádro ${result.core_use_count}</span>`);
  if (result.processing_use_count) badges.push(`<span class="badge">Zpracování ${result.processing_use_count}</span>`);
  if (result.photos?.length) badges.push(`<span class="badge">Media ${result.photos.length}</span>`);
  if (result.primary_photo_kind_label) {
    const kindClass =
      result.primary_photo_kind === "photo"
        ? "media-photo"
        : result.primary_photo_kind === "illustration"
          ? "media-illustration"
          : result.primary_photo_kind === "auto_cover"
            ? "media-auto-cover"
            : "";
    badges.push(`<span class="badge ${kindClass}">${result.primary_photo_kind_label}</span>`);
  }
  return badges.join("");
}

function renderPlantCard(result) {
  const fragment = els.template.content.cloneNode(true);
  const card = fragment.querySelector(".plant-card");
  const image = fragment.querySelector(".plant-card-image");
  const placeholder = fragment.querySelector(".plant-card-placeholder");

  fragment.querySelector(".card-title").textContent = result.cesky_nazev_hlavni;
  fragment.querySelector(".card-subtitle").textContent = result.vedecky_nazev_hlavni;
  fragment.querySelector(".card-badges").innerHTML = renderBadges(result);
  fragment.querySelector(".meta-grid").innerHTML = renderMeta([
    result.status_cetnost_reprezentativni,
    result.top_evidence_rank ? `Top důkaznost ${result.top_evidence_rank}` : "",
    `${result.pocet_ceskych_aliasu} českých aliasů`,
  ]);
  fragment.querySelector(".plant-card-status").textContent =
    result.status_v_cr_text || "Status v ČR zatím není v datech vyplněný.";
  fragment.querySelector(".plant-use-count").textContent = result.use_count;
  fragment.querySelector(".plant-durable-count").textContent = result.durable_use_count;
  fragment.querySelector(".plant-core-count").textContent = result.core_use_count;

  const profileLink = fragment.querySelector(".plant-profile-link");
  const exportLink = fragment.querySelector(".plant-export-link");
  if (result.plant_id) {
    profileLink.href = appUrl(`/plant/${encodeURIComponent(result.plant_id)}`);
    exportLink.href = appUrl(`/export/plant/${encodeURIComponent(result.plant_id)}.md`);
  } else {
    profileLink.href = appUrl(`/use/${encodeURIComponent(result.first_use_id)}`);
    profileLink.textContent = "První použití";
    exportLink.href = appUrl(`/?q=${encodeURIComponent(result.cesky_nazev_hlavni)}`);
    exportLink.textContent = "Hledat";
  }

  if (result.primary_photo) {
    image.src = result.primary_photo;
    image.alt = result.photos?.[0]?.alt || result.cesky_nazev_hlavni;
    image.title = [result.photos?.[0]?.credit, result.photos?.[0]?.source_name].filter(Boolean).join(" · ");
    image.hidden = false;
    placeholder.hidden = true;
  } else {
    card.classList.add("plant-card-no-photo");
  }

  return fragment;
}

function aggregatePlantsFromSearch(payload) {
  const byKey = new Map();

  (payload.results || []).forEach((result) => {
    const key = `${result.cesky_nazev_hlavni}|||${result.vedecky_nazev_hlavni}`;
    if (!byKey.has(key)) {
      byKey.set(key, {
        plant_id: result.plant_id || "",
        first_use_id: result.use_id,
        cesky_nazev_hlavni: result.cesky_nazev_hlavni,
        vedecky_nazev_hlavni: result.vedecky_nazev_hlavni,
        status_v_cr_text: result.status_v_cr_text || "",
        status_cetnost_reprezentativni: result.status_cetnost_reprezentativni || "",
        pocet_ceskych_aliasu: result.pocet_ceskych_aliasu || 0,
        use_count: 0,
        durable_use_count: 0,
        core_use_count: 0,
        processing_use_count: 0,
        top_evidence_rank: 0,
        photos: result.photos || [],
        primary_photo: result.primary_photo || null,
        primary_photo_kind: result.primary_photo_kind || null,
        primary_photo_kind_label: result.primary_photo_kind_label || null,
      });
    }

    const aggregate = byKey.get(key);
    aggregate.use_count += 1;
    if (result.je_trvanlive_1m_plus) aggregate.durable_use_count += 1;
    if (result.je_v_jadru_bezne_1m_plus) aggregate.core_use_count += 1;
    if (result.processing_methods_text || result.forma_uchovani_text) aggregate.processing_use_count += 1;
    aggregate.top_evidence_rank = Math.max(aggregate.top_evidence_rank, Number(result.dukaznost_rank || 0));
  });

  const results = Array.from(byKey.values())
    .sort((a, b) => {
      return (
        b.core_use_count - a.core_use_count ||
        b.durable_use_count - a.durable_use_count ||
        b.processing_use_count - a.processing_use_count ||
        b.top_evidence_rank - a.top_evidence_rank ||
        a.cesky_nazev_hlavni.localeCompare(b.cesky_nazev_hlavni, "cs")
      );
    })
    .slice(0, Number(state.limit || "48"));

  return { count: results.length, results, compatibility_mode: true };
}

async function fetchPlantsPayload() {
  const params = buildSearchParams().toString();
  const plantsUrl = params ? `/api/plants?${params}` : "/api/plants";

  try {
    return await fetchJson(plantsUrl);
  } catch (error) {
    if (!String(error.message).includes("404")) {
      throw error;
    }
  }

  const fallbackParams = new URLSearchParams();
  if (state.q) fallbackParams.set("q", state.q);
  if (state.seasonal) fallbackParams.set("seasonal", "1");
  if (state.trvanlive) fallbackParams.set("trvanlive", "1");
  if (state.jadro) fallbackParams.set("jadro", "1");
  fallbackParams.set("limit", "200");

  const searchPayload = await fetchJson(`/api/search?${fallbackParams.toString()}`);
  return aggregatePlantsFromSearch(searchPayload);
}

function renderResults(payload) {
  els.results.innerHTML = "";
  els.resultsTitle.textContent = pluralizePlants(payload.count);

  if (!payload.results.length) {
    els.results.innerHTML = `
      <div class="empty-state">
        Pro zadané filtry teď nevyšla žádná rostlina. Zkus širší hledání nebo vypnout některý filtr.
      </div>
    `;
    return;
  }

  payload.results.forEach((result) => {
    els.results.appendChild(renderPlantCard(result));
  });
}

async function loadPlants() {
  els.results.innerHTML = '<div class="empty-state">Načítám galerii rostlin…</div>';
  const payload = await fetchPlantsPayload();
  syncUrl();
  renderSeasonalNote(payload.seasonal_window || seasonalDefault);
  renderResults(payload);
}

function resetFilters() {
  state.q = "";
  state.seasonal = true;
  state.trvanlive = false;
  state.jadro = false;
  state.limit = "48";
  syncControls();
  renderSeasonalNote();
  loadPlants();
}

function bindControls() {
  const debouncedLoad = debounce(loadPlants);

  els.q.addEventListener("input", (event) => {
    state.q = event.target.value.trim();
    debouncedLoad();
  });

  els.seasonal.addEventListener("change", (event) => {
    state.seasonal = event.target.checked;
    syncControls();
    renderSeasonalNote();
    loadPlants();
  });

  els.trvanlive.addEventListener("change", (event) => {
    state.trvanlive = event.target.checked;
    loadPlants();
  });

  els.jadro.addEventListener("change", (event) => {
    state.jadro = event.target.checked;
    loadPlants();
  });

  els.limit.addEventListener("change", (event) => {
    state.limit = event.target.value;
    loadPlants();
  });

  els.resetBtn.addEventListener("click", resetFilters);
}

async function init() {
  parseInitialState();
  await discoverApiBase();
  syncControls();
  bindControls();

  try {
    const summary = initialSummary;
    const options = initialOptions;
    const plants = await fetchPlantsPayload();
    seasonalDefault = options.seasonal_default || null;
    renderSummary(summary);
    syncUrl();
    renderSeasonalNote(plants.seasonal_window || seasonalDefault);
    renderResults(plants);
  } catch (error) {
    els.results.innerHTML = `<div class="empty-state">Nepodařilo se načíst galerii: ${error.message}</div>`;
  }
}

init();
