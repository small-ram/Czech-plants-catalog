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

let seasonalDefault = null;
let apiBase = "";
let initialSummary = null;
let initialOptions = null;

const API_BASE_CANDIDATES = ["", "http://127.0.0.1:8766"];

const els = {
  summaryStats: document.getElementById("summary-stats"),
  results: document.getElementById("results"),
  resultsTitle: document.getElementById("results-title"),
  dialog: document.getElementById("detail-dialog"),
  detailContent: document.getElementById("detail-content"),
  detailClose: document.getElementById("detail-close"),
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

function labelize(value) {
  return String(value || "")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
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
    if (key === "month" && state.seasonal) {
      return;
    }
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
  const nextUrl = params.toString() ? `/?${params.toString()}` : "/";
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

function populateSelect(select, items, { valueKey = null, labelKey = null } = {}) {
  if (!Array.isArray(items)) {
    return;
  }
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
    card.innerHTML = `<strong>${value}</strong><span>${label}</span>`;
    els.summaryStats.appendChild(card);
  });
}

function renderSeasonalNote(windowConfig = seasonalDefault) {
  if (!els.seasonalNote) return;

  if (!state.seasonal) {
    if (state.month) {
      const monthLabel = els.month.selectedOptions?.[0]?.textContent || state.month;
      els.seasonalNote.textContent = `Používáš ručně vybraný měsíc: ${monthLabel}.`;
    } else {
      els.seasonalNote.textContent = "Sezónní okno je vypnuté, takže se zobrazují položky bez časového omezení.";
    }
    return;
  }

  if (!windowConfig) {
    els.seasonalNote.textContent = "Sezónní okno je aktivní.";
    return;
  }

  els.seasonalNote.textContent = `Výchozí okno pro ${windowConfig.today_label}: ${windowConfig.label}. ${windowConfig.reason}.`;
}

function renderBadges(result) {
  const badges = [];
  badges.push(`<span class="badge">${result.domena}</span>`);
  badges.push(`<span class="badge">Důkaznost ${result.dukaznost_skore}</span>`);
  if (result.je_trvanlive_1m_plus) badges.push('<span class="badge">Trvanlivé</span>');
  if (result.je_v_jadru_bezne_1m_plus) badges.push('<span class="badge core">Jádro</span>');
  return badges.join("");
}

function renderMeta(values) {
  return values
    .filter(Boolean)
    .map((value) => `<span class="meta-pill">${value}</span>`)
    .join("");
}

function mediaKindClass(kind) {
  switch (kind) {
    case "photo":
      return "photo-kind-photo";
    case "illustration":
      return "photo-kind-illustration";
    case "auto_cover":
      return "photo-kind-auto-cover";
    default:
      return "";
  }
}

function mediaKindLabel(photo) {
  if (photo.media_kind_label) return photo.media_kind_label;
  if (photo.media_kind === "photo") return "Foto";
  if (photo.media_kind === "illustration") return "Ilustrace";
  if (photo.media_kind === "auto_cover") return "Auto-cover";
  return "";
}

function renderPhotoCaption(photo) {
  const parts = [];
  const kindLabel = mediaKindLabel(photo);
  if (kindLabel) {
    parts.push(`<span class="photo-kind-pill ${mediaKindClass(photo.media_kind)}">${kindLabel}</span>`);
  }
  if (photo.caption) parts.push(`<span>${photo.caption}</span>`);
  if (photo.credit) parts.push(`<span>${photo.credit}</span>`);
  if (photo.license) parts.push(`<span>${photo.license}</span>`);
  if (photo.source_url) {
    parts.push(
      `<a class="photo-source-link" href="${photo.source_url}" target="_blank" rel="noreferrer">${photo.source_name || "Zdroj"}</a>`
    );
  }
  return parts.length ? `<figcaption class="photo-caption">${parts.join(" · ")}</figcaption>` : "";
}

function renderPhotoBlock(photos, fallbackText) {
  if (!photos || !photos.length) {
    return `<div class="photo-placeholder"><div>${fallbackText}</div></div>`;
  }

  return `
    <div class="photo-grid">
      ${photos
        .map(
          (photo) => `
            <figure class="photo-card">
              <img src="${photo.src}" alt="${photo.alt || ""}" loading="lazy" />
              ${renderPhotoCaption(photo)}
            </figure>
          `
        )
        .join("")}
    </div>
  `;
}

function renderProcessingMethods(methods) {
  if (!methods?.length) {
    return "<p>Neuvedeno.</p>";
  }
  return `<ul>${methods.map((method) => `<li>${method.label}</li>`).join("")}</ul>`;
}

function normalizeText(value) {
  return String(value || "")
    .trim()
    .replace(/\s+/g, " ")
    .toLowerCase();
}

function distinctText(primary, secondary) {
  return normalizeText(primary) && normalizeText(primary) !== normalizeText(secondary);
}

function teaserText(text, maxLength = 132) {
  const clean = String(text || "").replace(/\s+/g, " ").trim();
  if (!clean) return "";
  if (clean.length <= maxLength) return clean;
  return `${clean.slice(0, maxLength).trimEnd()}…`;
}

function renderFunctionalSection(detail, { title = "Látky a přínosy", plantLevel = false } = {}) {
  const items = [];
  if (detail.hlavni_prinos_text) {
    items.push(
      `<p><strong>${plantLevel ? "Proč je rostlina zajímavá:" : "Proč to může dávat smysl:"}</strong> ${detail.hlavni_prinos_text}</p>`
    );
  }
  if (detail.cilovy_efekt && distinctText(detail.cilovy_efekt, detail.hlavni_prinos_text)) {
    items.push(`<p><strong>Na co to tradičně míří:</strong> ${detail.cilovy_efekt}</p>`);
  }
  if (detail.aktivni_latky_text) {
    items.push(`<p><strong>Hlavní užitečné / aktivní látky:</strong> ${detail.aktivni_latky_text}</p>`);
  }
  if (detail.latky_a_logika_text) {
    items.push(`<p><strong>Látky a logika:</strong> ${detail.latky_a_logika_text}</p>`);
  }
  if (!items.length) {
    return "";
  }
  return `
    <section class="detail-section">
      <h3>${title}</h3>
      ${items.join("")}
    </section>
  `;
}

function renderResults(results) {
  els.results.innerHTML = "";
  if (!results.length) {
    els.results.innerHTML = `
      <div class="empty-state">
        Pro zadané filtry teď nic nevyšlo. Zkus širší hledání nebo vypnout některý z filtrů.
      </div>
    `;
    return;
  }

  results.forEach((result) => {
    const fragment = els.template.content.cloneNode(true);
    const card = fragment.querySelector(".result-card");
    const plantButton = card.querySelector(".plant-btn");
    const image = card.querySelector(".result-card-image");
    const placeholder = card.querySelector(".result-card-placeholder");
    card.querySelector(".card-id").textContent = result.raw_record_id;
    card.querySelector(".card-title").textContent = result.cesky_nazev_hlavni;
    card.querySelector(".card-subtitle").textContent = result.vedecky_nazev_hlavni;
    card.querySelector(".card-badges").innerHTML = renderBadges(result);
    card.querySelector(".meta-grid").innerHTML = renderMeta([
      result.cast_rostliny_text,
      result.poddomena_text,
      result.processing_methods_text,
      result.obdobi_ziskani_text,
      result.aplikovatelnost_v_cr,
      result.forma_uchovani_text,
    ]);
    card.querySelector(".card-effect").textContent =
      teaserText(result.hlavni_prinos_text || result.cilovy_efekt) || "Bez stručného shrnutí přínosu.";

    if (result.primary_photo) {
      image.src = result.primary_photo;
      image.alt = result.primary_photo_alt || result.cesky_nazev_hlavni;
      image.title = [result.primary_photo_credit, result.primary_photo_source_name].filter(Boolean).join(" · ");
      image.hidden = false;
      placeholder.hidden = true;
    } else {
      card.classList.add("result-card-no-photo");
    }

    card.querySelector(".detail-btn").addEventListener("click", () => openUseDetail(result.use_id));
    if (result.plant_id) {
      plantButton.addEventListener("click", () => openPlantDetail(result.plant_id));
    } else {
      plantButton.hidden = true;
    }
    els.results.appendChild(fragment);
  });
}

function bindDialogCloseButton() {
  const innerClose = els.detailContent.querySelector("#detail-close-inner");
  if (innerClose) {
    innerClose.addEventListener("click", () => els.dialog.close());
  }
}

function showDetailError(message) {
  els.detailContent.innerHTML = `<div class="empty-state">${message}</div>`;
  els.dialog.showModal();
}

function renderUseDetail(detail) {
  const aliasList = detail.aliases
    .map((alias) => `<li>${alias.alias} <small>(${alias.jazyk}, ${alias.typ_aliasu})</small></li>`)
    .join("");
  const sourceList = detail.sources
    .map(
      (source) => `
        <li>
          <strong>${source.raw_source_id}</strong> · ${source.role_zdroje}<br />
          <span>${source.nazev}</span><br />
          <a href="${source.url}" target="_blank" rel="noreferrer">${source.url}</a>
        </li>
      `
    )
    .join("");

  els.detailContent.innerHTML = `
    <button id="detail-close-inner" class="detail-close" type="button" aria-label="Zavřít detail">×</button>
    <div class="detail-grid">
      <div class="detail-hero">
        <div>
          <p class="eyebrow">${detail.raw_record_id}</p>
          <h2 class="detail-title">${detail.cesky_nazev_hlavni}</h2>
          <p class="card-subtitle">${detail.vedecky_nazev_hlavni}</p>
          <p>
            <button id="open-plant-profile" class="inline-link-btn" type="button">Otevřít profil celé rostliny</button>
            ·
            <a class="inline-link-btn" href="${appUrl(`/use/${encodeURIComponent(detail.use_id)}`)}">Samostatná stránka použití</a>
          </p>
          <div class="detail-meta">
            <span class="badge">${detail.domena}</span>
            <span class="badge">Důkaznost ${detail.dukaznost_skore}</span>
            <span class="meta-pill">${detail.cast_rostliny_text}</span>
            <span class="meta-pill">${detail.poddomena_text}</span>
            ${detail.processing_methods_text ? `<span class="meta-pill">${detail.processing_methods_text}</span>` : ""}
            ${detail.forma_uchovani_text ? `<span class="meta-pill">${detail.forma_uchovani_text}</span>` : ""}
            ${detail.orientacni_trvanlivost_text ? `<span class="meta-pill">${detail.orientacni_trvanlivost_text}</span>` : ""}
          </div>
        </div>
        ${renderPhotoBlock(detail.photos, "Foto pro tuhle rostlinu zatím není přiřazené. Přidat ho půjde přes lokální media manifest.")}
      </div>

      <section class="detail-section">
        <h3>Praktický popis</h3>
        <p>${detail.zpusob_pripravy || "Bez popisu přípravy."}</p>
      </section>

      ${renderFunctionalSection(detail)}

      <section class="detail-section">
        <h3>Jak sbírat správně</h3>
        <p>${detail.sber_doporuceni || "Bez odvozeného doporučení ke sběru."}</p>
      </section>

      <section class="detail-section">
        <h3>Metody dlouhodobého zpracování</h3>
        ${renderProcessingMethods(detail.processing_methods)}
      </section>

      <section class="detail-section">
        <h3>Sběr a lokalita</h3>
        <p><strong>Období:</strong> ${detail.obdobi_ziskani_text || "neuvedeno"}</p>
        <p><strong>Fenologie:</strong> ${detail.fenologicka_faze || "neuvedeno"}</p>
        <p><strong>Lokality:</strong> ${detail.typicke_lokality_text || "neuvedeno"}</p>
      </section>

      <section class="detail-section">
        <h3>Rizika a legální poznámka</h3>
        <p><strong>Rizika:</strong> ${detail.hlavni_rizika || "neuvedeno"}</p>
        <p><strong>Kontraindikace:</strong> ${detail.kontraindikace_interakce || "neuvedeno"}</p>
        <p><strong>Právo a sběr:</strong> ${detail.legalita_poznamka_cr || "neuvedeno"}</p>
      </section>

      ${
        detail.forma_uchovani_text
          ? `
        <section class="detail-section">
          <h3>Trvanlivost</h3>
          <p><strong>Forma:</strong> ${detail.forma_uchovani_text}</p>
          <p><strong>Interval:</strong> ${detail.orientacni_trvanlivost_text || "neuvedeno"}</p>
          <p><strong>Skladování:</strong> ${detail.poznamka_k_skladovani || "neuvedeno"}</p>
          ${detail.proc_je_v_jadru ? `<p><strong>Proč v jádru:</strong> ${detail.proc_je_v_jadru}</p>` : ""}
        </section>
      `
          : ""
      }

      <section class="detail-section">
        <h3>Aliasy</h3>
        <ul>${aliasList || "<li>Bez aliasů.</li>"}</ul>
      </section>

      <section class="detail-section">
        <h3>Zdroje</h3>
        <ul>${sourceList || "<li>Bez zdrojů.</li>"}</ul>
      </section>
    </div>
  `;

  bindDialogCloseButton();
  const plantButton = els.detailContent.querySelector("#open-plant-profile");
  if (plantButton) {
    plantButton.addEventListener("click", () => openPlantDetail(detail.plant_id));
  }
}

function renderPlantDetail(detail) {
  const aliasList = detail.aliases
    .map((alias) => `<li>${alias.alias} <small>(${alias.jazyk}, ${alias.typ_aliasu})</small></li>`)
    .join("");
  const sourceList = detail.sources
    .map(
      (source) => `
        <li>
          <strong>${source.raw_source_id}</strong> · ${source.use_count} použití<br />
          <span>${source.nazev}</span><br />
          <a href="${source.url}" target="_blank" rel="noreferrer">${source.url}</a>
        </li>
      `
    )
    .join("");
  const useList = detail.uses
    .map(
      (use) => `
        <li class="use-item">
          <div class="use-item-head">
            <div>
              <p class="use-item-title">${use.raw_record_id} · ${use.poddomena_text}</p>
              <p class="use-item-sub">${use.domena} · ${use.cast_rostliny_text} · ${use.obdobi_ziskani_text || "bez období"}</p>
            </div>
            <button class="inline-link-btn" type="button" data-use-id="${use.use_id}">Otevřít použití</button>
          </div>
          <div class="meta-grid">
            ${renderMeta([
              `Důkaznost ${use.dukaznost_skore}`,
              use.status_znalosti,
              use.aplikovatelnost_v_cr,
              use.processing_methods_text,
              use.forma_uchovani_text,
              use.orientacni_trvanlivost_text,
              use.je_v_jadru_bezne_1m_plus ? "Jádro" : "",
            ])}
          </div>
          <p class="use-item-sub">${use.hlavni_prinos_text || use.cilovy_efekt || "Bez stručného shrnutí přínosu."}</p>
          ${
            use.cilovy_efekt && distinctText(use.cilovy_efekt, use.hlavni_prinos_text)
              ? `<p class="use-item-note"><strong>Na co míří:</strong> ${use.cilovy_efekt}</p>`
              : ""
          }
          <p class="use-item-note"><strong>Jak sbírat:</strong> ${use.sber_doporuceni || "neuvedeno"}</p>
        </li>
      `
    )
    .join("");

  els.detailContent.innerHTML = `
    <button id="detail-close-inner" class="detail-close" type="button" aria-label="Zavřít detail">×</button>
    <div class="detail-grid">
      <div class="detail-hero">
        <div>
          <p class="eyebrow">Profil rostliny</p>
          <h2 class="detail-title">${detail.cesky_nazev_hlavni}</h2>
          <p class="card-subtitle">${detail.vedecky_nazev_hlavni}</p>
          <p><a class="inline-link-btn" href="${appUrl(`/plant/${encodeURIComponent(detail.plant_id)}`)}">Samostatná stránka rostliny</a></p>
          <div class="detail-meta">
            <span class="badge">${detail.pocet_pouziti} použití</span>
            <span class="meta-pill">${detail.status_v_cr_text || "bez statusu"}</span>
            <span class="meta-pill">${detail.stats.durable_use_count} trvanlivých</span>
            <span class="meta-pill">${detail.stats.core_use_count} v jádru</span>
            <span class="meta-pill">${detail.stats.processing_use_count} se zpracováním</span>
          </div>
        </div>
        ${renderPhotoBlock(detail.photos, "Foto zatím není přidané. Aplikace už ale umí zobrazit lokální i webové obrázky přes plant media manifest.")}
      </div>

      <section class="detail-section">
        <h3>Status v ČR</h3>
        <p><strong>Text:</strong> ${detail.status_v_cr_text || "neuvedeno"}</p>
        <p>
          <strong>Příznaky:</strong>
          ${[
            detail.status_puvodni ? "původní" : "",
            detail.status_zdomacnely ? "zdomácnělý" : "",
            detail.status_pestovany ? "pěstovaný" : "",
            detail.status_zplanujici ? "zplaňující" : "",
            detail.status_invazni ? "invazní" : "",
          ]
            .filter(Boolean)
            .join(", ") || "bez strukturálních příznaků"}
        </p>
      </section>

      ${renderFunctionalSection(detail, { title: "Látky a přínosy rostliny", plantLevel: true })}

      <section class="detail-section">
        <h3>Aliasy</h3>
        <ul>${aliasList || "<li>Bez aliasů.</li>"}</ul>
      </section>

      <section class="detail-section">
        <h3>Použití této rostliny</h3>
        <ul class="use-list">${useList || "<li>Bez použití.</li>"}</ul>
      </section>

      <section class="detail-section">
        <h3>Zdroje</h3>
        <ul>${sourceList || "<li>Bez zdrojů.</li>"}</ul>
      </section>
    </div>
  `;

  els.detailContent.querySelectorAll("[data-use-id]").forEach((button) => {
    button.addEventListener("click", () => openUseDetail(button.dataset.useId));
  });
  bindDialogCloseButton();
}

async function openUseDetail(useId) {
  try {
    const detail = await fetchJson(`/api/use?use_id=${encodeURIComponent(useId)}`);
    renderUseDetail(detail);
    els.dialog.showModal();
  } catch (error) {
    showDetailError(`Nepodařilo se načíst detail použití: ${error.message}`);
  }
}

async function openPlantDetail(plantId) {
  try {
    const detail = await fetchJson(`/api/plant?plant_id=${encodeURIComponent(plantId)}`);
    renderPlantDetail(detail);
    els.dialog.showModal();
  } catch (error) {
    showDetailError(`Nepodařilo se načíst profil rostliny: ${error.message}`);
  }
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

async function search() {
  els.resultsTitle.textContent = "Hledání";
  const data = await fetchJson(`/api/search?${buildSearchParams().toString()}`);
  syncUrl();
  renderSeasonalNote(data.seasonal_window || seasonalDefault);
  els.resultsTitle.textContent = pluralizeResults(data.count);
  renderResults(data.results);
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
  await discoverApiBase();
  const summary = initialSummary;
  const options = initialOptions;
  renderSummary(summary);
  seasonalDefault = options.seasonal_default || null;

  populateSelect(els.domena, options.domains || []);
  populateSelect(els.evidenceMin, options.evidence_scores || []);
  populateSelect(
    els.partCategory,
    (options.part_categories || []).map((value) => ({ value, label: labelize(value) })),
    { valueKey: "value", labelKey: "label" }
  );
  populateSelect(
    els.subdomainCategory,
    (options.subdomain_categories || []).map((value) => ({ value, label: labelize(value) })),
    { valueKey: "value", labelKey: "label" }
  );
  populateSelect(els.processingMethod, options.processing_methods || [], { valueKey: "value", labelKey: "label" });
  populateSelect(els.month, options.months || [], { valueKey: "value", labelKey: "label" });
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
  els.detailClose.addEventListener("click", () => els.dialog.close());
  els.dialog.addEventListener("click", (event) => {
    const rect = els.dialog.getBoundingClientRect();
    const inDialog =
      rect.top <= event.clientY &&
      event.clientY <= rect.top + rect.height &&
      rect.left <= event.clientX &&
      event.clientX <= rect.left + rect.width;
    if (!inDialog) els.dialog.close();
  });

  await search();
}

init().catch((error) => {
  els.resultsTitle.textContent = "Chyba";
  els.results.innerHTML = `<div class="empty-state">Nepodařilo se načíst data: ${error.message}</div>`;
});
