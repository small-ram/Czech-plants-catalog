from __future__ import annotations

import argparse
import html
import json
import re
import sqlite3
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "exports" / "cz_rostliny_rozsireny_dataset_v6_jadro_bezne_trvanlive" / "v7_canonical" / "v7_dataset.sqlite"
MANIFEST_PATH = ROOT / "app" / "media" / "plant_media.json"
REPORT_PATH = ROOT / "MEDIA_WIKIMEDIA_FILL_REPORT.md"

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
USER_AGENT = "ceske-rostliny-wikimedia-fill/1.0 (local dataset maintenance)"

NON_PHOTO_HINTS = (
    "illustration",
    "drawing",
    "paint",
    "painting",
    "lindman",
    "koeh",
    "flora von deutschland",
    "nordens flora",
    "plate",
    "herbarium",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fill missing plant photos from Wikimedia sources.")
    parser.add_argument("--all", action="store_true", help="Refresh all plants, not just those missing a photo.")
    parser.add_argument("--limit", type=int, default=0, help="Optional limit of processed plants.")
    parser.add_argument("--sleep-ms", type=int, default=80, help="Delay between network requests.")
    return parser.parse_args()


def fetch_json(base_url: str, params: dict[str, Any]) -> dict[str, Any]:
    url = f"{base_url}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def strip_html(value: str | None) -> str:
    if not value:
        return ""
    text = html.unescape(value)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def load_manifest() -> dict[str, list[dict[str, Any]]]:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {}


def save_manifest(manifest: dict[str, list[dict[str, Any]]]) -> None:
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def has_photo(entries: list[dict[str, Any]]) -> bool:
    return any(isinstance(entry, dict) and entry.get("media_kind") == "photo" for entry in entries)


def canonical_taxon(name: str) -> str:
    name = re.sub(r"\s+", " ", name.strip())
    if not name:
        return ""
    if "spp." in name or "agg." in name:
        return name.split()[0]

    parts = name.split()
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]

    cleaned = [parts[0]]
    if re.fullmatch(r"[a-zx×-]+\.?", parts[1]):
        cleaned.append(parts[1].rstrip("."))
    else:
        return parts[0]

    if len(parts) >= 4 and parts[2] in {"subsp.", "var."} and re.fullmatch(r"[a-z-]+", parts[3]):
        cleaned.extend([parts[2], parts[3]])
    return " ".join(cleaned)


def candidate_titles(scientific_name: str) -> list[str]:
    candidates: list[str] = []

    def add(value: str) -> None:
        value = value.strip()
        if value and value not in candidates:
            candidates.append(value)

    add(scientific_name)
    add(canonical_taxon(scientific_name))

    for piece in re.split(r"\s*/\s*", scientific_name):
        cleaned = canonical_taxon(piece)
        add(cleaned)
        if cleaned:
            add(" ".join(cleaned.split()[:2]))
            add(cleaned.split()[0])
    return candidates


def wikipedia_search_titles(query: str) -> list[str]:
    payload = fetch_json(
        WIKIPEDIA_API,
        {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": "5",
            "format": "json",
        },
    )
    search_rows = payload.get("query", {}).get("search", [])
    return [row["title"] for row in search_rows if row.get("title")]


def wikipedia_page_props(title: str) -> tuple[str | None, str | None]:
    payload = fetch_json(
        WIKIPEDIA_API,
        {
            "action": "query",
            "titles": title,
            "redirects": "1",
            "prop": "pageprops",
            "ppprop": "page_image_free|wikibase_item",
            "format": "json",
        },
    )
    pages = payload.get("query", {}).get("pages", {})
    for page in pages.values():
        if "missing" in page:
            continue
        pageprops = page.get("pageprops", {})
        return pageprops.get("page_image_free"), pageprops.get("wikibase_item")
    return None, None


def wikidata_search_ids(query: str) -> list[str]:
    payload = fetch_json(
        WIKIDATA_API,
        {
            "action": "wbsearchentities",
            "search": query,
            "language": "en",
            "limit": "5",
            "format": "json",
        },
    )
    return [row["id"] for row in payload.get("search", []) if row.get("id")]


def wikidata_image_filenames(item_id: str) -> list[str]:
    payload = fetch_json(
        WIKIDATA_API,
        {
            "action": "wbgetentities",
            "ids": item_id,
            "props": "claims",
            "format": "json",
        },
    )
    entity = payload.get("entities", {}).get(item_id, {})
    claims = entity.get("claims", {}).get("P18", [])
    filenames: list[str] = []
    for claim in claims:
        value = claim.get("mainsnak", {}).get("datavalue", {}).get("value")
        if isinstance(value, str) and value not in filenames:
            filenames.append(value)
    return filenames


def commons_file_info(filename: str) -> dict[str, Any] | None:
    payload = fetch_json(
        COMMONS_API,
        {
            "action": "query",
            "titles": f"File:{filename}",
            "prop": "imageinfo",
            "iiprop": "url|extmetadata",
            "format": "json",
        },
    )
    pages = payload.get("query", {}).get("pages", {})
    for page in pages.values():
        if "missing" in page:
            continue
        imageinfo = page.get("imageinfo") or []
        if not imageinfo:
            continue
        info = imageinfo[0]
        return {
            "title": page.get("title", f"File:{filename}"),
            "url": info.get("url"),
            "descriptionurl": info.get("descriptionurl"),
            "extmetadata": info.get("extmetadata") or {},
        }
    return None


def commons_search_files(query: str) -> list[str]:
    payload = fetch_json(
        COMMONS_API,
        {
            "action": "query",
            "generator": "search",
            "gsrsearch": f"\"{query}\"",
            "gsrnamespace": "6",
            "gsrlimit": "6",
            "prop": "info",
            "format": "json",
        },
    )
    pages = payload.get("query", {}).get("pages", {})
    titles = [page.get("title", "") for page in pages.values()]
    titles = [title.removeprefix("File:") for title in titles if title.startswith("File:")]
    return sorted(set(titles))


def commons_gallery_images(title: str) -> list[str]:
    payload = fetch_json(
        COMMONS_API,
        {
            "action": "query",
            "titles": title,
            "prop": "images",
            "imlimit": "20",
            "format": "json",
        },
    )
    pages = payload.get("query", {}).get("pages", {})
    filenames: list[str] = []
    for page in pages.values():
        if "missing" in page:
            continue
        for image in page.get("images", []):
            title = image.get("title", "")
            if title.startswith("File:"):
                filename = title.removeprefix("File:")
                if filename not in filenames:
                    filenames.append(filename)
    return filenames


def is_probably_photo(filename: str, file_info: dict[str, Any]) -> bool:
    lowered_name = filename.lower()
    if lowered_name.endswith(".svg"):
        return False

    meta = file_info.get("extmetadata", {})
    combined = " ".join(
        strip_html(meta.get(key, {}).get("value"))
        for key in ("ImageDescription", "ObjectName", "Credit", "Artist")
    ).lower()
    if any(hint in lowered_name or hint in combined for hint in NON_PHOTO_HINTS):
        return False
    return True


def build_entry(filename: str, file_info: dict[str, Any], alt_label: str, scientific_name: str) -> dict[str, Any]:
    meta = file_info.get("extmetadata", {})
    artist = strip_html(meta.get("Artist", {}).get("value"))
    credit = strip_html(meta.get("Credit", {}).get("value"))
    license_name = strip_html(meta.get("LicenseShortName", {}).get("value"))
    if not artist:
        artist = credit or "Wikimedia contributor"
    source_url = file_info.get("descriptionurl") or f"https://commons.wikimedia.org/wiki/File:{quote(filename.replace(' ', '_'))}"
    return {
        "src": f"https://commons.wikimedia.org/wiki/Special:FilePath/{quote(filename)}",
        "alt": alt_label,
        "caption": f"Wikimedia Commons: {scientific_name}",
        "credit": artist,
        "media_kind": "photo",
        "source_name": "Wikimedia Commons",
        "source_url": source_url,
        "license": license_name,
    }


def find_photo_for_plant(scientific_name: str) -> dict[str, Any] | None:
    seen_titles: set[str] = set()
    seen_items: set[str] = set()
    for candidate in candidate_titles(scientific_name):
        title_candidates = [candidate, *wikipedia_search_titles(candidate)]
        for title in title_candidates:
            if title in seen_titles:
                continue
            seen_titles.add(title)
            filename, item_id = wikipedia_page_props(title)
            if filename:
                info = commons_file_info(filename)
                if info and is_probably_photo(filename, info):
                    return build_entry(filename, info, candidate, scientific_name)
            if item_id and item_id not in seen_items:
                seen_items.add(item_id)
                for item_filename in wikidata_image_filenames(item_id):
                    info = commons_file_info(item_filename)
                    if info and is_probably_photo(item_filename, info):
                        return build_entry(item_filename, info, candidate, scientific_name)

        for item_id in wikidata_search_ids(candidate):
            if item_id in seen_items:
                continue
            seen_items.add(item_id)
            for item_filename in wikidata_image_filenames(item_id):
                info = commons_file_info(item_filename)
                if info and is_probably_photo(item_filename, info):
                    return build_entry(item_filename, info, candidate, scientific_name)

        for filename in commons_gallery_images(candidate):
            info = commons_file_info(filename)
            if info and is_probably_photo(filename, info):
                return build_entry(filename, info, candidate, scientific_name)

        for filename in commons_search_files(candidate):
            info = commons_file_info(filename)
            if info and is_probably_photo(filename, info):
                return build_entry(filename, info, candidate, scientific_name)
    return None


def upsert_photo(manifest: dict[str, list[dict[str, Any]]], plant_id: str, entry: dict[str, Any]) -> None:
    entries = manifest.get(plant_id, [])
    if not isinstance(entries, list):
        entries = []
    remaining = [item for item in entries if not (isinstance(item, dict) and item.get("media_kind") == "photo")]
    manifest[plant_id] = [entry, *remaining]


def load_plants() -> list[dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "select plant_id, vedecky_nazev_hlavni, cesky_nazev_hlavni, pocet_pouziti from plants order by pocet_pouziti desc, cesky_nazev_hlavni"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def write_report(found: list[dict[str, str]], unresolved: list[dict[str, str]]) -> None:
    lines = [
        "# Media Wikimedia Fill Report",
        "",
        f"- doplněno foto pro `{len(found)}` rostlin",
        f"- bez nalezené fotky zůstalo `{len(unresolved)}` rostlin",
        "",
        "## Nově doplněné fotky",
        "",
    ]
    for row in found:
        lines.append(f"- `{row['plant_id']}` — `{row['scientific_name']}`")
    lines.extend(["", "## Bez doplnění", ""])
    for row in unresolved:
        lines.append(f"- `{row['plant_id']}` — `{row['scientific_name']}`")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    manifest = load_manifest()
    plants = load_plants()

    if not args.all:
        plants = [row for row in plants if not has_photo(manifest.get(row["plant_id"], []))]
    if args.limit > 0:
        plants = plants[: args.limit]

    found: list[dict[str, str]] = []
    unresolved: list[dict[str, str]] = []

    for row in plants:
        plant_id = row["plant_id"]
        scientific_name = row["vedecky_nazev_hlavni"]
        alt_label = row["cesky_nazev_hlavni"] or scientific_name
        try:
            entry = find_photo_for_plant(scientific_name)
        except Exception:
            entry = None
        if entry:
            entry["alt"] = alt_label
            upsert_photo(manifest, plant_id, entry)
            found.append({"plant_id": plant_id, "scientific_name": scientific_name})
        else:
            unresolved.append({"plant_id": plant_id, "scientific_name": scientific_name})
        time.sleep(max(args.sleep_ms, 0) / 1000)

    save_manifest(manifest)
    write_report(found, unresolved)
    print(f"Filled photos: {len(found)}")
    print(f"Unresolved: {len(unresolved)}")
    print(f"Report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
