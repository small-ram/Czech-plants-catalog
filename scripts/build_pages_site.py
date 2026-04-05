from __future__ import annotations

import json
import shutil
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
SITE_SRC_DIR = PROJECT_DIR / "site_src"
APP_STATIC_DIR = PROJECT_DIR / "app" / "static"
APP_MEDIA_DIR = PROJECT_DIR / "app" / "media"
DOCS_DIR = PROJECT_DIR / "docs"

sys.path.insert(0, str(PROJECT_DIR))

from app.catalog_server import render_plant_markdown, render_use_markdown  # noqa: E402


MONTH_LABELS = [
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
]


def choose_db_path(project_dir: Path) -> Path:
    candidates = list(project_dir.glob("exports/*/v7_canonical/v7_dataset.sqlite"))
    candidates.extend(project_dir.glob("exports/*/v7_canonical/v7_dataset.rebuild*.sqlite"))
    existing = [path for path in candidates if path.exists()]
    if not existing:
        raise FileNotFoundError("No SQLite database found. Run build_v7_sqlite.py first.")
    return max(existing, key=lambda path: path.stat().st_mtime)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def infer_media_kind(entry: dict[str, object]) -> str:
    explicit = str(entry.get("media_kind", "")).strip().lower()
    if explicit:
        return explicit

    src = str(entry.get("src", "")).strip().lower()
    caption = str(entry.get("caption", "")).strip().lower()
    credit = str(entry.get("credit", "")).strip().lower()
    combined = " ".join([src, caption, credit])
    if src.endswith("_auto_cover.svg") or "auto-cover" in combined or "auto cover" in combined:
        return "auto_cover"
    if src.endswith(".svg") or "ilustrativ" in combined:
        return "illustration"
    return "photo"


def load_public_photos(docs_dir: Path) -> dict[str, list[dict[str, str]]]:
    manifest_path = APP_MEDIA_DIR / "plant_media.json"
    if not manifest_path.exists():
        return {}

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    public_manifest: dict[str, list[dict[str, str]]] = {}

    for plant_id, entries in manifest.items():
        if not isinstance(entries, list):
            continue

        photos: list[dict[str, str]] = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            if infer_media_kind(entry) != "photo":
                continue

            src = str(entry.get("src", "")).strip()
            if not src:
                continue

            public_src = src
            if not src.startswith(("http://", "https://")):
                source_path = APP_MEDIA_DIR / Path(src)
                if not source_path.exists():
                    continue
                relative_path = Path("media") / Path(src)
                destination = docs_dir / relative_path
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, destination)
                public_src = relative_path.as_posix()

            photos.append(
                {
                    "src": public_src,
                    "alt": str(entry.get("alt", "")).strip(),
                    "caption": str(entry.get("caption", "")).strip(),
                    "credit": str(entry.get("credit", "")).strip(),
                    "source_name": str(entry.get("source_name", "")).strip(),
                    "source_url": str(entry.get("source_url", "")).strip(),
                    "license": str(entry.get("license", "")).strip(),
                    "media_kind": "photo",
                    "media_kind_label": "Foto",
                }
            )

        public_manifest[plant_id] = photos

    return public_manifest


def attach_photo_metadata(row: dict[str, object], media_by_plant: dict[str, list[dict[str, str]]]) -> None:
    plant_id = str(row.get("plant_id") or "").strip()
    photos = list(media_by_plant.get(plant_id, []))
    primary = photos[0] if photos else None
    row["photos"] = photos
    row["primary_photo"] = primary.get("src") if primary else None
    row["primary_photo_alt"] = primary.get("alt") if primary else None
    row["primary_photo_credit"] = primary.get("credit") if primary else None
    row["primary_photo_source_name"] = primary.get("source_name") if primary else None
    row["primary_photo_source_url"] = primary.get("source_url") if primary else None
    row["primary_photo_kind"] = primary.get("media_kind") if primary else None
    row["primary_photo_kind_label"] = primary.get("media_kind_label") if primary else None


def build_data(db_path: Path, docs_dir: Path) -> dict[str, object]:
    media_by_plant = load_public_photos(docs_dir)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        plants_rows = [dict(row) for row in conn.execute("SELECT * FROM plants ORDER BY cesky_nazev_hlavni ASC").fetchall()]
        uses_rows = [
            dict(row)
            for row in conn.execute(
                """
                SELECT
                    u.*,
                    p.vedecky_nazev_hlavni,
                    p.cesky_nazev_hlavni,
                    p.plant_id,
                    p.status_v_cr_text,
                    p.status_cetnost_reprezentativni,
                    p.pocet_ceskych_aliasu,
                    d.forma_uchovani_text,
                    d.orientacni_trvanlivost_text,
                    d.poznamka_k_skladovani,
                    d.proc_je_v_jadru
                FROM uses u
                JOIN plants p ON p.plant_id = u.plant_id
                LEFT JOIN durable_forms d ON d.use_id = u.use_id
                ORDER BY
                    u.je_v_jadru_bezne_1m_plus DESC,
                    u.je_trvanlive_1m_plus DESC,
                    u.processing_methods_count DESC,
                    u.dukaznost_rank DESC,
                    p.cesky_nazev_hlavni ASC,
                    u.poddomena_text ASC
                """
            ).fetchall()
        ]
        aliases_rows = [
            dict(row)
            for row in conn.execute(
                """
                SELECT plant_id, alias, jazyk, typ_aliasu, je_preferovany, pocet_vyskytu
                FROM plant_aliases
                ORDER BY plant_id, jazyk, je_preferovany DESC, alias ASC
                """
            ).fetchall()
        ]
        processing_rows = [
            dict(row)
            for row in conn.execute(
                """
                SELECT
                    upm.use_id,
                    upm.processing_method_id,
                    vpm.label,
                    vpm.group_label,
                    upm.method_order
                FROM use_processing_methods upm
                JOIN vocab_processing_methods vpm ON vpm.processing_method_id = upm.processing_method_id
                ORDER BY upm.use_id ASC, upm.method_order ASC, vpm.display_order ASC, vpm.label ASC
                """
            ).fetchall()
        ]
        processing_vocab = [
            dict(row)
            for row in conn.execute(
                """
                SELECT processing_method_id, label
                FROM vocab_processing_methods
                ORDER BY display_order ASC, label ASC
                """
            ).fetchall()
        ]
        use_source_rows = [
            dict(row)
            for row in conn.execute(
                """
                SELECT
                    us.use_id,
                    us.role_zdroje,
                    us.poradi,
                    s.raw_source_id,
                    s.nazev,
                    s.url,
                    s.source_family,
                    s.poznamka
                FROM use_sources us
                JOIN sources s ON s.source_id = us.source_id
                ORDER BY us.use_id ASC, us.poradi ASC, s.raw_source_id ASC
                """
            ).fetchall()
        ]
        durable_forms_count = int(conn.execute("SELECT COUNT(*) FROM durable_forms").fetchone()[0])
    finally:
        conn.close()

    aliases_by_plant: dict[str, list[dict[str, object]]] = defaultdict(list)
    alias_text_by_plant: dict[str, str] = {}
    for row in aliases_rows:
        aliases_by_plant[str(row["plant_id"])].append(row)
    for plant_id, items in aliases_by_plant.items():
        alias_text_by_plant[plant_id] = " ".join(str(item["alias"]) for item in items).lower()

    processing_by_use: dict[str, list[dict[str, object]]] = defaultdict(list)
    processing_ids_by_use: dict[str, list[str]] = defaultdict(list)
    for row in processing_rows:
        use_id = str(row["use_id"])
        payload = {
            "processing_method_id": row["processing_method_id"],
            "label": row["label"],
            "group_label": row["group_label"],
            "method_order": row["method_order"],
        }
        processing_by_use[use_id].append(payload)
        processing_ids_by_use[use_id].append(str(row["processing_method_id"]))

    sources_by_use: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in use_source_rows:
        use_id = str(row["use_id"])
        sources_by_use[use_id].append(
            {
                "role_zdroje": row["role_zdroje"],
                "poradi": row["poradi"],
                "raw_source_id": row["raw_source_id"],
                "nazev": row["nazev"],
                "url": row["url"],
                "source_family": row["source_family"],
                "poznamka": row["poznamka"],
            }
        )

    use_details: dict[str, dict[str, object]] = {}
    use_index: list[dict[str, object]] = []
    uses_by_plant: dict[str, list[dict[str, object]]] = defaultdict(list)

    for row in uses_rows:
        plant_id = str(row["plant_id"])
        use_id = str(row["use_id"])
        aliases = aliases_by_plant.get(plant_id, [])
        processing_methods = processing_by_use.get(use_id, [])

        detail = dict(row)
        detail["aliases"] = aliases
        detail["sources"] = sources_by_use.get(use_id, [])
        detail["processing_methods"] = processing_methods
        if not detail.get("processing_methods_text") and processing_methods:
            detail["processing_methods_text"] = " · ".join(str(item["label"]) for item in processing_methods)
        attach_photo_metadata(detail, media_by_plant)
        use_details[use_id] = detail

        index_row = {
            "use_id": use_id,
            "raw_record_id": detail["raw_record_id"],
            "plant_id": plant_id,
            "cesky_nazev_hlavni": detail["cesky_nazev_hlavni"],
            "vedecky_nazev_hlavni": detail["vedecky_nazev_hlavni"],
            "cesky_nazev_display": detail.get("cesky_nazev_display"),
            "domena": detail.get("domena"),
            "poddomena_text": detail.get("poddomena_text"),
            "poddomena_kategorie": detail.get("poddomena_kategorie"),
            "cast_rostliny_text": detail.get("cast_rostliny_text"),
            "cast_rostliny_kategorie": detail.get("cast_rostliny_kategorie"),
            "typicke_lokality_text": detail.get("typicke_lokality_text"),
            "obdobi_ziskani_text": detail.get("obdobi_ziskani_text"),
            "mesic_od": detail.get("mesic_od"),
            "mesic_do": detail.get("mesic_do"),
            "cilovy_efekt": detail.get("cilovy_efekt"),
            "sber_doporuceni": detail.get("sber_doporuceni"),
            "hlavni_rizika": detail.get("hlavni_rizika"),
            "legalita_poznamka_cr": detail.get("legalita_poznamka_cr"),
            "dukaznost_skore": detail.get("dukaznost_skore"),
            "dukaznost_rank": detail.get("dukaznost_rank"),
            "status_znalosti": detail.get("status_znalosti"),
            "aplikovatelnost_v_cr": detail.get("aplikovatelnost_v_cr"),
            "je_trvanlive_1m_plus": detail.get("je_trvanlive_1m_plus"),
            "je_v_jadru_bezne_1m_plus": detail.get("je_v_jadru_bezne_1m_plus"),
            "processing_methods_text": detail.get("processing_methods_text"),
            "processing_methods_count": detail.get("processing_methods_count"),
            "processing_method_ids": processing_ids_by_use.get(use_id, []),
            "forma_uchovani_text": detail.get("forma_uchovani_text"),
            "orientacni_trvanlivost_text": detail.get("orientacni_trvanlivost_text"),
            "proc_je_v_jadru": detail.get("proc_je_v_jadru"),
            "status_v_cr_text": detail.get("status_v_cr_text"),
            "status_cetnost_reprezentativni": detail.get("status_cetnost_reprezentativni"),
            "pocet_ceskych_aliasu": detail.get("pocet_ceskych_aliasu"),
        }
        attach_photo_metadata(index_row, media_by_plant)
        index_row["search_text"] = " ".join(
            str(value).strip().lower()
            for value in [
                detail.get("cesky_nazev_hlavni"),
                detail.get("vedecky_nazev_hlavni"),
                detail.get("cesky_nazev_display"),
                alias_text_by_plant.get(plant_id, ""),
                detail.get("domena"),
                detail.get("poddomena_text"),
                detail.get("cast_rostliny_text"),
                detail.get("cilovy_efekt"),
                detail.get("processing_methods_text"),
            ]
            if value
        )
        use_index.append(index_row)
        uses_by_plant[plant_id].append(detail)

    plant_details: dict[str, dict[str, object]] = {}
    plant_index: list[dict[str, object]] = []

    for plant in plants_rows:
        plant_id = str(plant["plant_id"])
        uses = uses_by_plant.get(plant_id, [])
        source_counter: dict[str, dict[str, object]] = {}
        for use in uses:
            for source in use.get("sources", []):
                raw_source_id = str(source["raw_source_id"])
                if raw_source_id not in source_counter:
                    source_counter[raw_source_id] = {
                        "raw_source_id": source["raw_source_id"],
                        "nazev": source["nazev"],
                        "url": source["url"],
                        "source_family": source["source_family"],
                        "use_count": 0,
                    }
                source_counter[raw_source_id]["use_count"] += 1

        sorted_sources = sorted(
            source_counter.values(),
            key=lambda item: (-int(item["use_count"]), str(item["raw_source_id"])),
        )

        payload = dict(plant)
        payload["aliases"] = aliases_by_plant.get(plant_id, [])
        payload["uses"] = [
            {
                "use_id": use["use_id"],
                "raw_record_id": use["raw_record_id"],
                "domena": use["domena"],
                "poddomena_text": use["poddomena_text"],
                "poddomena_kategorie": use["poddomena_kategorie"],
                "cast_rostliny_text": use["cast_rostliny_text"],
                "cast_rostliny_kategorie": use["cast_rostliny_kategorie"],
                "obdobi_ziskani_text": use["obdobi_ziskani_text"],
                "cilovy_efekt": use["cilovy_efekt"],
                "dukaznost_skore": use["dukaznost_skore"],
                "dukaznost_rank": use["dukaznost_rank"],
                "status_znalosti": use["status_znalosti"],
                "aplikovatelnost_v_cr": use["aplikovatelnost_v_cr"],
                "je_trvanlive_1m_plus": use["je_trvanlive_1m_plus"],
                "je_v_jadru_bezne_1m_plus": use["je_v_jadru_bezne_1m_plus"],
                "processing_methods_text": use["processing_methods_text"],
                "processing_methods_count": use["processing_methods_count"],
                "sber_doporuceni": use["sber_doporuceni"],
                "forma_uchovani_text": use["forma_uchovani_text"],
                "orientacni_trvanlivost_text": use["orientacni_trvanlivost_text"],
            }
            for use in uses
        ]
        payload["sources"] = sorted_sources
        payload["photos"] = list(media_by_plant.get(plant_id, []))
        payload["stats"] = {
            "use_count": len(uses),
            "durable_use_count": sum(1 for use in uses if use.get("je_trvanlive_1m_plus")),
            "core_use_count": sum(1 for use in uses if use.get("je_v_jadru_bezne_1m_plus")),
            "processing_use_count": sum(1 for use in uses if int(use.get("processing_methods_count") or 0) > 0),
            "top_evidence_rank": max((int(use.get("dukaznost_rank") or 0) for use in uses), default=0),
        }
        plant_details[plant_id] = payload

        index_row = {
            "plant_id": plant_id,
            "cesky_nazev_hlavni": plant["cesky_nazev_hlavni"],
            "vedecky_nazev_hlavni": plant["vedecky_nazev_hlavni"],
            "status_v_cr_text": plant.get("status_v_cr_text"),
            "status_cetnost_reprezentativni": plant.get("status_cetnost_reprezentativni"),
            "pocet_pouziti": plant.get("pocet_pouziti"),
            "pocet_ceskych_aliasu": plant.get("pocet_ceskych_aliasu"),
            "use_count": payload["stats"]["use_count"],
            "durable_use_count": payload["stats"]["durable_use_count"],
            "core_use_count": payload["stats"]["core_use_count"],
            "processing_use_count": payload["stats"]["processing_use_count"],
            "top_evidence_rank": payload["stats"]["top_evidence_rank"],
        }
        attach_photo_metadata(index_row, media_by_plant)
        index_row["search_text"] = " ".join(
            str(value).strip().lower()
            for value in [
                plant.get("cesky_nazev_hlavni"),
                plant.get("vedecky_nazev_hlavni"),
                alias_text_by_plant.get(plant_id, ""),
                plant.get("status_v_cr_text"),
            ]
            if value
        )
        plant_index.append(index_row)

    plant_index.sort(
        key=lambda item: (
            -int(item.get("core_use_count") or 0),
            -int(item.get("durable_use_count") or 0),
            -int(item.get("processing_use_count") or 0),
            -int(item.get("top_evidence_rank") or 0),
            str(item.get("cesky_nazev_hlavni") or ""),
        )
    )

    summary = {
        "counts": {
            "plants": len(plant_index),
            "uses": len(use_index),
            "durable_forms": durable_forms_count,
            "core_items": sum(1 for item in use_index if item.get("je_v_jadru_bezne_1m_plus")),
        }
    }
    options = {
        "domains": sorted({str(item["domena"]) for item in use_index if item.get("domena")}),
        "part_categories": sorted(
            {str(item["cast_rostliny_kategorie"]) for item in use_index if item.get("cast_rostliny_kategorie")}
        ),
        "subdomain_categories": sorted(
            {str(item["poddomena_kategorie"]) for item in use_index if item.get("poddomena_kategorie")}
        ),
        "processing_methods": [
            {"value": str(item["processing_method_id"]), "label": str(item["label"])} for item in processing_vocab
        ],
        "evidence_scores": [
            score
            for score in ["A", "B", "C", "D", "E"]
            if any(str(item.get("dukaznost_skore")) == score for item in use_index)
        ],
        "months": [{"value": index, "label": label} for index, label in enumerate(MONTH_LABELS) if index],
    }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "database_path": str(db_path),
        "summary": summary,
        "options": options,
        "uses": use_index,
        "plants": plant_index,
        "use_details": use_details,
        "plant_details": plant_details,
    }


def root_index_html() -> str:
    return """<!doctype html>
<html lang="cs">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>České rostliny katalog</title>
    <link rel="stylesheet" href="./static/styles.css" />
  </head>
  <body>
    <div class="page-shell">
      <header class="hero">
        <div class="hero-copy">
          <p class="eyebrow">Veřejný katalog nad statickými daty</p>
          <h1>České rostliny jako praktický katalog</h1>
          <p class="hero-text">
            Hledání v kurátorovaném datasetu použití, zpracování, sběru, rizik a zdrojů.
          </p>
          <div class="hero-actions">
            <a class="detail-btn" href="./plants/">Galerie rostlin</a>
          </div>
        </div>
        <div class="hero-stats" id="summary-stats"></div>
      </header>

      <main class="layout">
        <section class="filters-panel">
          <div class="filters-header">
            <h2>Filtry</h2>
            <button id="reset-btn" class="ghost-btn" type="button">Reset</button>
          </div>

          <label class="field">
            <span>Hledat</span>
            <input id="q" type="search" placeholder="např. sirup, lípa, sušení, žalud..." />
          </label>

          <label class="field">
            <span>Min. důkaznost</span>
            <select id="evidence_min">
              <option value="">Bez limitu</option>
            </select>
          </label>

          <section class="field">
            <span>Typ použití</span>
            <div id="domain-groups" class="multi-filter"></div>
          </section>

          <section class="field">
            <span>Jak rozšířené</span>
            <div id="knowledge-status-groups" class="multi-filter"></div>
          </section>

          <section class="field">
            <span>Sbíraná část</span>
            <div id="part-category-groups" class="multi-filter multi-filter-compact"></div>
          </section>

          <section class="field">
            <span>Způsob použití</span>
            <div id="subdomain-category-groups" class="multi-filter multi-filter-compact"></div>
          </section>

          <section class="field">
            <span>Dlouhodobé zpracování</span>
            <div id="processing-method-groups" class="multi-filter multi-filter-compact"></div>
          </section>

          <label class="field">
            <span>Měsíc sběru</span>
            <select id="month">
              <option value="">Libovolný</option>
            </select>
          </label>

          <p id="seasonal-note" class="context-note"></p>

          <label class="field">
            <span>Limit</span>
            <select id="limit">
              <option value="24">24</option>
              <option value="60" selected>60</option>
              <option value="120">120</option>
              <option value="200">200</option>
            </select>
          </label>

          <div class="checks">
            <label class="check check-highlight">
              <input id="seasonal" type="checkbox" />
              <span>Výchozí sezónní okno kolem dneška</span>
            </label>
            <label class="check">
              <input id="trvanlive" type="checkbox" />
              <span>Jen trvanlivé položky</span>
            </label>
            <label class="check">
              <input id="jadro" type="checkbox" />
              <span>Jen doporučený výběr</span>
            </label>
          </div>
        </section>

        <section class="results-panel">
          <div class="results-toolbar">
            <div>
              <p class="eyebrow">Výsledky</p>
              <h2 id="results-title">Načítání</h2>
            </div>
            <p class="toolbar-note">
              Otevři detail použití nebo celé rostliny na samostatné stránce.
            </p>
          </div>

          <div id="results" class="results-grid"></div>
        </section>
      </main>
    </div>

    <template id="result-card-template">
      <article class="result-card">
        <div class="card-topline"></div>
        <div class="result-card-media">
          <img class="result-card-image" alt="" loading="lazy" hidden />
          <div class="result-card-placeholder">
            <div class="result-card-placeholder-inner">
              <strong>Bez fotky</strong>
              <span>Primární fotka rostliny zatím není přiřazená.</span>
            </div>
          </div>
        </div>
        <div class="card-body">
          <div class="card-head">
            <div>
              <p class="card-id"></p>
              <h3 class="card-title"></h3>
              <p class="card-subtitle"></p>
            </div>
            <div class="card-badges"></div>
          </div>
          <div class="meta-grid"></div>
          <p class="card-effect"></p>
          <div class="card-actions">
            <a class="detail-btn" href="./">Použití</a>
            <a class="plant-btn" href="./">Rostlina</a>
          </div>
        </div>
      </article>
    </template>

    <script>window.CATALOG_BASE = ".";</script>
    <script src="./static/site-common.js" defer></script>
    <script src="./static/site-index.js" defer></script>
  </body>
</html>
"""


def plants_index_html() -> str:
    return """<!doctype html>
<html lang="cs">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Galerie rostlin</title>
    <link rel="stylesheet" href="../static/styles.css" />
  </head>
  <body>
    <div class="page-shell">
      <header class="hero">
        <div class="hero-copy">
          <p class="eyebrow">Rostliny</p>
          <h1>Galerie rostlin</h1>
          <p class="hero-text">
            Rychlé procházení profilů rostlin, jejich četnosti použití, trvanlivosti a síly opory.
          </p>
          <div class="hero-actions">
            <a class="detail-btn" href="../">Katalog použití</a>
          </div>
        </div>
        <div class="hero-stats" id="plants-summary-stats"></div>
      </header>

      <main class="layout">
        <section class="filters-panel">
          <div class="filters-header">
            <h2>Filtry</h2>
            <button id="plants-reset-btn" class="ghost-btn" type="button">Reset</button>
          </div>

          <label class="field">
            <span>Hledat rostlinu</span>
            <input id="plants-q" type="search" placeholder="např. bez, lípa, pampeliška, sambucus..." />
          </label>

          <label class="field">
            <span>Limit</span>
            <select id="plants-limit">
              <option value="24">24</option>
              <option value="48" selected>48</option>
              <option value="96">96</option>
              <option value="180">180</option>
            </select>
          </label>

          <section class="field">
            <span>Jak rozšířené</span>
            <div id="plants-knowledge-status-groups" class="multi-filter"></div>
          </section>

          <p id="plants-seasonal-note" class="context-note"></p>

          <div class="checks">
            <label class="check check-highlight">
              <input id="plants-seasonal" type="checkbox" />
              <span>Jen rostliny relevantní kolem dneška</span>
            </label>
            <label class="check">
              <input id="plants-trvanlive" type="checkbox" />
              <span>Jen rostliny s trvanlivým použitím</span>
            </label>
            <label class="check">
              <input id="plants-jadro" type="checkbox" />
              <span>Jen rostliny s položkou v doporučeném výběru</span>
            </label>
          </div>
        </section>

        <section class="results-panel">
          <div class="results-toolbar">
            <div>
              <p class="eyebrow">Galerie</p>
              <h2 id="plants-results-title">Načítání</h2>
            </div>
            <p class="toolbar-note">
              Otevři profil rostliny pro souhrn použití, zdrojů, aliasů a exportů.
            </p>
          </div>

          <div id="plants-results" class="plants-grid"></div>
        </section>
      </main>
    </div>

    <template id="plant-card-template">
      <article class="plant-card">
        <div class="plant-card-media">
          <img class="plant-card-image" alt="" loading="lazy" hidden />
          <div class="plant-card-placeholder">
            <div class="plant-card-placeholder-inner">
              <strong>Bez fotky</strong>
              <span>Primární fotografie zatím chybí.</span>
            </div>
          </div>
        </div>

        <div class="plant-card-body">
          <div class="card-head">
            <div>
              <p class="card-id">Profil rostliny</p>
              <h3 class="card-title"></h3>
              <p class="card-subtitle"></p>
            </div>
            <div class="card-badges"></div>
          </div>

          <div class="meta-grid"></div>
          <p class="plant-card-status"></p>

          <div class="plant-stat-grid">
            <div class="plant-stat">
              <strong class="plant-stat-value plant-use-count"></strong>
              <span>použití</span>
            </div>
            <div class="plant-stat">
              <strong class="plant-stat-value plant-durable-count"></strong>
              <span>trvanlivých</span>
            </div>
            <div class="plant-stat">
              <strong class="plant-stat-value plant-core-count"></strong>
              <span>ve výběru</span>
            </div>
          </div>

          <div class="card-actions">
            <a class="detail-btn plant-profile-link" href="../">Profil rostliny</a>
            <a class="plant-btn plant-export-link" href="../">Markdown</a>
          </div>
        </div>
      </article>
    </template>

    <script>window.CATALOG_BASE = "..";</script>
    <script src="../static/site-common.js" defer></script>
    <script src="../static/site-plants.js" defer></script>
  </body>
</html>
"""


def detail_page_html(kind: str, item_id: str) -> str:
    config = json.dumps({"kind": kind, "id": item_id}, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="cs">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Detail</title>
    <link rel="stylesheet" href="../../static/styles.css" />
  </head>
  <body>
    <div class="page-shell">
      <main class="detail-page-shell">
        <header class="detail-page-header">
          <div class="detail-page-nav">
            <a class="back-link" href="../../">Katalog použití</a>
            <a class="back-link secondary-link" href="../../plants/">Galerie rostlin</a>
          </div>
          <div class="detail-page-hero">
            <div>
              <p id="detail-page-eyebrow" class="eyebrow">Načítání</p>
              <h1 id="detail-page-title">Načítání detailu</h1>
              <p id="detail-page-subtitle" class="hero-text"></p>
            </div>
            <div id="detail-page-actions" class="hero-actions"></div>
          </div>
          <div id="detail-page-summary" class="hero-stats"></div>
          <div id="detail-page-meta" class="detail-meta-strip"></div>
        </header>

        <div id="detail-page-content" class="detail-page-content">
          <div class="empty-state">Načítání dat…</div>
        </div>
      </main>
    </div>

    <script>window.CATALOG_BASE = "../.."; window.CATALOG_DETAIL = {config};</script>
    <script src="../../static/site-common.js" defer></script>
    <script src="../../static/site-detail.js" defer></script>
  </body>
</html>
"""


def not_found_html() -> str:
    return """<!doctype html>
<html lang="cs">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Přesměrování</title>
    <script>
      (function () {
        const parts = window.location.pathname.split("/").filter(Boolean);
        const knownRoots = new Set(["plant", "use", "plants", "static", "data", "export"]);
        const repoBase = parts.length && !knownRoots.has(parts[0]) ? `/${parts[0]}` : "";
        const route = repoBase ? parts.slice(1) : parts;

        if (route[0] === "plant" && route[1]) {
          window.location.replace(`${repoBase}/plant/${encodeURIComponent(decodeURIComponent(route[1]))}/`);
          return;
        }
        if (route[0] === "use" && route[1]) {
          window.location.replace(`${repoBase}/use/${encodeURIComponent(decodeURIComponent(route[1]))}/`);
          return;
        }
        if (route[0] === "plants") {
          window.location.replace(`${repoBase}/plants/`);
          return;
        }
        window.location.replace(`${repoBase || ""}/`);
      })();
    </script>
  </head>
  <body></body>
</html>
"""


def write_pages(data: dict[str, object]) -> None:
    write_text(DOCS_DIR / "index.html", root_index_html())
    write_text(DOCS_DIR / "plants" / "index.html", plants_index_html())
    write_text(DOCS_DIR / "404.html", not_found_html())
    write_text(DOCS_DIR / ".nojekyll", "")

    for plant_id in data["plant_details"].keys():
        write_text(DOCS_DIR / "plant" / plant_id / "index.html", detail_page_html("plant", plant_id))
    for use_id in data["use_details"].keys():
        write_text(DOCS_DIR / "use" / use_id / "index.html", detail_page_html("use", use_id))


def write_exports(data: dict[str, object]) -> None:
    for plant_id, detail in data["plant_details"].items():
        write_text(DOCS_DIR / "data" / "plant" / f"{plant_id}.json", json.dumps(detail, ensure_ascii=False, indent=2))
        write_text(DOCS_DIR / "export" / "plant" / f"{plant_id}.json", json.dumps(detail, ensure_ascii=False, indent=2))
        write_text(DOCS_DIR / "export" / "plant" / f"{plant_id}.md", render_plant_markdown(detail))

    for use_id, detail in data["use_details"].items():
        write_text(DOCS_DIR / "data" / "use" / f"{use_id}.json", json.dumps(detail, ensure_ascii=False, indent=2))
        write_text(DOCS_DIR / "export" / "use" / f"{use_id}.json", json.dumps(detail, ensure_ascii=False, indent=2))
        write_text(DOCS_DIR / "export" / "use" / f"{use_id}.md", render_use_markdown(detail))


def copy_static_assets() -> None:
    static_target = DOCS_DIR / "static"
    static_target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(APP_STATIC_DIR / "styles.css", static_target / "styles.css")
    for source_path in (SITE_SRC_DIR / "static").glob("*.js"):
        shutil.copy2(source_path, static_target / source_path.name)


def write_bundle(data: dict[str, object]) -> None:
    bundle = {
        "generated_at": data["generated_at"],
        "database_path": data["database_path"],
        "summary": data["summary"],
        "options": data["options"],
        "uses": data["uses"],
        "plants": data["plants"],
    }
    write_text(DOCS_DIR / "data" / "catalog_bundle.json", json.dumps(bundle, ensure_ascii=False, indent=2))


def main() -> None:
    db_path = choose_db_path(PROJECT_DIR)

    if DOCS_DIR.exists():
        shutil.rmtree(DOCS_DIR)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    data = build_data(db_path, DOCS_DIR)
    copy_static_assets()
    write_bundle(data)
    write_exports(data)
    write_pages(data)

    print(f"GitHub Pages site written to: {DOCS_DIR}")
    print(f"Using database: {db_path}")
    print(f"Plants: {data['summary']['counts']['plants']}")
    print(f"Uses: {data['summary']['counts']['uses']}")


if __name__ == "__main__":
    main()
