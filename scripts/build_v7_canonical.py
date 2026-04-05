from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import openpyxl

from gathering_guidance import build_gathering_guidance
from preservation_methods import (
    build_processing_method_vocab_rows,
    extract_processing_method_ids,
    processing_methods_text,
)


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    return normalized.strip("_")


def choose_workbook(base_dir: Path) -> Path:
    workbooks = sorted(base_dir.glob("*.xlsx"))
    if not workbooks:
        raise FileNotFoundError("No .xlsx workbook found in the workspace.")

    preferred = base_dir / "cz_rostliny_rozsireny_dataset_v6_jadro_bezne_trvanlive.xlsx"
    if preferred.exists():
        return preferred

    return workbooks[0]


def normalize_cell(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip()
    return value


def read_sheet(ws: openpyxl.worksheet.worksheet.Worksheet) -> tuple[list[str], list[dict[str, Any]]]:
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return [], []
    headers = [str(value).strip() if value is not None else f"column_{idx+1}" for idx, value in enumerate(rows[0])]
    records = []
    for row in rows[1:]:
        if not any(value not in (None, "") for value in row):
            continue
        records.append({header: normalize_cell(value) for header, value in zip(headers, row)})
    return headers, records


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    headers = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def unique_slug(base_slug: str, used: set[str]) -> str:
    if base_slug not in used:
        used.add(base_slug)
        return base_slug
    index = 2
    while f"{base_slug}_{index}" in used:
        index += 1
    final_slug = f"{base_slug}_{index}"
    used.add(final_slug)
    return final_slug


def source_family_from_url(url: str | None) -> str | None:
    if not url:
        return None
    lowered = url.lower()
    if "ema.europa.eu" in lowered:
        return "ema"
    if "pfaf.org" in lowered:
        return "pfaf"
    if "researchgate.net" in lowered:
        return "researchgate"
    if "pmc.ncbi.nlm.nih.gov" in lowered:
        return "pmc"
    if "mdpi.com" in lowered:
        return "mdpi"
    return slugify(url.split("/")[2]) if "://" in url else slugify(url)


def build_vocab_table(rows: list[dict[str, Any]], id_field: str, label_field: str) -> list[dict[str, Any]]:
    seen = set()
    vocab_rows = []
    for row in rows:
        key = row[id_field]
        if key in seen:
            continue
        seen.add(key)
        vocab_rows.append(row)
    return vocab_rows


def main() -> None:
    project_dir = Path(__file__).resolve().parents[1]
    workbook_path = choose_workbook(project_dir)
    workbook = openpyxl.load_workbook(workbook_path, data_only=True)
    workbook_stem = workbook_path.stem

    export_dir = project_dir / "exports" / workbook_stem
    normalized_starter_path = export_dir / "normalized" / "starter_dataset_normalized.json"
    if not normalized_starter_path.exists():
        raise FileNotFoundError(
            f"Normalized export not found at {normalized_starter_path}. Run export_workbook.py first."
        )

    normalized_starter_rows = json.loads(normalized_starter_path.read_text(encoding="utf-8"))

    _, zdroje_rows = read_sheet(workbook["Zdroje"])
    _, trvanlive_rows = read_sheet(workbook["Trvanlive_1m_plus"])
    _, jadro_rows = read_sheet(workbook["Jadro_bezne_1m_plus"])

    canonical_dir = export_dir / "v7_canonical"
    canonical_json_dir = canonical_dir / "json"
    canonical_csv_dir = canonical_dir / "csv"

    # Plants and aliases
    used_plant_ids: set[str] = set()
    scientific_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in normalized_starter_rows:
        scientific_groups[row["vedecky_nazev"]].append(row)

    plants = []
    plant_aliases = []
    plant_id_by_scientific: dict[str, str] = {}

    for scientific_name, group_rows in sorted(scientific_groups.items()):
        plant_id = unique_slug(f"plant_{slugify(scientific_name)}", used_plant_ids)
        plant_id_by_scientific[scientific_name] = plant_id

        czech_name_counts = Counter(row["cesky_nazev"] for row in group_rows)
        primary_czech_name = czech_name_counts.most_common(1)[0][0]
        status_values = [row["status_v_CR"] for row in group_rows if row.get("status_v_CR")]
        status_counter = Counter(status_values)
        representative_status = status_counter.most_common(1)[0][0] if status_counter else None
        any_row = group_rows[0]

        plants.append(
            {
                "plant_id": plant_id,
                "vedecky_nazev_hlavni": scientific_name,
                "vedecky_nazev_display": scientific_name,
                "taxon_rank": "group" if "spp." in scientific_name.lower() or "agg." in scientific_name.lower() else "species_or_higher",
                "je_agregat_nebo_spp": ("spp." in scientific_name.lower() or "agg." in scientific_name.lower()),
                "cesky_nazev_hlavni": primary_czech_name,
                "status_v_cr_text": representative_status,
                "status_puvodni": any(row.get("status_contains_puvodni") for row in group_rows),
                "status_zdomacnely": any(row.get("status_contains_zdomacnely") for row in group_rows),
                "status_pestovany": any(row.get("status_contains_pestovany") for row in group_rows),
                "status_zplanujici": any(row.get("status_contains_zplanujici") for row in group_rows),
                "status_invazni": any(row.get("status_contains_invazni") for row in group_rows),
                "status_cetnost_reprezentativni": any_row.get("status_cetnost"),
                "pocet_pouziti": len(group_rows),
                "pocet_ceskych_aliasu": len(czech_name_counts),
            }
        )

        alias_order = 1
        for czech_name, count in sorted(czech_name_counts.items(), key=lambda item: (-item[1], item[0])):
            plant_aliases.append(
                {
                    "alias_id": f"{plant_id}_cz_{alias_order}",
                    "plant_id": plant_id,
                    "alias": czech_name,
                    "jazyk": "cs",
                    "typ_aliasu": "cesky_nazev",
                    "je_preferovany": czech_name == primary_czech_name,
                    "pocet_vyskytu": count,
                }
            )
            alias_order += 1

        plant_aliases.append(
            {
                "alias_id": f"{plant_id}_la_1",
                "plant_id": plant_id,
                "alias": scientific_name,
                "jazyk": "la",
                "typ_aliasu": "vedecky_nazev",
                "je_preferovany": True,
                "pocet_vyskytu": len(group_rows),
            }
        )

    # Uses
    trvanlive_by_id = {row["record_id"]: row for row in trvanlive_rows}
    uses = []
    use_processing_methods = []
    for row in normalized_starter_rows:
        plant_id = plant_id_by_scientific[row["vedecky_nazev"]]
        trvanlive_row = trvanlive_by_id.get(row["record_id"])
        method_ids = extract_processing_method_ids(
            row.get("poddomena"),
            row.get("zpusob_pripravy_nebo_vyuziti"),
            trvanlive_row.get("forma_uchovani") if trvanlive_row else None,
        )
        method_text = processing_methods_text(method_ids)
        uses.append(
            {
                "use_id": row["record_id"].lower(),
                "plant_id": plant_id,
                "raw_record_id": row["record_id"],
                "cesky_nazev_display": row["cesky_nazev"],
                "cast_rostliny_text": row["cast_rostliny"],
                "cast_rostliny_kategorie": row["cast_rostliny_skupina"],
                "cast_rostliny_je_kombinovana": row["cast_rostliny_je_kombinovana"],
                "domena": row["domena"],
                "domena_slug": row["domena_slug"],
                "poddomena_text": row["poddomena"],
                "poddomena_kategorie": row["poddomena_kategorie"],
                "status_znalosti": row["status_znalosti"],
                "status_znalosti_slug": row["status_znalosti_slug"],
                "aplikovatelnost_v_cr": row["aplikovatelnost_v_CR"],
                "aplikovatelnost_slug": row["aplikovatelnost_slug"],
                "typicke_lokality_text": row["typicke_lokality_v_CR"],
                "obdobi_ziskani_text": row["obdobi_ziskani"],
                "mesic_od": row["obdobi_mesic_od"],
                "mesic_do": row["obdobi_mesic_do"],
                "fenologicka_faze": row["fenologicka_faze"],
                "zpusob_pripravy": row["zpusob_pripravy_nebo_vyuziti"],
                "cilovy_efekt": row["cilovy_efekt"],
                "chutovy_profil": row["chutovy_profil"],
                "vonny_profil": row["vonny_profil"],
                "palivovy_potencial_text": row["palivovy_potencial"],
                "hlavni_rizika": row["hlavni_rizika"],
                "kontraindikace_interakce": row["kontraindikace_interakce"],
                "legalita_poznamka_cr": row["legalita_poznamka_CR"],
                "dukaznost_typ": row["dukaznost_typ"],
                "dukaznost_skore": row["dukaznost_skore"],
                "dukaznost_rank": row["dukaznost_rank"],
                "ma_druhy_zdroj": row["ma_druhy_zdroj"],
                "je_trvanlive_1m_plus": row["is_trvanlive_1m_plus"],
                "je_v_jadru_bezne_1m_plus": row["is_jadro_bezne_1m_plus"],
                "processing_methods_text": method_text,
                "processing_methods_count": len(method_ids),
                "ma_potravinove_konzervacni_metody": bool(method_ids),
                "sber_doporuceni": build_gathering_guidance(row),
                "kuratorska_poznamka": row["poznamka"],
            }
        )
        for order, method_id in enumerate(method_ids, start=1):
            use_processing_methods.append(
                {
                    "use_processing_method_id": f"{row['record_id'].lower()}_{method_id}",
                    "use_id": row["record_id"].lower(),
                    "raw_record_id": row["record_id"],
                    "processing_method_id": method_id,
                    "method_order": order,
                    "from_trvanlive_sheet": bool(trvanlive_row),
                }
            )

    # Durable forms
    jadro_by_id = {row["record_id"]: row for row in jadro_rows}
    durable_forms = []
    for row in trvanlive_rows:
        jadro_match = jadro_by_id.get(row["record_id"])
        method_ids = extract_processing_method_ids(
            row.get("forma_uchovani"),
            row.get("cesky_nazev"),
        )
        durable_forms.append(
            {
                "durable_id": f"durable_{row['record_id'].lower()}",
                "use_id": row["record_id"].lower(),
                "raw_record_id": row["record_id"],
                "plant_display_name": row["cesky_nazev"],
                "forma_uchovani_text": row["forma_uchovani"],
                "forma_uchovani_kategorie": slugify(row["forma_uchovani"]),
                "orientacni_trvanlivost_text": row["orientacni_trvanlivost"],
                "poznamka_k_skladovani": row.get("poznamka_k_skladovani"),
                "processing_methods_text": processing_methods_text(method_ids),
                "processing_methods_count": len(method_ids),
                "is_core_item": bool(jadro_match),
                "proc_je_v_jadru": jadro_match.get("proc_je_v_jadru") if jadro_match else None,
            }
        )

    # Sources and relations
    referenced_source_ids: set[str] = set()
    use_sources = []
    for row in normalized_starter_rows:
        for order, source_field in enumerate(("zdroj_id_1", "zdroj_id_2"), start=1):
            source_id = row.get(source_field)
            if not source_id:
                continue
            referenced_source_ids.add(source_id)
            use_sources.append(
                {
                    "use_source_id": f"{row['record_id'].lower()}_{source_id.lower()}",
                    "use_id": row["record_id"].lower(),
                    "source_id": source_id.lower(),
                    "raw_source_id": source_id,
                    "role_zdroje": "primary" if order == 1 else "secondary",
                    "poradi": order,
                }
            )

    sources = []
    for row in zdroje_rows:
        source_id = row["zdroj_id"]
        sources.append(
            {
                "source_id": source_id.lower(),
                "raw_source_id": source_id,
                "nazev": row["nazev"],
                "url": row["url"],
                "source_family": source_family_from_url(row.get("url")),
                "is_referenced": source_id in referenced_source_ids,
                "poznamka": row.get("poznamka"),
            }
        )

    # Vocabulary tables
    part_categories = build_vocab_table(
        [
            {
                "part_category_id": category,
                "label": category.replace("_", " "),
                "row_count": count,
            }
            for category, count in Counter(row["cast_rostliny_kategorie"] for row in uses).most_common()
        ],
        "part_category_id",
        "label",
    )
    subdomain_categories = build_vocab_table(
        [
            {
                "subdomain_category_id": category,
                "label": category.replace("_", " "),
                "row_count": count,
            }
            for category, count in Counter(row["poddomena_kategorie"] for row in uses).most_common()
        ],
        "subdomain_category_id",
        "label",
    )
    storage_categories = build_vocab_table(
        [
            {
                "storage_category_id": category,
                "label": category.replace("_", " "),
                "row_count": count,
            }
            for category, count in Counter(row["forma_uchovani_kategorie"] for row in durable_forms).most_common()
        ],
        "storage_category_id",
        "label",
    )
    processing_methods_vocab = build_processing_method_vocab_rows()

    payloads = {
        "plants": plants,
        "plant_aliases": plant_aliases,
        "uses": uses,
        "durable_forms": durable_forms,
        "sources": sources,
        "use_sources": use_sources,
        "use_processing_methods": use_processing_methods,
        "vocab_part_categories": part_categories,
        "vocab_subdomain_categories": subdomain_categories,
        "vocab_storage_categories": storage_categories,
        "vocab_processing_methods": processing_methods_vocab,
    }

    for name, rows in payloads.items():
        write_csv(canonical_csv_dir / f"{name}.csv", rows)
        write_json(canonical_json_dir / f"{name}.json", rows)

    czech_to_scientific: dict[str, set[str]] = defaultdict(set)
    for row in normalized_starter_rows:
        czech_to_scientific[row["cesky_nazev"]].add(row["vedecky_nazev"])
    ambiguous_czech_name_examples = [
        {
            "cesky_nazev": name,
            "vedecke_nazvy": sorted(values),
        }
        for name, values in sorted(czech_to_scientific.items())
        if len(values) > 1
    ][:10]

    summary = {
        "workbook_file": workbook_path.name,
        "canonical_output_dir": str(canonical_dir),
        "table_counts": {name: len(rows) for name, rows in payloads.items()},
        "referenced_source_count": len(referenced_source_ids),
        "unreferenced_source_count": len([row for row in sources if not row["is_referenced"]]),
        "scientific_name_collisions_with_multiple_czech_names": len(
            [name for name, rows in scientific_groups.items() if len({row['cesky_nazev'] for row in rows}) > 1]
        ),
        "ambiguous_czech_names": len([name for name, values in czech_to_scientific.items() if len(values) > 1]),
        "ambiguous_czech_name_examples": ambiguous_czech_name_examples,
    }

    write_json(canonical_dir / "summary.json", summary)
    manifest = {
        "tables": list(payloads.keys()),
        "csv_dir": str(canonical_csv_dir),
        "json_dir": str(canonical_json_dir),
        "summary_file": str(canonical_dir / "summary.json"),
    }
    write_json(canonical_dir / "manifest.json", manifest)

    print(f"Canonical dataset written to: {canonical_dir}")


if __name__ == "__main__":
    main()
