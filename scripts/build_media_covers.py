from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from dataclasses import dataclass
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_MEDIA_DIR = ROOT / "app" / "media"
MANIFEST_PATH = APP_MEDIA_DIR / "plant_media.json"
DEFAULT_DB = (
    ROOT
    / "exports"
    / "cz_rostliny_rozsireny_dataset_v6_jadro_bezne_trvanlive"
    / "v7_canonical"
    / "v7_dataset.sqlite"
)

PALETTES = [
    ("#f6efdf", "#d9c5a1", "#5b6f47", "#1f2b1f"),
    ("#eef1d8", "#92b169", "#41633a", "#20301c"),
    ("#f5efcf", "#c8a93a", "#5d7b34", "#2a2b17"),
    ("#f7e6db", "#d48767", "#5b6f47", "#281713"),
    ("#f3ecd4", "#c3be79", "#61753a", "#1f2b1f"),
    ("#e9efe3", "#88a97a", "#48664f", "#1f2d24"),
]


@dataclass
class PlantRecord:
    plant_id: str
    cesky_nazev_hlavni: str
    vedecky_nazev_hlavni: str
    pocet_pouziti: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate local SVG covers for plants and update plant_media.json.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="Path to v7_dataset.sqlite")
    parser.add_argument("--limit", type=int, default=20, help="How many top plants to consider")
    parser.add_argument(
        "--missing-only",
        action="store_true",
        help="Generate covers only for plants that do not already have entries in plant_media.json",
    )
    parser.add_argument(
        "--overwrite-files",
        action="store_true",
        help="Overwrite existing generated SVG files if they already exist",
    )
    return parser.parse_args()


def load_manifest() -> dict[str, list[dict[str, str]]]:
    if not MANIFEST_PATH.exists():
        return {}
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def save_manifest(payload: dict[str, list[dict[str, str]]]) -> None:
    MANIFEST_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def infer_media_kind(entry: dict[str, str]) -> str:
    explicit = str(entry.get("media_kind", "")).strip().lower()
    if explicit in {"photo", "illustration", "auto_cover"}:
        return explicit

    src = str(entry.get("src", "")).strip().lower()
    caption = str(entry.get("caption", "")).strip().lower()
    credit = str(entry.get("credit", "")).strip().lower()
    alt = str(entry.get("alt", "")).strip().lower()
    combined = " ".join([src, caption, credit, alt])

    if src.endswith("_auto_cover.svg") or "auto-cover" in combined or "auto cover" in combined or "automaticky gener" in combined:
        return "auto_cover"
    if src.endswith(".svg") or "ilustrativ" in combined or "svg cover" in combined:
        return "illustration"
    return "photo"


def normalize_manifest(payload: dict[str, list[dict[str, str]]]) -> dict[str, list[dict[str, str]]]:
    normalized: dict[str, list[dict[str, str]]] = {}
    for plant_id, entries in payload.items():
        if not isinstance(entries, list):
            continue
        normalized_entries: list[dict[str, str]] = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            src = str(entry.get("src", "")).strip()
            if not src:
                continue
            normalized_entries.append(
                {
                    "src": src,
                    "alt": str(entry.get("alt", "")).strip(),
                    "caption": str(entry.get("caption", "")).strip(),
                    "credit": str(entry.get("credit", "")).strip(),
                    "source_name": str(entry.get("source_name", "")).strip(),
                    "source_url": str(entry.get("source_url", "")).strip(),
                    "license": str(entry.get("license", "")).strip(),
                    "media_kind": infer_media_kind(entry),
                }
            )
        if normalized_entries:
            normalized[plant_id] = normalized_entries
    return normalized


def choose_palette(plant_id: str) -> tuple[str, str, str, str]:
    checksum = sum(ord(ch) for ch in plant_id)
    return PALETTES[checksum % len(PALETTES)]


def ascii_slug(value: str) -> str:
    replacements = {
        "á": "a",
        "ä": "a",
        "č": "c",
        "ď": "d",
        "é": "e",
        "ě": "e",
        "í": "i",
        "ľ": "l",
        "ĺ": "l",
        "ň": "n",
        "ó": "o",
        "ô": "o",
        "ö": "o",
        "ř": "r",
        "š": "s",
        "ť": "t",
        "ú": "u",
        "ů": "u",
        "ü": "u",
        "ý": "y",
        "ž": "z",
        "/": "-",
        " ": "-",
    }
    normalized = "".join(replacements.get(ch.lower(), ch.lower()) for ch in value)
    safe = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in normalized)
    while "--" in safe:
        safe = safe.replace("--", "-")
    return safe.strip("-_") or "plant"


def fetch_top_plants(db_path: Path, limit: int) -> list[PlantRecord]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT plant_id, cesky_nazev_hlavni, vedecky_nazev_hlavni, pocet_pouziti
            FROM plants
            ORDER BY pocet_pouziti DESC, cesky_nazev_hlavni ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    finally:
        conn.close()
    return [PlantRecord(**dict(row)) for row in rows]


def wrap_text(text: str, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    current_len = 0
    for word in words:
        next_len = current_len + len(word) + (1 if current else 0)
        if current and next_len > width:
            lines.append(" ".join(current))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len = next_len
    if current:
        lines.append(" ".join(current))
    return lines[:2]


def build_svg(record: PlantRecord) -> str:
    bg_start, bg_end, accent, ink = choose_palette(record.plant_id)
    czech_lines = wrap_text(record.cesky_nazev_hlavni, 20)
    latin_line = record.vedecky_nazev_hlavni.upper()
    initials = "".join(part[:1].upper() for part in record.cesky_nazev_hlavni.split()[:3]) or record.cesky_nazev_hlavni[:2].upper()

    text_y = 640
    czech_blocks = []
    for index, line in enumerate(czech_lines):
        czech_blocks.append(
            f'<text x="84" y="{text_y + index * 88}" font-family="Georgia, \'Palatino Linotype\', serif" font-size="86">{escape(line)}</text>'
        )

    shapes = f"""
      <circle cx="1025" cy="155" r="180" fill="#ffffff" opacity="0.38"/>
      <circle cx="176" cy="770" r="220" fill="{accent}" opacity="0.12"/>
      <path d="M296 782 C378 628 490 470 614 226" fill="none" stroke="{accent}" stroke-width="18" stroke-linecap="round"/>
      <path d="M458 472 C572 410 708 430 856 532" fill="none" stroke="{accent}" stroke-width="12" stroke-linecap="round"/>
      <path d="M376 334 C310 284 232 286 162 350" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/>
      <circle cx="612" cy="234" r="88" fill="{accent}" opacity="0.18"/>
      <circle cx="792" cy="516" r="72" fill="{accent}" opacity="0.14"/>
      <circle cx="252" cy="420" r="54" fill="{accent}" opacity="0.16"/>
      <text x="875" y="738" text-anchor="middle" font-family="'Trebuchet MS', 'Segoe UI', sans-serif" font-size="220" fill="{accent}" opacity="0.22">{escape(initials)}</text>
    """

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 900" role="img" aria-labelledby="title desc">
  <title id="title">{escape(record.cesky_nazev_hlavni)}</title>
  <desc id="desc">Automaticky generovaný ilustrativní cover pro profil rostliny {escape(record.cesky_nazev_hlavni)}.</desc>
  <defs>
    <linearGradient id="bg" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0%" stop-color="{bg_start}"/>
      <stop offset="100%" stop-color="{bg_end}"/>
    </linearGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="18" stdDeviation="18" flood-color="{ink}" flood-opacity="0.12"/>
    </filter>
  </defs>
  <rect width="1200" height="900" fill="url(#bg)"/>
  <g filter="url(#shadow)">
    {shapes}
  </g>
  <g fill="{ink}">
    {''.join(czech_blocks)}
    <text x="88" y="792" font-family="'Trebuchet MS', 'Segoe UI', sans-serif" font-size="32" letter-spacing="3">{escape(latin_line)}</text>
    <text x="88" y="846" font-family="'Trebuchet MS', 'Segoe UI', sans-serif" font-size="24" letter-spacing="2">AUTO COVER · {record.pocet_pouziti} POUZITI V DATASETU</text>
  </g>
</svg>
"""


def ensure_manifest_entry(manifest: dict[str, list[dict[str, str]]], record: PlantRecord, file_name: str) -> None:
    entries = manifest.setdefault(record.plant_id, [])
    local_src = next((entry for entry in entries if entry.get("src") == file_name), None)
    if local_src is None:
        entries.append(
            {
                "src": file_name,
                "alt": f"Ilustrativní cover pro {record.cesky_nazev_hlavni}",
                "caption": "Automaticky generovaný lokální cover pro profil rostliny",
                "credit": "interní auto-cover generator",
                "source_name": "",
                "source_url": "",
                "license": "",
                "media_kind": "auto_cover",
            }
        )
        return

    local_src["media_kind"] = "auto_cover"


def count_media_kinds(manifest: dict[str, list[dict[str, str]]]) -> Counter:
    counts: Counter = Counter()
    for entries in manifest.values():
        for entry in entries:
            counts[entry.get("media_kind", "photo")] += 1
    return counts


def primary_media_kind(entries: list[dict[str, str]]) -> str:
    if not entries:
        return "none"
    return str(entries[0].get("media_kind", "photo"))


def build_report(
    selected: list[PlantRecord],
    generated: list[PlantRecord],
    manifest_before: dict[str, list[dict[str, str]]],
    manifest_after: dict[str, list[dict[str, str]]],
    *,
    limit: int,
    missing_only: bool,
) -> str:
    command = f"python .\\scripts\\build_media_covers.py --limit {limit}"
    if missing_only:
        command += " --missing-only"
    kind_counts = count_media_kinds(manifest_after)

    lines = [
        "# Media Pokryti A Auto-Covers",
        "",
        "## Co se stalo",
        "",
        f"- Pocet rostlin v manifestu pred behem: {len(manifest_before)}",
        f"- Pocet rostlin v manifestu po behu: {len(manifest_after)}",
        f"- Zvažovaný batch: {len(selected)} top rostlin podle `pocet_pouziti`",
        f"- Nove vygenerovane auto-covery: {len(generated)}",
        f"- Polozky typu `auto_cover`: {kind_counts.get('auto_cover', 0)}",
        f"- Polozky typu `illustration`: {kind_counts.get('illustration', 0)}",
        f"- Polozky typu `photo`: {kind_counts.get('photo', 0)}",
        "",
        "## Batch",
        "",
    ]
    generated_ids = {item.plant_id for item in generated}
    for record in selected:
        status = "nove generovano" if record.plant_id in generated_ids else "uz melo media"
        lines.append(f"- `{record.plant_id}` · {record.cesky_nazev_hlavni} · {record.pocet_pouziti} pouziti · {status}")
    lines.extend(
        [
            "",
            "## Workflow",
            "",
            "```powershell",
            command,
            "```",
            "",
            "Skript zachovava existujici rucne pripravene polozky v `plant_media.json` a doplnuje jen chybejici lokalni SVG cover soubory.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def build_priority_report(selected: list[PlantRecord], manifest_after: dict[str, list[dict[str, str]]]) -> str:
    auto_records = [record for record in selected if primary_media_kind(manifest_after.get(record.plant_id, [])) == "auto_cover"]
    illustration_records = [record for record in selected if primary_media_kind(manifest_after.get(record.plant_id, [])) == "illustration"]
    photo_records = [record for record in selected if primary_media_kind(manifest_after.get(record.plant_id, [])) == "photo"]

    def add_section(lines: list[str], heading: str, records: list[PlantRecord]) -> None:
        lines.extend(["", f"## {heading}", ""])
        if not records:
            lines.append("- zadne polozky")
            return
        for record in records:
            lines.append(f"- `{record.plant_id}` · {record.cesky_nazev_hlavni} · {record.pocet_pouziti} pouziti")

    lines = [
        "# Media Nahrady Prioritizace",
        "",
        "## Souhrn",
        "",
        f"- Rostlin s primarnim auto-coverem: {len(auto_records)}",
        f"- Rostlin s rucni ilustraci: {len(illustration_records)}",
        f"- Rostlin s primarni skutecnou fotkou: {len(photo_records)}",
        "",
        "## Doporuceni",
        "",
        "- Nahrazovat nejdriv auto-covery u rostlin s nejvyssim `pocet_pouziti`.",
        "- U rucnich ilustraci je nizsi urgence, protoze jsou uz kuratorovane a vizualne stabilni.",
        "- Jakmile pridas skutecnou fotku jako prvni polozku v seznamu media pro danou rostlinu, UI ji zacne pouzivat jako primarni.",
        "",
    ]

    add_section(lines, "Top 20 Auto-Coveru K Nahrade", auto_records[:20])
    add_section(lines, "Rucni Ilustrace", illustration_records)
    add_section(lines, "Skutecne Fotky", photo_records)
    lines.extend(
        [
            "",
            "## Prakticky Postup",
            "",
            "1. U vybraneho `plant_id` vloz skutecnou fotku jako prvni polozku v `plant_media.json`.",
            "2. Vypln `credit` a nastav `media_kind` na `photo`.",
            "3. Ponech puvodni ilustraci nebo auto-cover az jako druhou polozku jen jako fallback.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    APP_MEDIA_DIR.mkdir(parents=True, exist_ok=True)

    manifest_before = normalize_manifest(load_manifest())
    manifest_after = json.loads(json.dumps(manifest_before, ensure_ascii=False))

    selected = fetch_top_plants(args.db, args.limit)
    generated: list[PlantRecord] = []

    for record in selected:
        if args.missing_only and record.plant_id in manifest_after:
            continue

        file_name = f"{ascii_slug(record.plant_id)}_auto_cover.svg"
        file_path = APP_MEDIA_DIR / file_name
        if file_path.exists() and not args.overwrite_files:
            ensure_manifest_entry(manifest_after, record, file_name)
            continue

        file_path.write_text(build_svg(record), encoding="utf-8")
        ensure_manifest_entry(manifest_after, record, file_name)
        generated.append(record)

    save_manifest(manifest_after)

    report_path = ROOT / "MEDIA_POKRYTI_A_AUTO_COVERS.md"
    report_path.write_text(
        build_report(
            selected,
            generated,
            manifest_before,
            manifest_after,
            limit=args.limit,
            missing_only=args.missing_only,
        ),
        encoding="utf-8",
    )

    priority_report_path = ROOT / "MEDIA_NAHRADY_PRIORITIZACE.md"
    priority_report_path.write_text(build_priority_report(selected, manifest_after), encoding="utf-8")

    print(f"Generated covers: {len(generated)}")
    print(f"Manifest entries: {len(manifest_after)}")
    print(f"Report: {report_path}")
    print(f"Priority report: {priority_report_path}")


if __name__ == "__main__":
    main()
