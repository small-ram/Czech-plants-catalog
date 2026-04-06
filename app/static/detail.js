function renderMeta(values) {
  return values
    .filter(Boolean)
    .map((value) => `<span class="meta-pill">${value}</span>`)
    .join("");
}

let apiBase = "";

const API_BASE_CANDIDATES = ["", "http://127.0.0.1:8766"];

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
      const options = await fetchJsonAbsolute(candidate ? `${candidate}/api/options` : "/api/options");
      if (isCompatibleOptions(options)) {
        apiBase = candidate;
        return;
      }
    } catch (_error) {
      // Try the next candidate.
    }
  }
  throw new Error("Nepodařilo se najít kompatibilní katalogové API.");
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
  if (!parts.length) return "";
  return `<figcaption class="photo-caption">${parts.join(" · ")}</figcaption>`;
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

function renderFunctionalSection(detail, { title = "Látky a přínosy", plantLevel = false } = {}) {
  const items = [];
  if (detail.hlavni_prinos_text) {
    items.push(
      `<p><strong>${plantLevel ? "Proč je rostlina zajímavá:" : "Proč to může dávat smysl:"}</strong> ${C.escapeHtml(detail.hlavni_prinos_text)}</p>`
    );
  }
  if (detail.cilovy_efekt && distinctText(detail.cilovy_efekt, detail.hlavni_prinos_text)) {
    items.push(`<p><strong>Na co to tradičně míří:</strong> ${C.escapeHtml(detail.cilovy_efekt)}</p>`);
  }
  if (detail.aktivni_latky_text) {
    items.push(`<p><strong>Hlavní užitečné / aktivní látky:</strong> ${C.escapeHtml(detail.aktivni_latky_text)}</p>`);
  }
  if (detail.latky_a_logika_text) {
    items.push(`<p><strong>Látky a logika:</strong> ${C.escapeHtml(detail.latky_a_logika_text)}</p>`);
  }
  if (!items.length) {
    return "";
  }
  return `
    <section class="detail-section">
      <h3>${C.escapeHtml(title)}</h3>
      ${items.join("")}
    </section>
  `;
}

function routeInfo() {
  const parts = window.location.pathname.split("/").filter(Boolean);
  if (parts.length >= 2 && parts[0] === "plant") {
    return { kind: "plant", id: decodeURIComponent(parts.slice(1).join("/")) };
  }
  if (parts.length >= 2 && parts[0] === "use") {
    return { kind: "use", id: decodeURIComponent(parts.slice(1).join("/")) };
  }
  return null;
}

function setActions(route) {
  const actions = document.getElementById("detail-page-actions");
  const exportBase =
    route.kind === "plant"
      ? appUrl(`/export/plant/${encodeURIComponent(route.id)}`)
      : appUrl(`/export/use/${encodeURIComponent(route.id)}`);

  actions.innerHTML = `
    <button id="copy-link-btn" class="ghost-btn" type="button">Kopírovat odkaz</button>
    <a class="ghost-btn" href="${exportBase}.json">JSON</a>
    <a class="detail-btn" href="${exportBase}.md">Markdown</a>
  `;

  const copyButton = document.getElementById("copy-link-btn");
  copyButton.addEventListener("click", async () => {
    const originalLabel = copyButton.textContent;
    try {
      await navigator.clipboard.writeText(window.location.href);
      copyButton.textContent = "Zkopírováno";
      setTimeout(() => {
        copyButton.textContent = originalLabel;
      }, 1400);
    } catch {
      copyButton.textContent = "Nešlo zkopírovat";
      setTimeout(() => {
        copyButton.textContent = originalLabel;
      }, 1400);
    }
  });
}

function setHeader({ eyebrow, title, subtitle, summaryHtml = "", metaHtml = "" }) {
  document.getElementById("detail-page-eyebrow").textContent = eyebrow;
  document.getElementById("detail-page-title").textContent = title;
  document.getElementById("detail-page-subtitle").textContent = subtitle || "";
  document.getElementById("detail-page-summary").innerHTML = summaryHtml;
  document.getElementById("detail-page-meta").innerHTML = metaHtml;
  document.title = `${title} | České rostliny`;
}

function renderUsePage(detail) {
  setHeader({
    eyebrow: detail.raw_record_id,
    title: detail.cesky_nazev_hlavni,
    subtitle: detail.vedecky_nazev_hlavni,
    summaryHtml: `
      <div class="stat-card"><strong>${detail.domena}</strong><span>Doména</span></div>
      <div class="stat-card"><strong>${detail.dukaznost_skore}</strong><span>Důkaznost</span></div>
      <div class="stat-card"><strong>${detail.obdobi_ziskani_text || "?"}</strong><span>Období</span></div>
    `,
    metaHtml: renderMeta([
      detail.cast_rostliny_text,
      detail.poddomena_text,
      detail.processing_methods_text,
      detail.forma_uchovani_text,
      detail.orientacni_trvanlivost_text,
    ]),
  });

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

  document.getElementById("detail-page-content").innerHTML = `
    <div class="detail-grid">
      <div class="detail-hero standalone-hero">
        <div>
          <p><a class="inline-link-btn" href="${appUrl(`/plant/${encodeURIComponent(detail.plant_id)}`)}">Otevřít profil celé rostliny</a></p>
          <div class="detail-meta">
            <span class="badge">${detail.domena}</span>
            <span class="badge">Důkaznost ${detail.dukaznost_skore}</span>
            <span class="meta-pill">${detail.aplikovatelnost_v_cr}</span>
          </div>
        </div>
        ${renderPhotoBlock(detail.photos, "Foto pro tuhle rostlinu zatím není přiřazené. Přidat ho půjde přes plant_media.json.")}
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
}

function renderPlantPage(detail) {
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
            <a class="inline-link-btn" href="${appUrl(`/use/${encodeURIComponent(use.use_id)}`)}">Otevřít použití</a>
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

  setHeader({
    eyebrow: "Profil rostliny",
    title: detail.cesky_nazev_hlavni,
    subtitle: detail.vedecky_nazev_hlavni,
    summaryHtml: `
      <div class="stat-card"><strong>${detail.stats.use_count}</strong><span>Použití</span></div>
      <div class="stat-card"><strong>${detail.stats.durable_use_count}</strong><span>Trvanlivá</span></div>
      <div class="stat-card"><strong>${detail.stats.core_use_count}</strong><span>V jádru</span></div>
    `,
    metaHtml: renderMeta([detail.status_v_cr_text]),
  });

  document.getElementById("detail-page-content").innerHTML = `
    <div class="detail-grid">
      <div class="detail-hero standalone-hero">
        <div>
          <div class="detail-meta">
            <span class="meta-pill">${detail.status_v_cr_text || "bez statusu"}</span>
            <span class="meta-pill">${detail.pocet_pouziti} použití</span>
            <span class="meta-pill">${detail.pocet_ceskych_aliasu} českých aliasů</span>
            <span class="meta-pill">${detail.stats.processing_use_count} se zpracováním</span>
          </div>
        </div>
        ${renderPhotoBlock(detail.photos, "Foto zatím není přidané. Přidat ho můžeš přes app/media/plant_media.json.")}
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
        <h3>Zdroje napříč rostlinou</h3>
        <ul>${sourceList || "<li>Bez zdrojů.</li>"}</ul>
      </section>
    </div>
  `;
}

async function init() {
  await discoverApiBase();
  const route = routeInfo();
  if (!route) {
    document.getElementById("detail-page-content").innerHTML = `
      <div class="empty-state">Neplatná detailní cesta. Vrať se do katalogu a zkus to znovu.</div>
    `;
    return;
  }

  setActions(route);

  try {
    if (route.kind === "plant") {
      const detail = await fetchJson(`/api/plant?plant_id=${encodeURIComponent(route.id)}`);
      renderPlantPage(detail);
    } else {
      const detail = await fetchJson(`/api/use?use_id=${encodeURIComponent(route.id)}`);
      renderUsePage(detail);
    }
  } catch (error) {
    document.getElementById("detail-page-content").innerHTML = `
      <div class="empty-state">Nepodařilo se načíst detail: ${error.message}</div>
    `;
  }
}

init();
