const C = window.CatalogSite;

const state = {
  q: "",
  seasonal: true,
  trvanlive: false,
  jadro: false,
  limit: "48",
};

let bundle = null;
let plantsById = new Map();

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
  const nextUrl = params.toString() ? `?${params.toString()}` : window.location.pathname;
  window.history.replaceState(null, "", nextUrl);
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
    card.innerHTML = `<strong>${value}</strong><span>${C.escapeHtml(label)}</span>`;
    els.summaryStats.appendChild(card);
  });
}

function renderSeasonalNote() {
  if (!state.seasonal) {
    els.seasonalNote.textContent = "Sezónní filtr je vypnutý, takže galerie ukazuje všechny rostliny podle ostatních filtrů.";
    return;
  }

  const windowConfig = C.seasonalWindowPayload();
  els.seasonalNote.textContent = `Výchozí okno pro ${windowConfig.today_label}: ${windowConfig.label}. ${windowConfig.reason}.`;
}

function renderBadges(result) {
  const badges = [];
  if (result.durable_use_count) badges.push(`<span class="badge">Trvanlivé ${result.durable_use_count}</span>`);
  if (result.core_use_count) badges.push(`<span class="badge core">Jádro ${result.core_use_count}</span>`);
  if (result.processing_use_count) badges.push(`<span class="badge">Zpracování ${result.processing_use_count}</span>`);
  if (result.photos?.length) badges.push(`<span class="badge">Media ${result.photos.length}</span>`);
  return badges.join("");
}

function renderPlantCard(result) {
  const fragment = els.template.content.cloneNode(true);
  const image = fragment.querySelector(".plant-card-image");
  const placeholder = fragment.querySelector(".plant-card-placeholder");

  fragment.querySelector(".card-title").textContent = result.cesky_nazev_hlavni;
  fragment.querySelector(".card-subtitle").textContent = result.vedecky_nazev_hlavni;
  fragment.querySelector(".card-badges").innerHTML = renderBadges(result);
  fragment.querySelector(".meta-grid").innerHTML = C.renderMeta([
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
  profileLink.href = C.siteUrl(`plant/${encodeURIComponent(result.plant_id)}/`);
  exportLink.href = C.siteUrl(`export/plant/${encodeURIComponent(result.plant_id)}.md`);

  if (result.primary_photo) {
    image.src = C.assetUrl(result.primary_photo);
    image.alt = result.primary_photo_alt || result.cesky_nazev_hlavni;
    image.title = [result.primary_photo_credit, result.primary_photo_source_name].filter(Boolean).join(" · ");
    image.hidden = false;
    placeholder.hidden = true;
  }

  return fragment;
}

function renderResults(results) {
  els.results.innerHTML = "";
  if (!results.length) {
    els.results.innerHTML = '<div class="empty-state">Tomu neodpovídá žádná rostlina. Zkus obecnější hledání nebo vypnout některý filtr.</div>';
    return;
  }
  results.forEach((result) => {
    els.results.appendChild(renderPlantCard(result));
  });
}

function relevantUses() {
  const query = state.q.trim().toLowerCase();
  const seasonalWindow = C.seasonalWindowPayload();

  return (bundle.uses || []).filter((use) => {
    if (state.seasonal && !seasonalWindow.months.some((month) => C.monthMatches(use, month))) return false;
    if (state.trvanlive && !C.normalizeBooleanish(use.je_trvanlive_1m_plus)) return false;
    if (state.jadro && !C.normalizeBooleanish(use.je_v_jadru_bezne_1m_plus)) return false;

    if (!query) return true;
    const plant = plantsById.get(use.plant_id);
    return Boolean(plant && (plant.search_text || "").includes(query));
  });
}

function aggregatePlants() {
  const aggregates = new Map();

  relevantUses().forEach((use) => {
    const plant = plantsById.get(use.plant_id);
    if (!plant) return;
    if (!aggregates.has(use.plant_id)) {
      aggregates.set(use.plant_id, {
        ...plant,
        use_count: 0,
        durable_use_count: 0,
        core_use_count: 0,
        processing_use_count: 0,
        top_evidence_rank: 0,
      });
    }

    const aggregate = aggregates.get(use.plant_id);
    aggregate.use_count += 1;
    if (C.normalizeBooleanish(use.je_trvanlive_1m_plus)) aggregate.durable_use_count += 1;
    if (C.normalizeBooleanish(use.je_v_jadru_bezne_1m_plus)) aggregate.core_use_count += 1;
    if (Number(use.processing_methods_count || 0) > 0 || use.forma_uchovani_text) aggregate.processing_use_count += 1;
    aggregate.top_evidence_rank = Math.max(aggregate.top_evidence_rank, Number(use.dukaznost_rank || 0));
  });

  return Array.from(aggregates.values())
    .sort((a, b) => {
      if (b.core_use_count !== a.core_use_count) return b.core_use_count - a.core_use_count;
      if (b.durable_use_count !== a.durable_use_count) return b.durable_use_count - a.durable_use_count;
      if (b.processing_use_count !== a.processing_use_count) return b.processing_use_count - a.processing_use_count;
      if (b.top_evidence_rank !== a.top_evidence_rank) return b.top_evidence_rank - a.top_evidence_rank;
      return a.cesky_nazev_hlavni.localeCompare(b.cesky_nazev_hlavni, "cs");
    });
}

function syncState() {
  state.q = els.q.value.trim();
  state.seasonal = els.seasonal.checked;
  state.trvanlive = els.trvanlive.checked;
  state.jadro = els.jadro.checked;
  state.limit = els.limit.value;
  renderSeasonalNote();
}

function search() {
  const filtered = aggregatePlants();
  const limited = filtered.slice(0, Number(state.limit || 48));
  syncUrl();
  els.resultsTitle.textContent = pluralizePlants(filtered.length);
  renderResults(limited);
}

function resetFilters() {
  state.q = "";
  state.seasonal = true;
  state.trvanlive = false;
  state.jadro = false;
  state.limit = "48";
  syncControls();
  renderSeasonalNote();
  search();
}

async function init() {
  parseInitialState();
  bundle = await C.loadBundle();
  plantsById = new Map((bundle.plants || []).map((plant) => [plant.plant_id, plant]));

  renderSummary(bundle.summary);
  syncControls();
  renderSeasonalNote();

  const runSearch = debounce(() => {
    syncState();
    search();
  });

  [els.q, els.trvanlive, els.jadro, els.limit].forEach((element) => {
    const eventName = element.tagName === "INPUT" && element.type === "search" ? "input" : "change";
    element.addEventListener(eventName, runSearch);
  });

  els.seasonal.addEventListener("change", () => {
    syncState();
    search();
  });

  els.resetBtn.addEventListener("click", resetFilters);
  search();
}

init().catch((error) => {
  els.resultsTitle.textContent = "Chyba";
  els.results.innerHTML = `<div class="empty-state">Nepodařilo se načíst data: ${C.escapeHtml(error.message)}</div>`;
});
