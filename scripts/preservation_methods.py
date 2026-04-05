from __future__ import annotations

import re
import unicodedata


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    return normalized.lower()


PROCESSING_METHOD_DEFINITIONS = [
    {
        "processing_method_id": "suseni",
        "label": "Sušení",
        "group_label": "dehydratace",
        "patterns": [r"\bsusen\w*\b", r"\bsvaze\w*\b", r"\bsace\w*\b", r"\bkrizal\w*\b", r"\bplatk\w*\b"],
    },
    {
        "processing_method_id": "mrazeni",
        "label": "Mražení",
        "group_label": "chlad",
        "patterns": [r"\bmrazen\w*\b", r"\bzamrazen\w*\b"],
    },
    {
        "processing_method_id": "chlazene_skladovani",
        "label": "Skladování v chladu",
        "group_label": "chlad",
        "patterns": [r"\bchladu\b", r"\bchlade\b", r"\blednic\w*\b", r"\bmezisklad\w*\b", r"\bskladovan\w* v chladu\b"],
    },
    {
        "processing_method_id": "sirup",
        "label": "Sirup / koncentrát",
        "group_label": "sladke_konzervace",
        "patterns": [r"\bsirup\w*\b", r"\bkoncentrat\w*\b", r"\bcordial\b"],
    },
    {
        "processing_method_id": "zavareni",
        "label": "Zavaření / sterilace ve sklenici",
        "group_label": "tepelna_konzervace",
        "patterns": [
            r"\bzavar\w*\b",
            r"\bzavarenin\w*\b",
            r"\bdzem\w*\b",
            r"\bmarmelad\w*\b",
            r"\bzele\b",
            r"\brosol\w*\b",
            r"\bpovid\w*\b",
            r"\bmembrillo\b",
        ],
    },
    {
        "processing_method_id": "pasterace",
        "label": "Pasterace",
        "group_label": "tepelna_konzervace",
        "patterns": [r"\bpaster\w*\b"],
    },
    {
        "processing_method_id": "sterilizace",
        "label": "Sterilizace",
        "group_label": "tepelna_konzervace",
        "patterns": [r"\bsteriliz\w*\b"],
    },
    {
        "processing_method_id": "kvaseni",
        "label": "Kvašení / fermentace",
        "group_label": "fermentace",
        "patterns": [r"\bkvasen\w*\b", r"\bferment\w*\b", r"\bperry\b", r"\bcider\b", r"\bkysan\w*\b"],
    },
    {
        "processing_method_id": "ocet",
        "label": "Naložení do octa / ocet",
        "group_label": "fermentace",
        "patterns": [r"\bocet\w*\b", r"\boctov\w*\b", r"\bvinegar\b"],
    },
    {
        "processing_method_id": "olej",
        "label": "Naložení do oleje / olej",
        "group_label": "tuk",
        "patterns": [r"\bv oleji\b", r"\bdo oleje\b", r"\bolejov\w*\b", r"\bmacerat v oleji\b"],
    },
    {
        "processing_method_id": "tinktura",
        "label": "Tinktura / alkoholová macerace",
        "group_label": "alkohol",
        "patterns": [r"\btinktur\w*\b", r"\balkoholov\w*\b", r"\bliker\w*\b", r"\bdestilat\w*\b", r"\blihov\w*\b"],
    },
    {
        "processing_method_id": "cukrovani",
        "label": "Cukrování / kandování / džem",
        "group_label": "sladke_konzervace",
        "patterns": [r"\bkand\w*\b", r"\bcukrov\w*\b", r"\bdzem\w*\b", r"\bmarmelad\w*\b", r"\bzele\b", r"\bpovid\w*\b"],
    },
    {
        "processing_method_id": "kompot",
        "label": "Kompot",
        "group_label": "tepelna_konzervace",
        "patterns": [r"\bkompot\w*\b"],
    },
    {
        "processing_method_id": "nakladani",
        "label": "Nakládání",
        "group_label": "pickles",
        "patterns": [r"\bnaklad\w*\b", r"\bnalozen\w*\b", r"\bpickl\w*\b"],
    },
]

PROCESSING_METHODS_BY_ID = {
    row["processing_method_id"]: row for row in PROCESSING_METHOD_DEFINITIONS
}


def extract_processing_method_ids(*values: str | None) -> list[str]:
    combined = " | ".join(value for value in values if value)
    haystack = normalize_text(combined)
    if not haystack:
        return []

    found: list[str] = []
    for row in PROCESSING_METHOD_DEFINITIONS:
        if any(re.search(pattern, haystack) for pattern in row["patterns"]):
            found.append(row["processing_method_id"])
    return found


def processing_method_labels(method_ids: list[str]) -> list[str]:
    return [
        PROCESSING_METHODS_BY_ID[method_id]["label"]
        for method_id in method_ids
        if method_id in PROCESSING_METHODS_BY_ID
    ]


def processing_methods_text(method_ids: list[str]) -> str | None:
    labels = processing_method_labels(method_ids)
    if not labels:
        return None
    return " · ".join(labels)


def build_processing_method_vocab_rows() -> list[dict[str, str]]:
    rows = []
    for order, row in enumerate(PROCESSING_METHOD_DEFINITIONS, start=1):
        rows.append(
            {
                "processing_method_id": row["processing_method_id"],
                "label": row["label"],
                "group_label": row["group_label"],
                "display_order": order,
            }
        )
    return rows
