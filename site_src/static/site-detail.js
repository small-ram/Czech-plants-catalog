const C = window.CatalogSite;

function renderProcessingMethods(methods) {
  if (!methods?.length) {
    return "<p>Neuvedeno.</p>";
  }
  return `<ul>${methods.map((method) => `<li>${C.escapeHtml(method.label)}</li>`).join("")}</ul>`;
}

function routeInfo() {
  if (window.CATALOG_DETAIL?.kind && window.CATALOG_DETAIL?.id) {
    return window.CATALOG_DETAIL;
  }

  const params = new URLSearchParams(window.location.search);
  const kind = params.get("kind");
  const id = params.get("id");
  if (kind && id) return { kind, id };
  return null;
}

function setActions(route) {
  const actions = document.getElementById("detail-page-actions");
  const exportBase =
    route.kind === "plant"
      ? C.siteUrl(`export/plant/${encodeURIComponent(route.id)}`)
      : C.siteUrl(`export/use/${encodeURIComponent(route.id)}`);

  actions.innerHTML = `
    <button id="copy-link-btn" class="ghost-btn" type="button">Kopírovat odkaz</button>
    <a class="ghost-btn" href="${exportBase}.json">Stáhnout JSON</a>
    <a class="detail-btn" href="${exportBase}.md">Stáhnout Markdown</a>
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

function sectionNav(items) {
  return `
    <nav class="section-nav" aria-label="Rychlá navigace po detailu">
      ${items.map((item) => `<a href="#${C.escapeHtml(item.id)}">${C.escapeHtml(item.label)}</a>`).join("")}
    </nav>
  `;
}

function section(id, title, content) {
  return `
    <section id="${C.escapeHtml(id)}" class="detail-section detail-section-anchor">
      <h3>${C.escapeHtml(title)}</h3>
      ${content}
    </section>
  `;
}

function renderUsePage(detail) {
  setHeader({
    eyebrow: `Detail použití · ${detail.raw_record_id}`,
    title: detail.cesky_nazev_hlavni,
    subtitle: detail.vedecky_nazev_hlavni,
    summaryHtml: `
      <div class="stat-card"><strong>${C.escapeHtml(detail.domena)}</strong><span>Doména</span></div>
      <div class="stat-card"><strong>${C.escapeHtml(C.evidenceLabel(detail.dukaznost_skore))}</strong><span>Důkaznost</span></div>
      <div class="stat-card"><strong>${C.escapeHtml(detail.obdobi_ziskani_text || "?")}</strong><span>Období</span></div>
    `,
    metaHtml: C.renderMeta([
      detail.cast_rostliny_text,
      detail.poddomena_text,
      detail.processing_methods_text,
      detail.forma_uchovani_text,
      detail.orientacni_trvanlivost_text,
      C.knowledgeLabel(detail.status_znalosti),
    ]),
  });

  const aliasList = (detail.aliases || [])
    .map(
      (alias) =>
        `<li>${C.escapeHtml(alias.alias)} <small>(${C.escapeHtml(alias.jazyk)}, ${C.escapeHtml(alias.typ_aliasu)})</small></li>`
    )
    .join("");

  const sourceList = (detail.sources || [])
    .map((source) => {
      const url = source.url
        ? `<a href="${C.escapeHtml(source.url)}" target="_blank" rel="noreferrer">Otevřít zdroj</a>`
        : "";
      return `
        <li>
          <strong>${C.escapeHtml(source.raw_source_id)}</strong> · ${C.escapeHtml(source.role_zdroje)}<br />
          <span>${C.escapeHtml(source.nazev)}</span><br />
          ${url}
        </li>
      `;
    })
    .join("");

  const sections = [
    { id: "prakticky-popis", label: "Praktický popis" },
    { id: "cilovy-efekt", label: "Cílový efekt" },
    { id: "jak-sbirat", label: "Jak sbírat" },
    { id: "metody-zpracovani", label: "Metody zpracování" },
    { id: "sber-a-lokalita", label: "Sběr a lokalita" },
    { id: "rizika-a-legalita", label: "Rizika a legalita" },
    ...(detail.forma_uchovani_text ? [{ id: "trvanlivost", label: "Trvanlivost" }] : []),
    { id: "aliasy", label: "Aliasy" },
    { id: "zdroje", label: "Zdroje" },
  ];

  document.getElementById("detail-page-content").innerHTML = `
    ${sectionNav(sections)}
    <div class="detail-grid">
      <div class="detail-hero standalone-hero">
        <div>
          <p><a class="inline-link-btn" href="${C.siteUrl(`plant/${encodeURIComponent(detail.plant_id)}/`)}">Otevřít profil celé rostliny</a></p>
          <div class="detail-meta">
            <span class="badge">${C.escapeHtml(detail.domena)}</span>
            <span class="badge">${C.escapeHtml(C.evidenceLabel(detail.dukaznost_skore))}</span>
            <span class="meta-pill">${C.escapeHtml(detail.aplikovatelnost_v_cr || "neuvedeno")}</span>
          </div>
        </div>
        ${C.renderPhotoBlock(detail.photos, "Foto pro tuhle rostlinu zatím není přiřazené.")}
      </div>

      ${section("prakticky-popis", "Praktický popis", `<p>${C.escapeHtml(detail.zpusob_pripravy || "Bez popisu přípravy.")}</p>`)}
      ${section("cilovy-efekt", "Cílový efekt", `<p>${C.escapeHtml(detail.cilovy_efekt || "Bez popisu.")}</p>`)}
      ${section("jak-sbirat", "Jak sbírat správně", `<p>${C.escapeHtml(detail.sber_doporuceni || "Bez odvozeného doporučení ke sběru.")}</p>`)}
      ${section("metody-zpracovani", "Metody dlouhodobého zpracování", renderProcessingMethods(detail.processing_methods))}
      ${section(
        "sber-a-lokalita",
        "Sběr a lokalita",
        `
          <p><strong>Období:</strong> ${C.escapeHtml(detail.obdobi_ziskani_text || "neuvedeno")}</p>
          <p><strong>Fenologie:</strong> ${C.escapeHtml(detail.fenologicka_faze || "neuvedeno")}</p>
          <p><strong>Lokality:</strong> ${C.escapeHtml(detail.typicke_lokality_text || "neuvedeno")}</p>
        `
      )}
      ${section(
        "rizika-a-legalita",
        "Rizika a legální poznámka",
        `
          <p><strong>Rizika:</strong> ${C.escapeHtml(detail.hlavni_rizika || "neuvedeno")}</p>
          <p><strong>Kontraindikace:</strong> ${C.escapeHtml(detail.kontraindikace_interakce || "neuvedeno")}</p>
          <p><strong>Právo a sběr:</strong> ${C.escapeHtml(detail.legalita_poznamka_cr || "neuvedeno")}</p>
        `
      )}
      ${
        detail.forma_uchovani_text
          ? section(
              "trvanlivost",
              "Trvanlivost",
              `
                <p><strong>Forma:</strong> ${C.escapeHtml(detail.forma_uchovani_text)}</p>
                <p><strong>Interval:</strong> ${C.escapeHtml(detail.orientacni_trvanlivost_text || "neuvedeno")}</p>
                <p><strong>Skladování:</strong> ${C.escapeHtml(detail.poznamka_k_skladovani || "neuvedeno")}</p>
                ${detail.proc_je_v_jadru ? `<p><strong>Proč v jádru:</strong> ${C.escapeHtml(detail.proc_je_v_jadru)}</p>` : ""}
              `
            )
          : ""
      }
      ${section("aliasy", "Aliasy", `<ul>${aliasList || "<li>Bez aliasů.</li>"}</ul>`)}
      ${section("zdroje", "Zdroje", `<ul>${sourceList || "<li>Bez zdrojů.</li>"}</ul>`)}
    </div>
  `;
}

function renderPlantPage(detail) {
  const aliasList = (detail.aliases || [])
    .map(
      (alias) =>
        `<li>${C.escapeHtml(alias.alias)} <small>(${C.escapeHtml(alias.jazyk)}, ${C.escapeHtml(alias.typ_aliasu)})</small></li>`
    )
    .join("");

  const sourceList = (detail.sources || [])
    .map((source) => {
      const url = source.url
        ? `<a href="${C.escapeHtml(source.url)}" target="_blank" rel="noreferrer">Otevřít zdroj</a>`
        : "";
      return `
        <li>
          <strong>${C.escapeHtml(source.raw_source_id)}</strong> · ${C.escapeHtml(source.use_count)} použití<br />
          <span>${C.escapeHtml(source.nazev)}</span><br />
          ${url}
        </li>
      `;
    })
    .join("");

  const useList = (detail.uses || [])
    .map(
      (use) => `
        <li class="use-item">
          <div class="use-item-head">
            <div>
              <p class="use-item-title">${C.escapeHtml(use.raw_record_id)} · ${C.escapeHtml(use.poddomena_text)}</p>
              <p class="use-item-sub">${C.escapeHtml(use.domena)} · ${C.escapeHtml(use.cast_rostliny_text)} · ${C.escapeHtml(use.obdobi_ziskani_text || "bez období")}</p>
            </div>
            <a class="inline-link-btn" href="${C.siteUrl(`use/${encodeURIComponent(use.use_id)}/`)}">Detail použití</a>
          </div>
          <div class="meta-grid">
            ${C.renderMeta([
              C.evidenceLabel(use.dukaznost_skore),
              C.knowledgeLabel(use.status_znalosti),
              use.aplikovatelnost_v_cr,
              use.processing_methods_text,
              use.forma_uchovani_text,
              use.orientacni_trvanlivost_text,
              use.je_v_jadru_bezne_1m_plus ? "Praktické jádro" : "",
            ])}
          </div>
          <p class="use-item-sub">${C.escapeHtml(use.cilovy_efekt || "Bez popisu cílového efektu.")}</p>
          <p class="use-item-note"><strong>Jak sbírat:</strong> ${C.escapeHtml(use.sber_doporuceni || "neuvedeno")}</p>
        </li>
      `
    )
    .join("");

  setHeader({
    eyebrow: "Profil rostliny",
    title: detail.cesky_nazev_hlavni,
    subtitle: detail.vedecky_nazev_hlavni,
    summaryHtml: `
      <div class="stat-card"><strong>${C.escapeHtml(detail.stats.use_count)}</strong><span>Použití</span></div>
      <div class="stat-card"><strong>${C.escapeHtml(detail.stats.durable_use_count)}</strong><span>Trvanlivá</span></div>
      <div class="stat-card"><strong>${C.escapeHtml(detail.stats.core_use_count)}</strong><span>V jádru</span></div>
    `,
    metaHtml: C.renderMeta([
      detail.status_v_cr_text,
      detail.status_cetnost_reprezentativni,
      `${detail.pocet_ceskych_aliasu} českých aliasů`,
    ]),
  });

  const sections = [
    { id: "status-v-cr", label: "Status v ČR" },
    { id: "aliasy", label: "Aliasy" },
    { id: "pouziti-rostliny", label: "Použití" },
    { id: "zdroje", label: "Zdroje" },
  ];

  document.getElementById("detail-page-content").innerHTML = `
    ${sectionNav(sections)}
    <div class="detail-grid">
      <div class="detail-hero standalone-hero">
        <div>
          <div class="detail-meta">
            <span class="badge">${C.escapeHtml(detail.stats.use_count)} použití</span>
            <span class="meta-pill">${C.escapeHtml(detail.status_v_cr_text || "bez statusu")}</span>
            <span class="meta-pill">${C.escapeHtml(detail.stats.durable_use_count)} trvanlivých</span>
            <span class="meta-pill">${C.escapeHtml(detail.stats.core_use_count)} v jádru</span>
            <span class="meta-pill">${C.escapeHtml(detail.stats.processing_use_count)} se zpracováním</span>
          </div>
        </div>
        ${C.renderPhotoBlock(detail.photos, "Foto zatím není přidané.")}
      </div>

      ${section(
        "status-v-cr",
        "Status v ČR",
        `
          <p><strong>Text:</strong> ${C.escapeHtml(detail.status_v_cr_text || "neuvedeno")}</p>
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
              .map((item) => C.escapeHtml(item))
              .join(", ") || "bez strukturálních příznaků"}
          </p>
        `
      )}
      ${section("aliasy", "Aliasy", `<ul>${aliasList || "<li>Bez aliasů.</li>"}</ul>`)}
      ${section("pouziti-rostliny", "Použití této rostliny", `<ul class="use-list">${useList || "<li>Bez použití.</li>"}</ul>`)}
      ${section("zdroje", "Zdroje", `<ul>${sourceList || "<li>Bez zdrojů.</li>"}</ul>`)}
    </div>
  `;
}

async function init() {
  const route = routeInfo();
  if (!route) {
    throw new Error("Chybí konfigurace detailu.");
  }

  setActions(route);
  const detail = route.kind === "plant" ? await C.loadPlantDetail(route.id) : await C.loadUseDetail(route.id);
  if (route.kind === "plant") {
    renderPlantPage(detail);
  } else {
    renderUsePage(detail);
  }
}

init().catch((error) => {
  document.getElementById("detail-page-title").textContent = "Chyba";
  document.getElementById("detail-page-content").innerHTML = `<div class="empty-state">Nepodařilo se načíst detail: ${C.escapeHtml(error.message)}</div>`;
});
