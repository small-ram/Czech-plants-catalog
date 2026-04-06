const C = window.CatalogSite;

const DEFAULT_SORT = "recommend";

const state = {
  q: "",
  domain_groups: [],
  evidence_min: "",
  part_categories: [],
  subdomain_categories: [],
  processing_methods: [],
  knowledge_statuses: [],
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
  evidenceMin: document.getElementById("evidence_min"),
  domainGroups: document.getElementById("domain-groups"),
  knowledgeGroups: document.getElementById("knowledge-status-groups"),
  partGroups: document.getElementById("part-category-groups"),
  subdomainGroups: document.getElementById("subdomain-category-groups"),
  processingGroups: document.getElementById("processing-method-groups"),
  month: document.getElementById("month"),
  seasonal: document.getElementById("seasonal"),
  seasonalNote: document.getElementById("seasonal-note"),
  trvanlive: document.getElementById("trvanlive"),
  jadro: document.getElementById("jadro"),
  sort: document.getElementById("sort"),
  limit: document.getElementById("limit"),
  basicGroup: document.getElementById("filters-group-basic"),
  practicalGroup: document.getElementById("filters-group-practical"),
  advancedGroup: document.getElementById("filters-group-advanced"),
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

function parseMultiParam(params, key) {
  const values = params.getAll(key).filter(Boolean);
  if (values.length) return values;
  const single = params.get(key);
  return single ? [single] : [];
}

function uniqueValues(values) {
  return Array.from(new Set((values || []).filter(Boolean)));
}

function toggleArrayValue(values, target) {
  const current = uniqueValues(values);
  if (current.includes(target)) {
    return current.filter((value) => value !== target);
  }
  return [...current, target];
}

function parseInitialState() {
  const params = new URLSearchParams(window.location.search);
  state.q = params.get("q") || "";
  state.domain_groups = uniqueValues(parseMultiParam(params, "domena").flatMap((value) => C.domainGroupIdsFromValue(value)));
  state.evidence_min = params.get("evidence_min") || "";
  state.part_categories = uniqueValues(parseMultiParam(params, "part_category"));
  state.subdomain_categories = uniqueValues(parseMultiParam(params, "subdomain_category"));
  state.processing_methods = uniqueValues(parseMultiParam(params, "processing_method"));
  state.knowledge_statuses = uniqueValues(parseMultiParam(params, "knowledge_status"));
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
      <label class="field field-inline toolbar-field toolbar-field-narrow">
        <span>Limit</span>
        <select id="limit">
          <option value="24">24</option>
          <option value="60">60</option>
          <option value="120">120</option>
          <option value="200">200</option>
        </select>
      </label>
    `;
    toolbar.appendChild(controls);
    els.sort = document.getElementById("sort");
    els.limit = document.getElementById("limit");
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

function multiOptionButton(option, selectedValues, key) {
  const isActive = selectedValues.includes(option.value);
  return `
    <button
      class="multi-option${isActive ? " active" : ""}"
      type="button"
      data-filter-key="${C.escapeHtml(key)}"
      data-filter-value="${C.escapeHtml(option.value)}"
      aria-pressed="${isActive ? "true" : "false"}"
    >
      <span class="multi-option-label">${C.escapeHtml(option.label)}</span>
    </button>
  `;
}

function knowledgeOptions() {
  return uniqueValues((bundle?.uses || []).map((use) => use.status_znalosti))
    .sort((a, b) => C.knowledgeRank(b) - C.knowledgeRank(a))
    .map((value) => ({ value, label: C.knowledgeLabel(value) }));
}

function renderMultiGroups() {
  if (!bundle) return;

  if (els.domainGroups) {
    els.domainGroups.innerHTML = C.domainGroupOptions()
      .map((option) => multiOptionButton(option, state.domain_groups, "domain_groups"))
      .join("");
  }

  if (els.knowledgeGroups) {
    els.knowledgeGroups.innerHTML = knowledgeOptions()
      .map((option) => multiOptionButton(option, state.knowledge_statuses, "knowledge_statuses"))
      .join("");
  }

  if (els.partGroups) {
    els.partGroups.innerHTML = (bundle.options.part_categories || [])
      .map((value) =>
        multiOptionButton({ value, label: C.partCategoryLabel(value) }, state.part_categories, "part_categories")
      )
      .join("");
  }

  if (els.subdomainGroups) {
    els.subdomainGroups.innerHTML = (bundle.options.subdomain_categories || [])
      .map((value) =>
        multiOptionButton(
          { value, label: C.subdomainCategoryLabel(value) },
          state.subdomain_categories,
          "subdomain_categories"
        )
      )
      .join("");
  }

  if (els.processingGroups) {
    els.processingGroups.innerHTML = (bundle.options.processing_methods || [])
      .map((option) => multiOptionButton(option, state.processing_methods, "processing_methods"))
      .join("");
  }
}

function hasPracticalFiltersActive() {
  return Boolean(state.processing_methods.length || state.trvanlive || state.jadro);
}

function hasAdvancedFiltersActive() {
  return Boolean(
    state.knowledge_statuses.length || state.part_categories.length || state.subdomain_categories.length || state.evidence_min
  );
}

function syncFilterGroupState() {
  if (hasPracticalFiltersActive() && els.practicalGroup) {
    els.practicalGroup.open = true;
  }
  if (hasAdvancedFiltersActive() && els.advancedGroup) {
    els.advancedGroup.open = true;
  }
}

function syncControls() {
  els.q.value = state.q;
  els.evidenceMin.value = state.evidence_min;
  els.month.value = state.month;
  els.month.disabled = state.seasonal;
  els.seasonal.checked = state.seasonal;
  els.trvanlive.checked = state.trvanlive;
  els.jadro.checked = state.jadro;
  if (els.limit) els.limit.value = state.limit;
  if (els.sort) els.sort.value = state.sort;
  renderMultiGroups();
  syncFilterGroupState();
}

function appendMulti(params, key, values) {
  uniqueValues(values).forEach((value) => params.append(key, value));
}

function buildSearchParams() {
  const params = new URLSearchParams();
  if (state.q) params.set("q", state.q);
  appendMulti(params, "domena", state.domain_groups);
  if (state.evidence_min) params.set("evidence_min", state.evidence_min);
  appendMulti(params, "part_category", state.part_categories);
  appendMulti(params, "subdomain_category", state.subdomain_categories);
  appendMulti(params, "processing_method", state.processing_methods);
  appendMulti(params, "knowledge_status", state.knowledge_statuses);
  if (!state.seasonal && state.month) params.set("month", state.month);
  if (state.seasonal) params.set("seasonal", "1");
  if (state.trvanlive) params.set("trvanlive", "1");
  if (state.jadro) params.set("jadro", "1");
  if (state.sort !== DEFAULT_SORT) params.set("sort", state.sort);
  if (state.limit) params.set("limit", state.limit);
  return params;
}

function syncUrl() {
  const params = buildSearchParams();
  const nextUrl = params.toString() ? `?${params.toString()}` : window.location.pathname;
  window.history.replaceState(null, "", nextUrl);
}

function populateSelect(select, items, { valueKey = null, labelKey = null } = {}) {
  if (!select || !Array.isArray(items)) return;
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
    ["Doporučený výběr", summary.counts.core_items],
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
      els.seasonalNote.textContent = "Sezónní okno je vypnuté.";
    }
    return;
  }

  const windowConfig = C.seasonalWindowPayload();
  els.seasonalNote.textContent = `Výchozí okno: ${windowConfig.label}.`;
}

function renderBadges(result) {
  const badges = [
    `<span class="badge">${C.escapeHtml(C.domainLabel(result.domena))}</span>`,
    `<span class="badge">${C.escapeHtml(C.evidenceLabel(result.dukaznost_skore))}</span>`,
  ];

  if (C.normalizeBooleanish(result.je_v_jadru_bezne_1m_plus)) {
    badges.push('<span class="badge core">Doporučený výběr</span>');
  } else if (result.status_znalosti && result.status_znalosti !== "mainstream") {
    badges.push(`<span class="badge subtle">${C.escapeHtml(C.knowledgeLabel(result.status_znalosti))}</span>`);
  }

  return badges.slice(0, 3).join("");
}

function compactProcessingText(result) {
  const count = Number(result.processing_methods_count || 0);
  if (!count) return "";
  if (count === 1) {
    return String(result.processing_methods_text || "")
      .split("·")[0]
      .trim();
  }
  return `${count} způsoby zpracování`;
}

function teaserText(text, maxLength = 112) {
  const clean = String(text || "").replace(/\s+/g, " ").trim();
  if (!clean) return "";
  if (clean.length <= maxLength) return clean;
  return `${clean.slice(0, maxLength).trimEnd()}…`;
}

function renderResultCard(result) {
  const fragment = els.template.content.cloneNode(true);
  const article = fragment.querySelector(".result-card");
  const primaryLayer = fragment.querySelector(".card-primary-layer");
  const media = fragment.querySelector(".result-card-media");
  const image = fragment.querySelector(".result-card-image");
  const placeholder = fragment.querySelector(".result-card-placeholder");
  const meta = fragment.querySelector(".card-quick-meta");
  const effect = fragment.querySelector(".card-effect");
  const useLine = fragment.querySelector(".card-use-line");

  const useUrl = C.siteUrl(`use/${encodeURIComponent(result.use_id)}/`);
  const plantUrl = C.siteUrl(`plant/${encodeURIComponent(result.plant_id)}/`);

  primaryLayer.href = useUrl;
  primaryLayer.setAttribute("aria-label", `Detail použití: ${result.cesky_nazev_hlavni}`);

  article.dataset.useId = result.use_id;
  fragment.querySelector(".card-title").textContent = result.cesky_nazev_hlavni;
  fragment.querySelector(".card-subtitle").textContent = result.vedecky_nazev_hlavni;
  fragment.querySelector(".card-badges").innerHTML = renderBadges(result);
  useLine.innerHTML = `<strong>Použití:</strong> ${C.escapeHtml(result.poddomena_text || "neuvedeno")}`;

  const metaValues = [result.cast_rostliny_text, result.obdobi_ziskani_text, compactProcessingText(result)].filter(Boolean);
  if (metaValues.length) {
    meta.innerHTML = C.renderMeta(metaValues.slice(0, 3));
  } else {
    meta.remove();
  }

  const effectText = teaserText(result.hlavni_prinos_text || result.cilovy_efekt, 120);
  if (effectText) {
    effect.textContent = effectText;
  } else {
    effect.remove();
  }

  const useLink = fragment.querySelector(".detail-btn");
  const plantLink = fragment.querySelector(".plant-btn");
  useLink.href = useUrl;
  useLink.textContent = "Detail použití";
  plantLink.href = plantUrl;
  plantLink.textContent = "Rostlina";

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
    if (state.domain_groups.length && !state.domain_groups.some((group) => C.domainGroupMatches(use.domena, group))) {
      return false;
    }
    if (state.part_categories.length && !state.part_categories.includes(use.cast_rostliny_kategorie)) return false;
    if (state.subdomain_categories.length && !state.subdomain_categories.includes(use.poddomena_kategorie)) return false;
    if (state.processing_methods.length) {
      const processingIds = use.processing_method_ids || [];
      if (!state.processing_methods.some((value) => processingIds.includes(value))) return false;
    }
    if (state.knowledge_statuses.length && !state.knowledge_statuses.includes(use.status_znalosti)) return false;
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

function filterChip(label, value, key, filterValue = "") {
  return `
    <button
      class="filter-chip"
      type="button"
      data-filter-key="${C.escapeHtml(key)}"
      data-filter-value="${C.escapeHtml(filterValue)}"
    >
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
  state.domain_groups.forEach((value) => {
    chips.push(filterChip("Typ použití", C.domainGroupLabel(value), "domain_groups", value));
  });
  if (state.evidence_min) chips.push(filterChip("Min. důkaznost", C.evidenceLabel(state.evidence_min), "evidence_min"));
  state.part_categories.forEach((value) => {
    chips.push(filterChip("Sbíraná část", C.partCategoryLabel(value), "part_categories", value));
  });
  state.subdomain_categories.forEach((value) => {
    chips.push(filterChip("Způsob použití", C.subdomainCategoryLabel(value), "subdomain_categories", value));
  });
  state.processing_methods.forEach((value) => {
    chips.push(filterChip("Zpracování", processingMap.get(value) || value, "processing_methods", value));
  });
  state.knowledge_statuses.forEach((value) => {
    chips.push(filterChip("Jak rozšířené", C.knowledgeLabel(value), "knowledge_statuses", value));
  });
  if (state.seasonal) chips.push(filterChip("Sezóna", seasonalWindow.label, "seasonal"));
  if (!state.seasonal && state.month) chips.push(filterChip("Měsíc", C.monthLabel(state.month), "month"));
  if (state.trvanlive) chips.push(filterChip("Prakticky", "Jen trvanlivé", "trvanlive"));
  if (state.jadro) chips.push(filterChip("Prakticky", "Jen doporučený výběr", "jadro"));

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

function clearFilter(key, value) {
  switch (key) {
    case "q":
      state.q = "";
      break;
    case "domain_groups":
      state.domain_groups = state.domain_groups.filter((item) => item !== value);
      break;
    case "evidence_min":
      state.evidence_min = "";
      break;
    case "part_categories":
      state.part_categories = state.part_categories.filter((item) => item !== value);
      break;
    case "subdomain_categories":
      state.subdomain_categories = state.subdomain_categories.filter((item) => item !== value);
      break;
    case "processing_methods":
      state.processing_methods = state.processing_methods.filter((item) => item !== value);
      break;
    case "knowledge_statuses":
      state.knowledge_statuses = state.knowledge_statuses.filter((item) => item !== value);
      break;
    case "seasonal":
      state.seasonal = false;
      break;
    case "month":
      state.month = "";
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
  state.evidence_min = els.evidenceMin.value;
  state.seasonal = els.seasonal.checked;
  state.month = state.seasonal ? "" : els.month.value;
  state.trvanlive = els.trvanlive.checked;
  state.jadro = els.jadro.checked;
  state.limit = els.limit ? els.limit.value : state.limit;
  state.sort = els.sort ? els.sort.value : DEFAULT_SORT;
  renderSeasonalNote();
  syncFilterGroupState();
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
  state.domain_groups = [];
  state.evidence_min = "";
  state.part_categories = [];
  state.subdomain_categories = [];
  state.processing_methods = [];
  state.knowledge_statuses = [];
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

function bindMultiGroup(container, key) {
  if (!container) return;
  container.addEventListener("click", (event) => {
    const button = event.target.closest("[data-filter-key]");
    if (!button) return;
    const value = button.dataset.filterValue;
    state[key] = toggleArrayValue(state[key], value);
    syncControls();
    search();
  });
}

async function init() {
  parseInitialState();
  ensureEnhancements();
  bundle = await C.loadBundle();
  renderSummary(bundle.summary);

  populateSelect(
    els.evidenceMin,
    (bundle.options.evidence_scores || []).map((value) => ({ value, label: C.evidenceLabel(value) })),
    { valueKey: "value", labelKey: "label" }
  );
  populateSelect(els.month, bundle.options.months || [], { valueKey: "value", labelKey: "label" });

  syncControls();
  renderSeasonalNote();

  const runSearch = debounce(() => {
    syncState();
    search();
  });

  [els.q, els.evidenceMin, els.month, els.trvanlive, els.jadro, els.limit, els.sort]
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

  bindMultiGroup(els.domainGroups, "domain_groups");
  bindMultiGroup(els.knowledgeGroups, "knowledge_statuses");
  bindMultiGroup(els.partGroups, "part_categories");
  bindMultiGroup(els.subdomainGroups, "subdomain_categories");
  bindMultiGroup(els.processingGroups, "processing_methods");

  els.resetBtn.addEventListener("click", resetFilters);
  if (els.activeFilters) {
    els.activeFilters.addEventListener("click", (event) => {
      const chip = event.target.closest("[data-filter-key]");
      if (!chip) return;
      clearFilter(chip.dataset.filterKey, chip.dataset.filterValue);
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
