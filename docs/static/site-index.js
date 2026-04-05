const C = window.CatalogSite;

const DEFAULT_SORT = "recommend";

const state = {
  q: "",
  domena: "",
  evidence_min: "",
  part_category: "",
  subdomain_category: "",
  processing_method: "",
  knowledge_status: "",
  month: "",
  seasonal: true,
  trvanlive: false,
  jadro: false,
  sort: DEFAULT_SORT,
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
  state.knowledge_status = params.get("knowledge_status") || "";
  state.month = params.get("month") || "";
  state.sort = params.get("sort") || DEFAULT_SORT;
  const hasSeasonal = params.has("seasonal");
  const hasMonth = Boolean(state.month);
  state.seasonal = hasSeasonal ? params.get("seasonal") === "1" : !hasMonth;
  state.trvanlive = params.get("trvanlive") === "1";
  state.jadro = params.get("jadro") === "1";
  state.limit = params.get("limit") || state.limit;
}

function ensureEnhancements() {
  const searchField = els.q?.closest(".field");
  if (searchField && !document.getElementById("filters-help")) {
    const note = document.createElement("p");
    note.id = "filters-help";
    note.className = "helper-note";
    note.textContent =
      "Tip: zkus hledat podle výsledku i procesu, třeba „sirup“, „pupeny“, „žaludová mouka“ nebo přepni filtr Jak známé na méně známé či téměř zapomenuté.";
    searchField.after(note);
  }

  if (els.seasonalNote && !document.getElementById("knowledge_status")) {
    const field = document.createElement("label");
    field.className = "field";
    field.innerHTML = `
      <span>Jak známé</span>
      <select id="knowledge_status">
        <option value="">Vše</option>
      </select>
    `;
    els.seasonalNote.before(field);
    els.knowledgeStatus = document.getElementById("knowledge_status");
  }

  const toolbar = document.querySelector(".results-toolbar");
  if (toolbar && !document.getElementById("sort")) {
    const controls = document.createElement("div");
    controls.className = "toolbar-controls";
    controls.innerHTML = `
      <label class="field field-inline toolbar-field">
        <span>Řazení</span>
        <select id="sort">
          <option value="recommend">Doporučené</option>
          <option value="alphabetical">Abecedně</option>
          <option value="evidence">Nejvyšší důkaznost</option>
          <option value="hidden_gems">Méně známé nahoře</option>
        </select>
      </label>
    `;
    toolbar.appendChild(controls);
    els.sort = document.getElementById("sort");
  }

  if (toolbar && !document.getElementById("results-context-block")) {
    const context = document.createElement("section");
    context.id = "results-context-block";
    context.className = "results-context-block";
    context.innerHTML = `
      <p id="results-context" class="results-context-text"></p>
      <div id="active-filters" class="active-filters"></div>
    `;
    toolbar.after(context);
    els.resultsContext = document.getElementById("results-context");
    els.activeFilters = document.getElementById("active-filters");
  }
}

function syncControls() {
  els.q.value = state.q;
  els.domena.value = state.domena;
  els.evidenceMin.value = state.evidence_min;
  if (els.knowledgeStatus) els.knowledgeStatus.value = state.knowledge_status;
  els.partCategory.value = state.part_category;
  els.subdomainCategory.value = state.subdomain_category;
  els.processingMethod.value = state.processing_method;
  els.month.value = state.month;
  els.month.disabled = state.seasonal;
  els.seasonal.checked = state.seasonal;
  els.trvanlive.checked = state.trvanlive;
  els.jadro.checked = state.jadro;
  els.limit.value = state.limit;
  if (els.sort) els.sort.value = state.sort;
}

function buildSearchParams() {
  const params = new URLSearchParams();
  Object.entries(state).forEach(([key, value]) => {
    if (key === "month" && state.seasonal) return;
    if (key === "sort" && value === DEFAULT_SORT) return;
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
  badges.push(`<span class="badge">${C.escapeHtml(C.evidenceLabel(result.dukaznost_skore))}</span>`);
  if (result.status_znalosti) badges.push(`<span class="badge subtle">${C.escapeHtml(C.knowledgeLabel(result.status_znalosti))}</span>`);
  if (C.normalizeBooleanish(result.je_trvanlive_1m_plus)) badges.push('<span class="badge">Trvanlivé</span>');
  if (C.normalizeBooleanish(result.je_v_jadru_bezne_1m_plus)) badges.push('<span class="badge core">Praktické jádro</span>');
  return badges.join("");
}

function renderResultCard(result) {
  const fragment = els.template.content.cloneNode(true);
  const media = fragment.querySelector(".result-card-media");
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
  useLink.textContent = "Detail použití";
  plantLink.href = C.siteUrl(`plant/${encodeURIComponent(result.plant_id)}/`);
  plantLink.textContent = "Profil rostliny";

  if (result.primary_photo) {
    image.src = C.assetUrl(result.primary_photo);
    image.alt = result.primary_photo_alt || result.cesky_nazev_hlavni;
    image.title = [result.primary_photo_credit, result.primary_photo_source_name].filter(Boolean).join(" · ");
    image.hidden = false;
    media.classList.add("has-image");
    placeholder.remove();
  }

  return fragment;
}

function renderResults(results) {
  els.results.innerHTML = "";
  if (!results.length) {
    const hint = state.q
      ? `Zkus obecnější hledání místo „${C.escapeHtml(state.q)}“ nebo uber některý filtr.`
      : "Zkus ubrat některý filtr nebo vypnout sezónní okno.";
    els.results.innerHTML = `<div class="empty-state">Tomu neodpovídá žádná položka. ${hint}</div>`;
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
    if (state.knowledge_status && use.status_znalosti !== state.knowledge_status) return false;
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

function sortUses(results) {
  const items = results.slice();
  switch (state.sort) {
    case "alphabetical":
      return items.sort((a, b) => {
        const byPlant = String(a.cesky_nazev_hlavni || "").localeCompare(String(b.cesky_nazev_hlavni || ""), "cs");
        if (byPlant !== 0) return byPlant;
        return String(a.poddomena_text || "").localeCompare(String(b.poddomena_text || ""), "cs");
      });
    case "evidence":
      return items.sort((a, b) => {
        if (Number(b.dukaznost_rank || 0) !== Number(a.dukaznost_rank || 0)) {
          return Number(b.dukaznost_rank || 0) - Number(a.dukaznost_rank || 0);
        }
        if (Number(b.je_v_jadru_bezne_1m_plus || 0) !== Number(a.je_v_jadru_bezne_1m_plus || 0)) {
          return Number(b.je_v_jadru_bezne_1m_plus || 0) - Number(a.je_v_jadru_bezne_1m_plus || 0);
        }
        return String(a.cesky_nazev_hlavni || "").localeCompare(String(b.cesky_nazev_hlavni || ""), "cs");
      });
    case "hidden_gems":
      return items.sort((a, b) => {
        if (C.knowledgeRank(b.status_znalosti) !== C.knowledgeRank(a.status_znalosti)) {
          return C.knowledgeRank(b.status_znalosti) - C.knowledgeRank(a.status_znalosti);
        }
        if (Number(b.dukaznost_rank || 0) !== Number(a.dukaznost_rank || 0)) {
          return Number(b.dukaznost_rank || 0) - Number(a.dukaznost_rank || 0);
        }
        return String(a.cesky_nazev_hlavni || "").localeCompare(String(b.cesky_nazev_hlavni || ""), "cs");
      });
    default:
      return items;
  }
}

function filterChip(label, value, key) {
  return `
    <button class="filter-chip" type="button" data-filter-key="${C.escapeHtml(key)}">
      <span class="filter-chip-label">${C.escapeHtml(label)}:</span>
      <span>${C.escapeHtml(value)}</span>
      <span class="filter-chip-remove" aria-hidden="true">×</span>
    </button>
  `;
}

function renderActiveFilters(totalCount, displayedCount) {
  const chips = [];
  const seasonalWindow = C.seasonalWindowPayload();
  const processingMap = new Map((bundle.options.processing_methods || []).map((item) => [item.value, item.label]));

  if (state.q) chips.push(filterChip("Hledání", state.q, "q"));
  if (state.seasonal) chips.push(filterChip("Sezóna", seasonalWindow.label, "seasonal"));
  if (!state.seasonal && state.month) chips.push(filterChip("Měsíc", C.monthLabel(state.month), "month"));
  if (state.domena) chips.push(filterChip("Doména", state.domena, "domena"));
  if (state.evidence_min) chips.push(filterChip("Min. důkaznost", C.evidenceLabel(state.evidence_min), "evidence_min"));
  if (state.knowledge_status) chips.push(filterChip("Jak známé", C.knowledgeLabel(state.knowledge_status), "knowledge_status"));
  if (state.part_category) chips.push(filterChip("Část", C.labelize(state.part_category), "part_category"));
  if (state.subdomain_category) chips.push(filterChip("Použití", C.labelize(state.subdomain_category), "subdomain_category"));
  if (state.processing_method) {
    chips.push(filterChip("Zpracování", processingMap.get(state.processing_method) || state.processing_method, "processing_method"));
  }
  if (state.trvanlive) chips.push(filterChip("Prakticky", "Jen trvanlivé", "trvanlive"));
  if (state.jadro) chips.push(filterChip("Prakticky", "Jen jádro", "jadro"));

  if (els.resultsContext) {
    els.resultsContext.textContent =
      displayedCount < totalCount
        ? `Zobrazeno ${displayedCount} z ${totalCount} výsledků kvůli limitu.`
        : `${totalCount} výsledků podle aktuálních filtrů.`;
  }

  if (els.activeFilters) {
    els.activeFilters.innerHTML = chips.length
      ? chips.join("")
      : '<div class="results-context-empty">Výchozí režim: doporučené řazení a bez dalších omezení kromě případného sezónního okna.</div>';
  }
}

function clearFilter(key) {
  switch (key) {
    case "q":
      state.q = "";
      break;
    case "seasonal":
      state.seasonal = false;
      break;
    case "month":
      state.month = "";
      break;
    case "domena":
      state.domena = "";
      break;
    case "evidence_min":
      state.evidence_min = "";
      break;
    case "knowledge_status":
      state.knowledge_status = "";
      break;
    case "part_category":
      state.part_category = "";
      break;
    case "subdomain_category":
      state.subdomain_category = "";
      break;
    case "processing_method":
      state.processing_method = "";
      break;
    case "trvanlive":
      state.trvanlive = false;
      break;
    case "jadro":
      state.jadro = false;
      break;
    default:
      break;
  }
}

function syncState() {
  state.q = els.q.value.trim();
  state.domena = els.domena.value;
  state.evidence_min = els.evidenceMin.value;
  state.knowledge_status = els.knowledgeStatus ? els.knowledgeStatus.value : "";
  state.part_category = els.partCategory.value;
  state.subdomain_category = els.subdomainCategory.value;
  state.processing_method = els.processingMethod.value;
  state.seasonal = els.seasonal.checked;
  state.month = state.seasonal ? "" : els.month.value;
  state.trvanlive = els.trvanlive.checked;
  state.jadro = els.jadro.checked;
  state.limit = els.limit.value;
  state.sort = els.sort ? els.sort.value : DEFAULT_SORT;
  renderSeasonalNote();
}

function search() {
  const filtered = sortUses(filterUses());
  const limited = filtered.slice(0, Number(state.limit || 60));
  syncUrl();
  els.resultsTitle.textContent = pluralizeResults(filtered.length);
  renderActiveFilters(filtered.length, limited.length);
  renderResults(limited);
}

function resetFilters() {
  state.q = "";
  state.domena = "";
  state.evidence_min = "";
  state.knowledge_status = "";
  state.part_category = "";
  state.subdomain_category = "";
  state.processing_method = "";
  state.month = "";
  state.seasonal = true;
  state.trvanlive = false;
  state.jadro = false;
  state.sort = DEFAULT_SORT;
  state.limit = "60";
  syncControls();
  renderSeasonalNote();
  search();
}

async function init() {
  parseInitialState();
  ensureEnhancements();
  bundle = await C.loadBundle();
  renderSummary(bundle.summary);

  populateSelect(els.domena, bundle.options.domains || []);
  populateSelect(
    els.evidenceMin,
    (bundle.options.evidence_scores || []).map((value) => ({ value, label: C.evidenceLabel(value) })),
    { valueKey: "value", labelKey: "label" }
  );
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
  populateSelect(
    els.knowledgeStatus,
    Array.from(new Set((bundle.uses || []).map((use) => use.status_znalosti).filter(Boolean)))
      .sort((a, b) => C.knowledgeRank(b) - C.knowledgeRank(a))
      .map((value) => ({ value, label: C.knowledgeLabel(value) })),
    { valueKey: "value", labelKey: "label" }
  );
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
    els.knowledgeStatus,
    els.partCategory,
    els.subdomainCategory,
    els.processingMethod,
    els.month,
    els.trvanlive,
    els.jadro,
    els.limit,
    els.sort,
  ]
    .filter(Boolean)
    .forEach((element) => {
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
  if (els.activeFilters) {
    els.activeFilters.addEventListener("click", (event) => {
      const chip = event.target.closest("[data-filter-key]");
      if (!chip) return;
      clearFilter(chip.dataset.filterKey);
      syncControls();
      search();
    });
  }

  search();
}

init().catch((error) => {
  els.resultsTitle.textContent = "Chyba";
  els.results.innerHTML = `<div class="empty-state">Nepodařilo se načíst data: ${C.escapeHtml(error.message)}</div>`;
});
