const C = window.CatalogSite;

const DEFAULT_SORT = "recommend";

const state = {
  q: "",
  knowledge_statuses: [],
  seasonal: true,
  trvanlive: false,
  jadro: false,
  sort: DEFAULT_SORT,
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
  knowledgeGroups: document.getElementById("plants-knowledge-status-groups"),
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

function uniqueValues(values) {
  return Array.from(new Set((values || []).filter(Boolean)));
}

function parseInitialState() {
  const params = new URLSearchParams(window.location.search);
  state.q = params.get("q") || "";
  state.knowledge_statuses = uniqueValues(params.getAll("knowledge_status").filter(Boolean));
  state.seasonal = params.has("seasonal") ? params.get("seasonal") === "1" : true;
  state.trvanlive = params.get("trvanlive") === "1";
  state.jadro = params.get("jadro") === "1";
  state.sort = params.get("sort") || DEFAULT_SORT;
  state.limit = params.get("limit") || state.limit;
}

function ensureEnhancements() {
  const searchField = els.q?.closest(".field");
  if (searchField && !document.getElementById("plants-help")) {
    const note = document.createElement("p");
    note.id = "plants-help";
    note.className = "helper-note";
    note.textContent =
      "Tip: použij hledání pro rod i české jméno a kombinuj ho s více stavy rozšířenosti, když chceš procházet méně známé nebo téměř zapomenuté druhy.";
    searchField.after(note);
  }

  const toolbar = document.querySelector(".results-toolbar");
  if (toolbar && !document.getElementById("plants-sort")) {
    const controls = document.createElement("div");
    controls.className = "toolbar-controls";
    controls.innerHTML = `
      <label class="field field-inline toolbar-field">
        <span>Řazení</span>
        <select id="plants-sort">
          <option value="recommend">Doporučené</option>
          <option value="most_uses">Nejvíc použití</option>
          <option value="alphabetical">Abecedně</option>
          <option value="evidence">Nejvyšší důkaznost</option>
          <option value="hidden_gems">Méně známé nahoře</option>
        </select>
      </label>
    `;
    toolbar.appendChild(controls);
    els.sort = document.getElementById("plants-sort");
  }

  if (toolbar && !document.getElementById("plants-context-block")) {
    const context = document.createElement("section");
    context.id = "plants-context-block";
    context.className = "results-context-block";
    context.innerHTML = `
      <p id="plants-context" class="results-context-text"></p>
      <div id="plants-active-filters" class="active-filters"></div>
    `;
    toolbar.after(context);
    els.resultsContext = document.getElementById("plants-context");
    els.activeFilters = document.getElementById("plants-active-filters");
  }
}

function toggleArrayValue(values, target) {
  const current = uniqueValues(values);
  if (current.includes(target)) {
    return current.filter((value) => value !== target);
  }
  return [...current, target];
}

function knowledgeOptions() {
  return uniqueValues((bundle?.uses || []).map((use) => use.status_znalosti))
    .sort((a, b) => C.knowledgeRank(b) - C.knowledgeRank(a))
    .map((value) => ({ value, label: C.knowledgeLabel(value) }));
}

function multiOptionButton(option, selectedValues) {
  const isActive = selectedValues.includes(option.value);
  return `
    <button
      class="multi-option${isActive ? " active" : ""}"
      type="button"
      data-filter-key="knowledge_statuses"
      data-filter-value="${C.escapeHtml(option.value)}"
      aria-pressed="${isActive ? "true" : "false"}"
    >
      <span class="multi-option-label">${C.escapeHtml(option.label)}</span>
    </button>
  `;
}

function renderKnowledgeGroup() {
  if (!bundle || !els.knowledgeGroups) return;
  els.knowledgeGroups.innerHTML = knowledgeOptions()
    .map((option) => multiOptionButton(option, state.knowledge_statuses))
    .join("");
}

function syncControls() {
  els.q.value = state.q;
  els.seasonal.checked = state.seasonal;
  els.trvanlive.checked = state.trvanlive;
  els.jadro.checked = state.jadro;
  els.limit.value = state.limit;
  if (els.sort) els.sort.value = state.sort;
  renderKnowledgeGroup();
}

function buildSearchParams() {
  const params = new URLSearchParams();
  if (state.q) params.set("q", state.q);
  state.knowledge_statuses.forEach((value) => params.append("knowledge_status", value));
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
    els.seasonalNote.textContent = "Sezónní filtr je vypnutý, takže galerie ukazuje všechny rostliny podle ostatních filtrů.";
    return;
  }

  const windowConfig = C.seasonalWindowPayload();
  els.seasonalNote.textContent = `Výchozí okno pro ${windowConfig.today_label}: ${windowConfig.label}. ${windowConfig.reason}.`;
}

function renderBadges(result) {
  const badges = [];
  if (result.durable_use_count) badges.push(`<span class="badge">Trvanlivé ${result.durable_use_count}</span>`);
  if (result.core_use_count) badges.push(`<span class="badge core">Doporučený výběr ${result.core_use_count}</span>`);
  if (result.processing_use_count) badges.push(`<span class="badge">Zpracování ${result.processing_use_count}</span>`);
  if (result.photos?.length) badges.push(`<span class="badge subtle">Fotky ${result.photos.length}</span>`);
  if (result.hidden_gem_rank > 1) {
    badges.push(
      `<span class="badge subtle">${C.escapeHtml(
        result.hidden_gem_rank >= 4 ? "Téměř zapomenuté stopy" : "Méně známé stopy"
      )}</span>`
    );
  }
  return badges.join("");
}

function renderPlantCard(result) {
  const fragment = els.template.content.cloneNode(true);
  const media = fragment.querySelector(".plant-card-media");
  const image = fragment.querySelector(".plant-card-image");
  const placeholder = fragment.querySelector(".plant-card-placeholder");

  fragment.querySelector(".card-title").textContent = result.cesky_nazev_hlavni;
  fragment.querySelector(".card-subtitle").textContent = result.vedecky_nazev_hlavni;
  fragment.querySelector(".card-badges").innerHTML = renderBadges(result);
  fragment.querySelector(".meta-grid").innerHTML = C.renderMeta([
    result.status_cetnost_reprezentativni ? C.knowledgeLabel(result.status_cetnost_reprezentativni) : "",
    result.top_evidence_rank ? `Top opora ${result.top_evidence_rank}` : "",
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
  profileLink.textContent = "Otevřít profil";
  exportLink.href = C.siteUrl(`export/plant/${encodeURIComponent(result.plant_id)}.md`);
  exportLink.textContent = "Stáhnout MD";

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
      ? `Zkus obecnější hledání místo „${C.escapeHtml(state.q)}“ nebo vypni některý filtr.`
      : "Zkus vypnout sezónní režim nebo ubrat některé omezení.";
    els.results.innerHTML = `<div class="empty-state">Tomu neodpovídá žádná rostlina. ${hint}</div>`;
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
    if (state.knowledge_statuses.length && !state.knowledge_statuses.includes(use.status_znalosti)) return false;

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
        hidden_gem_rank: 0,
      });
    }

    const aggregate = aggregates.get(use.plant_id);
    aggregate.use_count += 1;
    if (C.normalizeBooleanish(use.je_trvanlive_1m_plus)) aggregate.durable_use_count += 1;
    if (C.normalizeBooleanish(use.je_v_jadru_bezne_1m_plus)) aggregate.core_use_count += 1;
    if (Number(use.processing_methods_count || 0) > 0 || use.forma_uchovani_text) aggregate.processing_use_count += 1;
    aggregate.top_evidence_rank = Math.max(aggregate.top_evidence_rank, Number(use.dukaznost_rank || 0));
    aggregate.hidden_gem_rank = Math.max(aggregate.hidden_gem_rank, C.knowledgeRank(use.status_znalosti));
  });

  return Array.from(aggregates.values());
}

function sortPlants(results) {
  const items = results.slice();
  switch (state.sort) {
    case "most_uses":
      return items.sort((a, b) => b.use_count - a.use_count || a.cesky_nazev_hlavni.localeCompare(b.cesky_nazev_hlavni, "cs"));
    case "alphabetical":
      return items.sort((a, b) => a.cesky_nazev_hlavni.localeCompare(b.cesky_nazev_hlavni, "cs"));
    case "evidence":
      return items.sort((a, b) => b.top_evidence_rank - a.top_evidence_rank || b.use_count - a.use_count);
    case "hidden_gems":
      return items.sort((a, b) => {
        if (b.hidden_gem_rank !== a.hidden_gem_rank) return b.hidden_gem_rank - a.hidden_gem_rank;
        if (b.top_evidence_rank !== a.top_evidence_rank) return b.top_evidence_rank - a.top_evidence_rank;
        return a.cesky_nazev_hlavni.localeCompare(b.cesky_nazev_hlavni, "cs");
      });
    default:
      return items.sort((a, b) => {
        if (b.core_use_count !== a.core_use_count) return b.core_use_count - a.core_use_count;
        if (b.durable_use_count !== a.durable_use_count) return b.durable_use_count - a.durable_use_count;
        if (b.processing_use_count !== a.processing_use_count) return b.processing_use_count - a.processing_use_count;
        if (b.top_evidence_rank !== a.top_evidence_rank) return b.top_evidence_rank - a.top_evidence_rank;
        return a.cesky_nazev_hlavni.localeCompare(b.cesky_nazev_hlavni, "cs");
      });
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

  if (state.q) chips.push(filterChip("Hledání", state.q, "q"));
  state.knowledge_statuses.forEach((value) => {
    chips.push(filterChip("Jak rozšířené", C.knowledgeLabel(value), "knowledge_statuses", value));
  });
  if (state.seasonal) chips.push(filterChip("Sezóna", seasonalWindow.label, "seasonal"));
  if (state.trvanlive) chips.push(filterChip("Prakticky", "Jen s trvanlivým použitím", "trvanlive"));
  if (state.jadro) chips.push(filterChip("Prakticky", "Jen s položkou v doporučeném výběru", "jadro"));

  if (els.resultsContext) {
    els.resultsContext.textContent =
      displayedCount < totalCount
        ? `Zobrazeno ${displayedCount} z ${totalCount} rostlin kvůli limitu.`
        : `${totalCount} rostlin podle aktuálních filtrů.`;
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
    case "seasonal":
      state.seasonal = false;
      break;
    case "knowledge_statuses":
      state.knowledge_statuses = state.knowledge_statuses.filter((item) => item !== value);
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
  state.seasonal = els.seasonal.checked;
  state.trvanlive = els.trvanlive.checked;
  state.jadro = els.jadro.checked;
  state.sort = els.sort ? els.sort.value : DEFAULT_SORT;
  state.limit = els.limit.value;
  renderSeasonalNote();
}

function search() {
  const filtered = sortPlants(aggregatePlants());
  const limited = filtered.slice(0, Number(state.limit || 48));
  syncUrl();
  els.resultsTitle.textContent = pluralizePlants(filtered.length);
  renderActiveFilters(filtered.length, limited.length);
  renderResults(limited);
}

function resetFilters() {
  state.q = "";
  state.knowledge_statuses = [];
  state.seasonal = true;
  state.trvanlive = false;
  state.jadro = false;
  state.sort = DEFAULT_SORT;
  state.limit = "48";
  syncControls();
  renderSeasonalNote();
  search();
}

function bindKnowledgeGroup() {
  if (!els.knowledgeGroups) return;
  els.knowledgeGroups.addEventListener("click", (event) => {
    const button = event.target.closest("[data-filter-key]");
    if (!button) return;
    const value = button.dataset.filterValue;
    state.knowledge_statuses = toggleArrayValue(state.knowledge_statuses, value);
    syncControls();
    search();
  });
}

async function init() {
  parseInitialState();
  ensureEnhancements();
  bundle = await C.loadBundle();
  plantsById = new Map((bundle.plants || []).map((plant) => [plant.plant_id, plant]));

  renderSummary(bundle.summary);
  syncControls();
  renderSeasonalNote();

  const runSearch = debounce(() => {
    syncState();
    search();
  });

  [els.q, els.trvanlive, els.jadro, els.limit, els.sort]
    .filter(Boolean)
    .forEach((element) => {
      const eventName = element.tagName === "INPUT" && element.type === "search" ? "input" : "change";
      element.addEventListener(eventName, runSearch);
    });

  els.seasonal.addEventListener("change", () => {
    syncState();
    search();
  });

  bindKnowledgeGroup();

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
