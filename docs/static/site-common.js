(function () {
  const MONTH_LABELS = [
    "",
    "leden",
    "únor",
    "březen",
    "duben",
    "květen",
    "červen",
    "červenec",
    "srpen",
    "září",
    "říjen",
    "listopad",
    "prosinec",
  ];

  const MONTH_LABELS_GENITIVE = [
    "",
    "ledna",
    "února",
    "března",
    "dubna",
    "května",
    "června",
    "července",
    "srpna",
    "září",
    "října",
    "listopadu",
    "prosince",
  ];

  const MEDIA_KIND_LABELS = {
    photo: "Foto",
    illustration: "Ilustrace",
    auto_cover: "Auto-cover",
  };

  const EVIDENCE_LABELS = {
    A: "A · nejsilnější opora",
    B: "B · silná opora",
    C: "C · střední opora",
    D: "D · slabší opora",
    E: "E · ojedinělá zmínka",
  };

  const RAW_DOMAIN_LABELS = {
    potrava: "Jídlo",
    pití: "Pití",
    "potrava a pití": "Jídlo i pití",
    fytoterapie: "Léčivé",
    léčba: "Léčivé",
    palivo: "Palivo",
    vůně: "Vůně",
  };

  const DOMAIN_GROUPS = [
    {
      value: "food",
      label: "Jídlo",
      raw: ["potrava", "potrava a pití"],
    },
    {
      value: "drink",
      label: "Pití",
      raw: ["pití", "potrava a pití"],
    },
    {
      value: "healing",
      label: "Léčivé",
      raw: ["fytoterapie", "léčba"],
    },
    {
      value: "fuel",
      label: "Palivo",
      raw: ["palivo"],
    },
    {
      value: "scent",
      label: "Vůně",
      raw: ["vůně"],
    },
  ];

  const PART_CATEGORY_LABELS = {
    drevnata_cast: "Kůra / dřevo",
    kombinovana_cast: "Více částí",
    kvetni_cast: "Květy",
    listova_nadzemni_cast: "Listy / nať",
    miza: "Míza",
    ostatni: "Jiné",
    plodova_cast: "Plody",
    podzemni_cast: "Kořen / oddenek",
    semena_a_orisky: "Semena / oříšky",
    vyhonky_a_pupeny: "Pupeny / mladé výhony",
  };

  const SUBDOMAIN_CATEGORY_LABELS = {
    caj_nalev: "Čaj a nálev",
    cerstva_potrava: "Čerstvě k jídlu",
    fermentace: "Fermentace",
    kavova_nahrada: "Kávová náhražka",
    koreni_dochucovadlo: "Koření a dochucení",
    liker_macerat: "Likér / macerát",
    mouka_skrob: "Mouka / škrob",
    ocet: "Ocet",
    odvar: "Odvar",
    olej: "Olej",
    ostatni_specialni: "Speciální použití",
    palivo: "Palivo",
    sirup_koncentrat: "Sirup / koncentrát",
    suseni_skladovani: "Sušení / uskladnění",
    vune_a_vykurovani: "Vůně / vykuřování",
    zavarenina: "Zavařeniny a sladké uchování",
    zevni_aplikace: "Zevní použití",
  };

  const KNOWLEDGE_LABELS = {
    mainstream: "běžně známé",
    "méně známé": "méně známé",
    "téměř zapomenuté": "téměř zapomenuté",
    "globální analog": "známé hlavně v zahraničí",
  };

  const KNOWLEDGE_SORT = {
    "téměř zapomenuté": 4,
    "méně známé": 3,
    "globální analog": 2,
    mainstream: 1,
  };

  let bundlePromise = null;
  const domainGroupMap = new Map(DOMAIN_GROUPS.map((group) => [group.value, group]));

  function basePath() {
    return window.CATALOG_BASE || ".";
  }

  function siteUrl(path = "") {
    const base = String(basePath()).replace(/\/+$/, "") || ".";
    const clean = String(path || "").replace(/^\/+/, "");
    return clean ? `${base}/${clean}` : base;
  }

  function assetUrl(path = "") {
    if (!path) return "";
    if (/^https?:\/\//i.test(path)) return path;
    return siteUrl(path);
  }

  async function fetchJson(path) {
    const response = await fetch(siteUrl(path));
    if (!response.ok) {
      throw new Error(`Request failed: ${response.status}`);
    }
    return response.json();
  }

  async function loadBundle() {
    if (!bundlePromise) {
      bundlePromise = fetchJson("data/catalog_bundle.json");
    }
    return bundlePromise;
  }

  async function loadUseDetail(useId) {
    return fetchJson(`data/use/${encodeURIComponent(useId)}.json`);
  }

  async function loadPlantDetail(plantId) {
    return fetchJson(`data/plant/${encodeURIComponent(plantId)}.json`);
  }

  function wrapMonth(month) {
    if (month < 1) return 12;
    if (month > 12) return 1;
    return month;
  }

  function seasonalWindowPayload(forDate = new Date()) {
    const today = forDate;
    const currentMonth = today.getMonth() + 1;
    const previousMonth = wrapMonth(currentMonth - 1);
    const nextMonth = wrapMonth(currentMonth + 1);

    let months;
    let mode;
    let reason;

    if (today.getDate() <= 10) {
      months = [previousMonth, currentMonth];
      mode = "early_month";
      reason = "začátek měsíce: minulý + aktuální";
    } else if (today.getDate() >= 22) {
      months = [currentMonth, nextMonth];
      mode = "late_month";
      reason = "konec měsíce: aktuální + následující";
    } else {
      months = [previousMonth, currentMonth, nextMonth];
      mode = "mid_month";
      reason = "střed měsíce: minulý + aktuální + následující";
    }

    return {
      enabled_by_default: true,
      today_iso: today.toISOString().slice(0, 10),
      today_label: `${today.getDate()}. ${MONTH_LABELS_GENITIVE[currentMonth]} ${today.getFullYear()}`,
      months,
      month_labels: months.map((month) => MONTH_LABELS[month]),
      label: months.map((month) => MONTH_LABELS[month]).join(" + "),
      mode,
      reason,
    };
  }

  function monthMatches(record, month) {
    const from = Number(record?.mesic_od);
    const to = Number(record?.mesic_do);
    if (!from || !to || !month) return false;
    if (from <= to) {
      return month >= from && month <= to;
    }
    return month >= from || month <= to;
  }

  function normalizeBooleanish(value) {
    return value === true || value === 1 || value === "1";
  }

  function rankThreshold(score) {
    return { A: 5, B: 4, C: 3, D: 2, E: 1 }[score] || null;
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function labelize(value) {
    return String(value || "")
      .replaceAll("_", " ")
      .replace(/\b\w/g, (char) => char.toUpperCase());
  }

  function evidenceLabel(score) {
    return EVIDENCE_LABELS[score] || score || "";
  }

  function evidenceScoreFromRank(rank) {
    return { 5: "A", 4: "B", 3: "C", 2: "D", 1: "E" }[Number(rank)] || "";
  }

  function domainLabel(rawDomain) {
    return RAW_DOMAIN_LABELS[String(rawDomain || "").trim()] || rawDomain || "";
  }

  function domainGroupOptions() {
    return DOMAIN_GROUPS.map((group) => ({
      value: group.value,
      label: group.label,
    }));
  }

  function domainGroupLabel(groupValue) {
    return domainGroupMap.get(groupValue)?.label || groupValue || "";
  }

  function domainGroupIdsFromValue(value) {
    const clean = String(value || "").trim();
    if (!clean) return [];
    if (domainGroupMap.has(clean)) return [clean];
    return DOMAIN_GROUPS.filter((group) => group.raw.includes(clean)).map((group) => group.value);
  }

  function domainGroupMatches(rawDomain, groupValue) {
    const group = domainGroupMap.get(String(groupValue || "").trim());
    if (!group) return false;
    return group.raw.includes(String(rawDomain || "").trim());
  }

  function monthLabel(month) {
    return MONTH_LABELS[Number(month)] || String(month || "");
  }

  function knowledgeRank(status) {
    return KNOWLEDGE_SORT[String(status || "").trim()] || 0;
  }

  function knowledgeLabel(status) {
    const raw = String(status || "").trim();
    return KNOWLEDGE_LABELS[raw] || raw;
  }

  function partCategoryLabel(value) {
    const raw = String(value || "").trim();
    return PART_CATEGORY_LABELS[raw] || labelize(raw);
  }

  function subdomainCategoryLabel(value) {
    const raw = String(value || "").trim();
    return SUBDOMAIN_CATEGORY_LABELS[raw] || labelize(raw);
  }

  function renderMeta(values) {
    return (values || [])
      .filter(Boolean)
      .map((value) => `<span class="meta-pill">${escapeHtml(value)}</span>`)
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
    if (photo?.media_kind_label) return photo.media_kind_label;
    if (photo?.media_kind) return MEDIA_KIND_LABELS[photo.media_kind] || photo.media_kind;
    return "";
  }

  function renderPhotoCaption(photo) {
    const parts = [];
    const kindLabel = mediaKindLabel(photo);
    if (kindLabel) {
      parts.push(
        `<span class="photo-kind-pill ${mediaKindClass(photo.media_kind)}">${escapeHtml(kindLabel)}</span>`
      );
    }
    if (photo.caption) parts.push(`<span>${escapeHtml(photo.caption)}</span>`);
    if (photo.credit) parts.push(`<span>${escapeHtml(photo.credit)}</span>`);
    if (photo.license) parts.push(`<span>${escapeHtml(photo.license)}</span>`);
    if (photo.source_url) {
      parts.push(
        `<a class="photo-source-link" href="${escapeHtml(photo.source_url)}" target="_blank" rel="noreferrer">${escapeHtml(photo.source_name || "Zdroj")}</a>`
      );
    }
    if (!parts.length) return "";
    return `<figcaption class="photo-caption">${parts.join(" · ")}</figcaption>`;
  }

  function renderPhotoBlock(photos, fallbackText) {
    if (!photos || !photos.length) {
      return `<div class="photo-placeholder"><div>${escapeHtml(fallbackText)}</div></div>`;
    }

    return `
      <div class="photo-grid">
        ${photos
          .map(
            (photo) => `
              <figure class="photo-card">
                <img src="${escapeHtml(assetUrl(photo.src))}" alt="${escapeHtml(photo.alt || "")}" loading="lazy" />
                ${renderPhotoCaption(photo)}
              </figure>
            `
          )
          .join("")}
      </div>
    `;
  }

  window.CatalogSite = {
    MONTH_LABELS,
    MONTH_LABELS_GENITIVE,
    assetUrl,
    domainGroupIdsFromValue,
    domainGroupLabel,
    domainGroupMatches,
    domainGroupOptions,
    domainLabel,
    evidenceLabel,
    evidenceScoreFromRank,
    escapeHtml,
    fetchJson,
    knowledgeRank,
    knowledgeLabel,
    labelize,
    loadBundle,
    loadPlantDetail,
    loadUseDetail,
    mediaKindClass,
    mediaKindLabel,
    monthMatches,
    normalizeBooleanish,
    partCategoryLabel,
    rankThreshold,
    monthLabel,
    renderMeta,
    renderPhotoBlock,
    seasonalWindowPayload,
    siteUrl,
    subdomainCategoryLabel,
  };
})();
