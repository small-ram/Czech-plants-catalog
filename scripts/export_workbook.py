from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import openpyxl


ROMAN_MONTHS = {
    "I": 1,
    "II": 2,
    "III": 3,
    "IV": 4,
    "V": 5,
    "VI": 6,
    "VII": 7,
    "VIII": 8,
    "IX": 9,
    "X": 10,
    "XI": 11,
    "XII": 12,
}

SHEET_HEADER_RENAMES = {
    "README": {
        "README": "key",
        "": "value",
    },
}


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    return normalized.strip("_")


def normalize_cell(value: Any) -> Any:
    if isinstance(value, str):
        value = value.strip()
        return value
    return value


def choose_workbook(base_dir: Path) -> Path:
    workbooks = sorted(base_dir.glob("*.xlsx"))
    if not workbooks:
        raise FileNotFoundError("No .xlsx workbook found in the workspace.")

    preferred = base_dir / "cz_rostliny_rozsireny_dataset_v6_jadro_bezne_trvanlive.xlsx"
    if preferred.exists():
        return preferred

    return workbooks[0]


def sanitize_headers(sheet_name: str, raw_headers: list[Any]) -> list[str]:
    rename_map = SHEET_HEADER_RENAMES.get(sheet_name, {})
    headers: list[str] = []
    seen: Counter[str] = Counter()

    for idx, raw in enumerate(raw_headers, start=1):
        header = "" if raw is None else str(raw).strip()
        header = rename_map.get(header, header)
        if not header:
            header = f"column_{idx}"

        seen[header] += 1
        if seen[header] > 1:
            header = f"{header}_{seen[header]}"

        headers.append(header)

    return headers


def read_sheet(ws: openpyxl.worksheet.worksheet.Worksheet) -> dict[str, Any]:
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return {"sheet_name": ws.title, "headers": [], "rows": []}

    headers = sanitize_headers(ws.title, list(rows[0]))
    records = []
    for row in rows[1:]:
        if not any(value not in (None, "") for value in row):
            continue
        record = {header: normalize_cell(value) for header, value in zip(headers, row)}
        records.append(record)

    return {
        "sheet_name": ws.title,
        "headers": headers,
        "rows": records,
    }


def write_csv(path: Path, rows: list[dict[str, Any]], headers: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header, "") for header in headers})


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def parse_roman_month_window(value: Any) -> tuple[int | None, int | None]:
    if not isinstance(value, str) or not value:
        return None, None

    tokens = re.findall(r"(?<![A-Z])(?:XII|XI|X|IX|VIII|VII|VI|V|IV|III|II|I)(?![A-Z])", value)
    months = [ROMAN_MONTHS[token] for token in tokens if token in ROMAN_MONTHS]
    if months:
        return months[0], months[-1]

    lowered = value.lower()
    season_map = {
        "jaro": (3, 5),
        "léto": (6, 8),
        "podzim": (9, 11),
        "zima": (12, 2),
        "celoročně": (1, 12),
    }
    for key, window in season_map.items():
        if key in lowered:
            return window

    return None, None


def normalize_domain(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    mapping = {
        "potrava": "potrava",
        "pití": "piti",
        "potrava a pití": "potrava_a_piti",
        "fytoterapie": "fytoterapie",
        "vůně": "vune",
        "léčba": "lecba",
        "palivo": "palivo",
    }
    return mapping.get(value, slugify(value))


def normalize_knowledge_status(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    mapping = {
        "mainstream": "mainstream",
        "méně známé": "mene_zname",
        "téměř zapomenuté": "temer_zapomenute",
        "globální analog": "globalni_analog",
        "izolovaný záznam": "izolovany_zaznam",
    }
    return mapping.get(value, slugify(value))


def normalize_applicability(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    mapping = {
        "vysoká": "vysoka",
        "střední": "stredni",
        "nízká": "nizka",
        "nízká až střední": "nizka_az_stredni",
    }
    return mapping.get(value, slugify(value))


def evidence_rank(value: Any) -> int | None:
    if not isinstance(value, str) or not value:
        return None
    mapping = {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1}
    return mapping.get(value)


def normalize_part_group(value: Any) -> tuple[str | None, bool]:
    if not isinstance(value, str) or not value:
        return None, False

    lowered = value.lower()
    matches = []

    keyword_groups = {
        "kvetni_cast": ["květ", "květy", "květenství", "kvetouc"],
        "listova_nadzemni_cast": ["list", "listy", "nať", "lodyha", "řapík", "stonky", "vrcholy", "růžice"],
        "vyhonky_a_pupeny": ["výhon", "výhonk", "pupen"],
        "podzemni_cast": ["kořen", "bulva", "hlíza", "cibule", "stroužek"],
        "plodova_cast": ["plod", "plody", "malvice", "šípek", "pseudoplod"],
        "semena_a_orisky": ["semeno", "semena", "bukvice", "žalud", "ořech", "jádro", "šištice"],
        "drevnata_cast": ["kůra", "dřevo", "větévky", "pryskyřice", "troud"],
        "miza": ["míza"],
    }

    for group, keywords in keyword_groups.items():
        if any(keyword in lowered for keyword in keywords):
            matches.append(group)

    unique_matches = list(dict.fromkeys(matches))
    if not unique_matches:
        return "ostatni", False

    if len(unique_matches) > 1:
        return "kombinovana_cast", True

    return unique_matches[0], False


def normalize_subdomain_category(value: Any) -> tuple[str | None, str]:
    if not isinstance(value, str) or not value:
        return None, "low"

    lowered = value.lower()
    rules = [
        ("caj_nalev", ["čaj", "nálev"]),
        ("sirup_koncentrat", ["sirup", "cordial"]),
        ("liker_macerat", ["likér", "ořechovka", "macer", "tinkt"]),
        ("ocet", ["ocet", "octov"]),
        ("zavarenina", ["džem", "želé", "rosol", "kompot", "povidla", "zavařen"]),
        ("koreni_dochucovadlo", ["koření", "dochucovač"]),
        ("kavova_nahrada", ["kávová náhražka", "náhražka kávy"]),
        ("mouka_skrob", ["mouka"]),
        ("olej", ["olej"]),
        ("zevni_aplikace", ["obklad", "oplach", "koupele", "zevní", "přiložení"]),
        ("vune_a_vykurovani", ["vykuř", "kadidlo", "polštář", "sáček", "aromat"]),
        ("palivo", ["podpal", "troud", "palivové dřevo", "teplo"]),
        ("fermentace", ["ferment", "kvašen"]),
        ("suseni_skladovani", ["sušen", "zásoby", "do zásoby"]),
        ("cerstva_potrava", ["zelenina", "polévka", "špenát", "salát", "svačina", "čerstvé"]),
        ("odvar", ["odvar"]),
    ]

    for category, keywords in rules:
        if any(keyword in lowered for keyword in keywords):
            confidence = "high" if len(keywords) == 1 else "medium"
            return category, confidence

    return "ostatni_specialni", "low"


def normalize_storage_form(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None

    lowered = value.lower()
    rules = [
        ("suseni", ["sušen", "sušení", "svazeček", "sáček"]),
        ("sirup", ["sirup", "koncentrát"]),
        ("zavarenina", ["zavařen", "želé"]),
        ("ocet", ["ocet", "octové"]),
        ("fermentovany_napoj", ["kvašený nápoj"]),
        ("alkoholovy_macerat", ["alkoholová macerace"]),
        ("olej", ["olej"]),
        ("suche_skladovani", ["suché skladování"]),
        ("prazeni", ["pražení"]),
        ("nakladani", ["nakládání"]),
        ("pryskyrice", ["pryskyřice"]),
    ]

    for category, keywords in rules:
        if any(keyword in lowered for keyword in keywords):
            return category

    return slugify(value)


def derive_status_flags(value: Any) -> dict[str, Any]:
    lowered = value.lower() if isinstance(value, str) else ""
    if not lowered:
        return {
            "status_contains_puvodni": False,
            "status_contains_zdomacnely": False,
            "status_contains_pestovany": False,
            "status_contains_zplanujici": False,
            "status_contains_invazni": False,
            "status_cetnost": None,
        }

    if "velmi běž" in lowered:
        cetnost = "velmi_bezny"
    elif "lokálně vzác" in lowered or "vzácněj" in lowered:
        cetnost = "vzacnejsi"
    elif "lokálně hojn" in lowered:
        cetnost = "lokalne_hojny"
    elif "lokálně běž" in lowered or "běžná lokálně" in lowered or "běžný lokálně" in lowered:
        cetnost = "lokalne_bezny"
    elif "běž" in lowered:
        cetnost = "bezny"
    else:
        cetnost = "neurceno"

    return {
        "status_contains_puvodni": "původní" in lowered,
        "status_contains_zdomacnely": "zdomácněl" in lowered,
        "status_contains_pestovany": "pěstovan" in lowered,
        "status_contains_zplanujici": "zplaňuj" in lowered,
        "status_contains_invazni": "invaz" in lowered,
        "status_cetnost": cetnost,
    }


def add_normalized_fields(
    starter_rows: list[dict[str, Any]],
    trvanlive_ids: set[str],
    jadro_ids: set[str],
) -> list[dict[str, Any]]:
    normalized_rows = []
    for row in starter_rows:
        month_from, month_to = parse_roman_month_window(row.get("obdobi_ziskani"))
        part_group, is_compound = normalize_part_group(row.get("cast_rostliny"))
        subdomain_category, subdomain_confidence = normalize_subdomain_category(row.get("poddomena"))
        enriched = dict(row)
        enriched.update(
            {
                "record_numeric_id": int(str(row["record_id"])[1:]) if row.get("record_id") else None,
                "is_trvanlive_1m_plus": row.get("record_id") in trvanlive_ids,
                "is_jadro_bezne_1m_plus": row.get("record_id") in jadro_ids,
                "domena_slug": normalize_domain(row.get("domena")),
                "status_znalosti_slug": normalize_knowledge_status(row.get("status_znalosti")),
                "aplikovatelnost_slug": normalize_applicability(row.get("aplikovatelnost_v_CR")),
                "dukaznost_rank": evidence_rank(row.get("dukaznost_skore")),
                "ma_druhy_zdroj": bool(row.get("zdroj_id_2")),
                "obdobi_mesic_od": month_from,
                "obdobi_mesic_do": month_to,
                "cast_rostliny_skupina": part_group,
                "cast_rostliny_je_kombinovana": is_compound,
                "poddomena_kategorie": subdomain_category,
                "poddomena_kategorie_confidence": subdomain_confidence,
            }
        )
        enriched.update(derive_status_flags(row.get("status_v_CR")))
        normalized_rows.append(enriched)

    return normalized_rows


def build_mapping_rows(
    values: list[str],
    classifier,
    extra_columns: list[str] | None = None,
) -> list[dict[str, Any]]:
    counter = Counter(values)
    rows = []
    extra_columns = extra_columns or []

    for original_value, count in sorted(counter.items(), key=lambda item: (-item[1], item[0])):
        result = classifier(original_value)
        if isinstance(result, tuple):
            if len(result) == 2:
                normalized_value, aux_value = result
                row = {
                    "original_value": original_value,
                    "count": count,
                    "suggested_value": normalized_value,
                    extra_columns[0] if extra_columns else "aux": aux_value,
                }
            else:
                raise ValueError("Unsupported tuple size from classifier.")
        elif isinstance(result, dict):
            row = {"original_value": original_value, "count": count}
            row.update(result)
        else:
            row = {
                "original_value": original_value,
                "count": count,
                "suggested_value": result,
            }
        rows.append(row)

    return rows


def build_undocumented_field_flags(sheet_payloads: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    slovnik_rows = sheet_payloads["Slovnik_sloupcu"]["rows"]
    documented_fields = {
        row["Nazev_sloupce"]
        for row in slovnik_rows
        if row.get("Nazev_sloupce")
    }

    flags = []
    for sheet_name in ("Starter_dataset", "Zdroje", "Trvanlive_1m_plus", "Jadro_bezne_1m_plus"):
        for field in sheet_payloads[sheet_name]["headers"]:
            if field not in documented_fields:
                flags.append(
                    {
                        "sheet": sheet_name,
                        "field": field,
                        "severity": "medium",
                        "issue_type": "undocumented_field",
                        "detail": "Field exists in workbook but is not defined in Slovnik_sloupcu.",
                    }
                )
    return flags


def build_editorial_review_flags(jadro_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks = [
        ("R159", "šípk", "Proc_je_v_jadru still mentions šípky for švestková povidla; review wording."),
        ("R166", "listov", "Proc_je_v_jadru still mentions listový čaj for bezový květ; review wording."),
        ("R179", "čajov", "Proc_je_v_jadru still mentions čajová droga for jalovčinky used as koření; review wording."),
        ("R180", "vůně", "Proc_je_v_jadru still mentions vůně for vrbová kůra do odvaru; review wording."),
    ]
    jadro_by_id = {row["record_id"]: row for row in jadro_rows}
    flags = []
    for record_id, token, detail in checks:
        row = jadro_by_id.get(record_id)
        reason = str(row.get("proc_je_v_jadru", "")).lower() if row else ""
        if token in reason:
            flags.append(
                {
                    "sheet": "Jadro_bezne_1m_plus",
                    "record_id": record_id,
                    "severity": "medium",
                    "issue_type": "editorial_review",
                    "detail": detail,
                }
            )
    return flags


def sheet_summary(sheet_name: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "sheet_name": sheet_name,
        "row_count": len(rows),
        "column_count": len(rows[0].keys()) if rows else 0,
    }


def main() -> None:
    project_dir = Path(__file__).resolve().parents[1]
    workbook_path = choose_workbook(project_dir)
    workbook = openpyxl.load_workbook(workbook_path, data_only=True)

    output_dir = project_dir / "exports" / workbook_path.stem
    raw_csv_dir = output_dir / "raw_csv"
    raw_json_dir = output_dir / "raw_json"
    normalized_dir = output_dir / "normalized"
    meta_dir = output_dir / "meta"

    sheet_payloads = {}
    for ws in workbook.worksheets:
        payload = read_sheet(ws)
        sheet_payloads[ws.title] = payload

        csv_name = f"{slugify(ws.title)}.csv"
        json_name = f"{slugify(ws.title)}.json"
        write_csv(raw_csv_dir / csv_name, payload["rows"], payload["headers"])
        write_json(raw_json_dir / json_name, payload["rows"])

    starter_rows = sheet_payloads["Starter_dataset"]["rows"]
    trvanlive_rows = sheet_payloads["Trvanlive_1m_plus"]["rows"]
    jadro_rows = sheet_payloads["Jadro_bezne_1m_plus"]["rows"]
    zdroje_rows = sheet_payloads["Zdroje"]["rows"]

    trvanlive_ids = {row["record_id"] for row in trvanlive_rows}
    jadro_ids = {row["record_id"] for row in jadro_rows}

    normalized_starter_rows = add_normalized_fields(starter_rows, trvanlive_ids, jadro_ids)
    normalized_headers = list(normalized_starter_rows[0].keys()) if normalized_starter_rows else []
    write_csv(normalized_dir / "starter_dataset_normalized.csv", normalized_starter_rows, normalized_headers)
    write_json(normalized_dir / "starter_dataset_normalized.json", normalized_starter_rows)

    part_mapping_rows = build_mapping_rows(
        [row["cast_rostliny"] for row in starter_rows if row.get("cast_rostliny")],
        normalize_part_group,
        extra_columns=["is_compound"],
    )
    subdomain_mapping_rows = build_mapping_rows(
        [row["poddomena"] for row in starter_rows if row.get("poddomena")],
        normalize_subdomain_category,
        extra_columns=["confidence"],
    )
    status_mapping_rows = build_mapping_rows(
        [row["status_v_CR"] for row in starter_rows if row.get("status_v_CR")],
        derive_status_flags,
    )
    storage_mapping_rows = build_mapping_rows(
        [row["forma_uchovani"] for row in trvanlive_rows if row.get("forma_uchovani")],
        normalize_storage_form,
    )

    mapping_specs = [
        ("cast_rostliny_map.csv", part_mapping_rows),
        ("poddomena_map.csv", subdomain_mapping_rows),
        ("status_v_cr_map.csv", status_mapping_rows),
        ("forma_uchovani_map.csv", storage_mapping_rows),
    ]
    for filename, rows in mapping_specs:
        headers = list(rows[0].keys()) if rows else []
        write_csv(normalized_dir / filename, rows, headers)
        write_json(normalized_dir / filename.replace(".csv", ".json"), rows)

    source_ids = {row["zdroj_id"] for row in zdroje_rows if row.get("zdroj_id")}
    referenced_source_ids = {
        row[key]
        for row in starter_rows
        for key in ("zdroj_id_1", "zdroj_id_2")
        if row.get(key)
    }
    unused_sources = sorted(source_ids - referenced_source_ids)

    palivo_values = [row.get("palivovy_potencial") for row in starter_rows]
    blank_palivo_count = sum(1 for value in palivo_values if value in (None, ""))
    explicit_na_palivo_count = sum(1 for value in palivo_values if value == "neaplikovatelné")

    quality_flags = build_undocumented_field_flags(sheet_payloads)
    quality_flags.extend(
        {
            "sheet": "Zdroje",
            "field": "zdroj_id",
            "severity": "low",
            "issue_type": "unused_source",
            "detail": f"Source {source_id} exists in Zdroje but is not referenced from Starter_dataset.",
            "record_id": source_id,
        }
        for source_id in unused_sources
    )
    if blank_palivo_count and explicit_na_palivo_count:
        quality_flags.append(
            {
                "sheet": "Starter_dataset",
                "field": "palivovy_potencial",
                "severity": "medium",
                "issue_type": "mixed_na_representation",
                "detail": (
                    "Field mixes blank cells and explicit 'neaplikovatelné' values; "
                    "standardize to a single convention."
                ),
                "blank_count": blank_palivo_count,
                "explicit_na_count": explicit_na_palivo_count,
            }
        )
    quality_flags.extend(build_editorial_review_flags(jadro_rows))

    quality_headers = sorted({key for row in quality_flags for key in row.keys()})
    write_csv(meta_dir / "quality_flags.csv", quality_flags, quality_headers)
    write_json(meta_dir / "quality_flags.json", quality_flags)

    sheet_summaries = {
        sheet_name: sheet_summary(sheet_name, payload["rows"])
        for sheet_name, payload in sheet_payloads.items()
    }
    workbook_summary = {
        "workbook_file": workbook_path.name,
        "output_dir": str(output_dir),
        "sheet_summaries": sheet_summaries,
        "starter_dataset_stats": {
            "row_count": len(starter_rows),
            "unique_scientific_names": len({row["vedecky_nazev"] for row in starter_rows}),
            "unique_czech_names": len({row["cesky_nazev"] for row in starter_rows}),
            "domain_counts": Counter(row["domena"] for row in starter_rows),
            "knowledge_counts": Counter(row["status_znalosti"] for row in starter_rows),
            "evidence_score_counts": Counter(row["dukaznost_skore"] for row in starter_rows),
        },
        "trvanlive_stats": {
            "row_count": len(trvanlive_rows),
            "storage_form_counts": Counter(row["forma_uchovani"] for row in trvanlive_rows),
        },
        "jadro_stats": {
            "row_count": len(jadro_rows),
            "storage_form_counts": Counter(row["forma_uchovani"] for row in jadro_rows),
        },
        "source_stats": {
            "source_count": len(source_ids),
            "referenced_source_count": len(referenced_source_ids),
            "unused_source_ids": unused_sources,
        },
    }
    write_json(meta_dir / "workbook_summary.json", workbook_summary)

    manifest = {
        "workbook_file": workbook_path.name,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "directories": {
            "raw_csv": str(raw_csv_dir),
            "raw_json": str(raw_json_dir),
            "normalized": str(normalized_dir),
            "meta": str(meta_dir),
        },
        "key_files": [
            str(normalized_dir / "starter_dataset_normalized.csv"),
            str(normalized_dir / "starter_dataset_normalized.json"),
            str(normalized_dir / "cast_rostliny_map.csv"),
            str(normalized_dir / "poddomena_map.csv"),
            str(normalized_dir / "status_v_cr_map.csv"),
            str(meta_dir / "quality_flags.csv"),
            str(meta_dir / "workbook_summary.json"),
        ],
    }
    write_json(output_dir / "manifest.json", manifest)

    print(f"Workbook: {workbook_path.name}")
    print(f"Exported to: {output_dir}")


if __name__ == "__main__":
    main()
