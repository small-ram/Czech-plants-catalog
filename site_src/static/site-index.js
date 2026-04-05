const C = window.CatalogSite;

const state = {
  q: "",
  domena: "",
  evidence_min: "",
  part_category: "",
  subdomain_category: "",
  processing_method: "",
  month: "",
  seasonal: true,
  trvanlive: false,
  jadro: false,
  limit: "60",
};

let bundle = null;

const els = {
  summaryStats: document.getElementById("summary-stats"),
  results: document.getElementById("results"),
  resultsTitle: document.getElementById("results-title"),
  template: document.getElementById("result-card-template"),
  resetBtn: document.getElementById("reset-btn"),
  q: document.getElementById("q"),
  domena: document.getElementById("domena"),
  evidenceMin: document.getElementById("evidence_min"),
  partCategory: document.getElementById("part_category"),
  subdomainCategory: document.getElementById("subdomain_category"),
  processingMethod: document.getElementById("processing_method"),
  month: document.getElementById("month"),
  seasonal: document.getElementById("seasonal"),
  seasonalNote: document.getElementById("seasonal-note"),
  trvanlive: document.getElementById("trvanlive"),
  jadro: document.getElementById("jadro"),
  limit: document.getElementById("limit"),
};

function debounce(fn, delay = 220) {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
}

function pluralizeResults(count) {
  if (count === 1) return "1 výsledek";
  if (count >= 2 && count <= 4) return `${count} výsledky`;
  return `${count} výsledků`;
}

function parseInitialState() {
  const params = new URLSearchParams(window.location.search);
  state.q = params.get("q") || "";
  state.domena = params.get("domena") || "";
  state.evidence_min = params.get("evidence_min") || "";
  state.part_category = params.get("part_category") || "";
  state.subdomain_category = params.get("subdomain_category") || "";
  state.processing_method = params.get("processing_method") || "";
  state.month = params.get("month") || "";
  const hasSeasonal = params.has("seasonal");
  const hasMonth = Boolean(state.month);
  state.seasonal = hasSeasonal ? params.get("seasonal") === "1" : !hasMonth;
  state.trvanlive = params.get("trvanlive") === "1";
  state.jadro = params.get("jadro") === "1";
  state.limit = params.get("limit") || state.limit;
}

function syncControls() {
  els.q.value = state.q;
  els.domena.value = state.domena;
  els.evidenceMin.value = state.evidence_min;
  els.partCategory.value = state.part_category;
  els.subdomainCategory.value = state.subdomain_category;
  els.processingMethod.value = state.processing_method;
  els.month.value = state.month;
  els.month.disabled = state.seasonal;
  els.seasonal.checked = state.seasonal;
  els.trvanlive.checked = state.trvanlive;
  els.jadro.checked = state.jadro;
  els.limit.value = state.limit;
}

function buildSearchParams() {
  const params = new URLSearchParams();
  Object.entries(state).forEach(([key, value]) => {
    if (key === "month" && state.seasonal) return;
    if (typeof value === "boolean") {
      if (value) params.set(key, "1");
      return;
    }
    if (value) params.set(key, value);
  });
  return params;
}

function syncUrl() {
  const params = buildSearchParams();
  const nextUrl = params.toString() ? `?${params.toString()}` : window.location.pathname;
  window.history.replaceState(null, "", nextUrl);
}

function populateSelect(select, items, { valueKey = null, labelKey = null } = {}) {
  if (!Array.isArray(items)) return;
  items.forEach((item) => {
    const option = document.createElement("option");
    if (typeof item === "object") {
      option.value = item[valueKey];
      option.textContent = item[labelKey];
    } else {
      option.value = item;
      option.textContent = item;
    }
    select.appendChild(option);
  });
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
    if (state.month) {
      const monthLabel = els.month.selectedOptions?.[0]?.textContent || state.month;
      els.seasonalNote.textContent = `Používáš ručně vybraný měsíc: ${monthLabel}.`;
    } else {
      els.seasonalNote.textContent = "Sezónní okno je vypnuté, takže se zobrazují položky bez časového omezení.";
    }
    return;
  }

  const windowConfig = C.seasonalWindowPayload();
  els.seasonalNote.textContent = `Výchozí okno pro ${windowConfig.today_label}: ${windowConfig.label}. ${windowConfig.reason}.`;
}

function renderBadges(result) {
  const badges = [];
  badges.push(`<span class="badge">${C.escapeHtml(result.domena)}</span>`);
  badges.push(`<span class="badge">Důkaznost ${C.escapeHtml(result.dukaznost_skore)}</span>`);
  if (C.normalizeBooleanish(result.je_trvanlive_1m_plus)) badges.push('<span class="badge">Trvanlivé</span>');
  if (C.normalizeBooleanish(result.je_v_jadru_bezne_1m_plus)) badges.push('<span class="badge core">Jádro</span>');
  return badges.join("");
}

function renderResultCard(result) {
  const fragment = els.template.content.cloneNode(true);
  const image = fragment.querySelector(".result-card-image");
  const placeholder = fragment.querySelector(".result-card-placeholder");

  fragment.querySelector(".card-id").textContent = result.raw_record_id;
  fragment.querySelector(".card-title").textContent = result.cesky_nazev_hlavni;
  fragment.querySelector(".card-subtitle").textContent = result.vedecky_nazev_hlavni;
  fragment.querySelector(".card-badges").innerHTML = renderBadges(result);
  fragment.querySelector(".meta-grid").innerHTML = C.renderMeta([
    result.cast_rostliny_text,
    result.poddomena_text,
    result.obdobi_ziskani_text,
    result.processing_methods_text,
    result.forma_uchovani_text,
    result.orientacni_trvanlivost_text,
  ]);
  fragment.querySelector(".card-effect").textContent = result.cilovy_efekt || "Bez popisu cílového efektu.";

  const useLink = fragment.querySelector(".detail-btn");
  const plantLink = fragment.querySelector(".plant-btn");
  useLink.href = C.siteUrl(`use/${encodeURIComponent(result.use_id)}/`);
  plantLink.href = C.siteUrl(`plant/${encodeURIComponent(result.plant_id)}/`);

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
    els.results.innerHTML = '<div class="empty-state">Tomu neodpovídá žádná položka. Zkus ubrat filtr nebo změnit hledaný výraz.</div>';
    return;
  }
  results.forEach((result) => {
    els.results.appendChild(renderResultCard(result));
  });
}

function filterUses() {
  const query = state.q.trim().toLowerCase();
  const seasonalWindow = C.seasonalWindowPayload();

  return (bundle.uses || []).filter((use) => {
    if (query && !(use.search_text || "").includes(query)) return false;
    if (state.domena && use.domena !== state.domena) return false;
    if (state.part_category && use.cast_rostliny_kategorie !== state.part_category) return false;
    if (state.subdomain_category && use.poddomena_kategorie !== state.subdomain_category) return false;
    if (state.processing_method && !(use.processing_method_ids || []).includes(state.processing_method)) return false;
    if (state.trvanlive && !C.normalizeBooleanish(use.je_trvanlive_1m_plus)) return false;
    if (state.jadro && !C.normalizeBooleanish(use.je_v_jadru_bezne_1m_plus)) return false;

    if (state.evidence_min) {
      const threshold = C.rankThreshold(state.evidence_min);
      if (threshold && Number(use.dukaznost_rank || 0) < threshold) return false;
    }

    if (state.seasonal) {
      return seasonalWindow.months.some((month) => C.monthMatches(use, month));
    }
    if (state.month) {
      return C.monthMatches(use, Number(state.month));
    }
    return true;
  });
}

function syncState() {
  state.q = els.q.value.trim();
  state.domena = els.domena.value;
  state.evidence_min = els.evidenceMin.value;
  state.part_category = els.partCategory.value;
  state.subdomain_category = els.subdomainCategory.value;
  state.processing_method = els.processingMethod.value;
  state.seasonal = els.seasonal.checked;
  state.month = state.seasonal ? "" : els.month.value;
  state.trvanlive = els.trvanlive.checked;
  state.jadro = els.jadro.checked;
  state.limit = els.limit.value;
  renderSeasonalNote();
}

function search() {
  const filtered = filterUses();
  const limited = filtered.slice(0, Number(state.limit || 60));
  syncUrl();
  els.resultsTitle.textContent = pluralizeResults(filtered.length);
  renderResults(limited);
}

function resetFilters() {
  state.q = "";
  state.domena = "";
  state.evidence_min = "";
  state.part_category = "";
  state.subdomain_category = "";
  state.processing_method = "";
  state.month = "";
  state.seasonal = true;
  state.trvanlive = false;
  state.jadro = false;
  state.limit = "60";
  syncControls();
  renderSeasonalNote();
  search();
}

async function init() {
  parseInitialState();
  bundle = await C.loadBundle();
  renderSummary(bundle.summary);

  populateSelect(els.domena, bundle.options.domains || []);
  populateSelect(els.evidenceMin, bundle.options.evidence_scores || []);
  populateSelect(
    els.partCategory,
    (bundle.options.part_categories || []).map((value) => ({ value, label: C.labelize(value) })),
    { valueKey: "value", labelKey: "label" }
  );
  populateSelect(
    els.subdomainCategory,
    (bundle.options.subdomain_categories || []).map((value) => ({ value, label: C.labelize(value) })),
    { valueKey: "value", labelKey: "label" }
  );
  populateSelect(els.processingMethod, bundle.options.processing_methods || [], {
    valueKey: "value",
    labelKey: "label",
  });
  populateSelect(els.month, bundle.options.months || [], { valueKey: "value", labelKey: "label" });

  syncControls();
  renderSeasonalNote();

  const runSearch = debounce(() => {
    syncState();
    search();
  });

  [
    els.q,
    els.domena,
    els.evidenceMin,
    els.partCategory,
    els.subdomainCategory,
    els.processingMethod,
    els.month,
    els.trvanlive,
    els.jadro,
    els.limit,
  ].forEach((element) => {
    const eventName = element.tagName === "INPUT" && element.type === "search" ? "input" : "change";
    element.addEventListener(eventName, runSearch);
  });

  els.seasonal.addEventListener("change", () => {
    state.seasonal = els.seasonal.checked;
    if (state.seasonal) {
      state.month = "";
      els.month.value = "";
    }
    syncControls();
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
