from __future__ import annotations

import argparse
import json
import mimetypes
import sqlite3
from datetime import date, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


APP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = APP_DIR.parent
STATIC_DIR = APP_DIR / "static"
MEDIA_DIR = APP_DIR / "media"
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
MONTH_LABELS_GENITIVE = [
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
]
MEDIA_KIND_LABELS = {
    "photo": "Foto",
    "illustration": "Ilustrace",
    "auto_cover": "Auto-cover",
}


def choose_db_path(project_dir: Path) -> Path:
    candidates = list(project_dir.glob("exports/*/v7_canonical/v7_dataset.sqlite"))
    candidates.extend(project_dir.glob("exports/*/v7_canonical/v7_dataset.rebuild*.sqlite"))
    existing = [path for path in candidates if path.exists()]
    if not existing:
        raise FileNotFoundError("No SQLite database found. Run build_v7_sqlite.py first.")
    return max(existing, key=lambda path: path.stat().st_mtime)


def month_match_expression(alias: str = "u") -> str:
    return f"""
            {alias}.mesic_od IS NOT NULL
            AND {alias}.mesic_do IS NOT NULL
            AND (
                ({alias}.mesic_od <= {alias}.mesic_do AND ? BETWEEN {alias}.mesic_od AND {alias}.mesic_do)
                OR
                ({alias}.mesic_od > {alias}.mesic_do AND (? >= {alias}.mesic_od OR ? <= {alias}.mesic_do))
            )
        """


def month_filter_sql(month: int, alias: str = "u") -> tuple[str, list[int]]:
    return (
        f"\n        AND (\n{month_match_expression(alias)}\n        )\n        ",
        [month, month, month],
    )


def month_filter_any_sql(months: list[int], alias: str = "u") -> tuple[str, list[int]]:
    unique_months = list(dict.fromkeys(months))
    if not unique_months:
        return "", []

    clauses = []
    params: list[int] = []
    expression = month_match_expression(alias)
    for month in unique_months:
        clauses.append(f"({expression})")
        params.extend([month, month, month])

    return (
        "\n        AND (\n            " + "\n            OR ".join(clauses) + "\n        )\n        ",
        params,
    )


def wrap_month(month: int) -> int:
    if month < 1:
        return 12
    if month > 12:
        return 1
    return month


def seasonal_window_payload(for_date: date | None = None) -> dict[str, object]:
    today = for_date or datetime.now().astimezone().date()
    current_month = today.month
    previous_month = wrap_month(current_month - 1)
    next_month = wrap_month(current_month + 1)

    if today.day <= 10:
        months = [previous_month, current_month]
        mode = "early_month"
        reason = "začátek měsíce: minulý + aktuální"
    elif today.day >= 22:
        months = [current_month, next_month]
        mode = "late_month"
        reason = "konec měsíce: aktuální + následující"
    else:
        months = [previous_month, current_month, next_month]
        mode = "mid_month"
        reason = "střed měsíce: minulý + aktuální + následující"

    month_labels = [MONTH_LABELS[month] for month in months]
    return {
        "enabled_by_default": True,
        "today_iso": today.isoformat(),
        "today_label": f"{today.day}. {MONTH_LABELS_GENITIVE[today.month]} {today.year}",
        "months": months,
        "month_labels": month_labels,
        "label": " + ".join(month_labels),
        "mode": mode,
        "reason": reason,
    }


def load_media_manifest() -> dict[str, list[dict[str, str]]]:
    manifest_path = MEDIA_DIR / "plant_media.json"
    if not manifest_path.exists():
        return {}
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def infer_media_kind(entry: dict[str, str]) -> str:
    explicit = str(entry.get("media_kind", "")).strip().lower()
    if explicit in MEDIA_KIND_LABELS:
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


def normalize_media_entries(entries: list[dict[str, str]] | object) -> list[dict[str, str]]:
    if not isinstance(entries, list):
        return []

    normalized = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        src = str(entry.get("src", "")).strip()
        if not src:
            continue
        if src.startswith(("http://", "https://", "/media/")):
            public_src = src
        else:
            public_src = f"/media/{src.replace('\\', '/')}"
        media_kind = infer_media_kind(entry)
        normalized.append(
            {
                "src": public_src,
                "alt": str(entry.get("alt", "")).strip(),
                "caption": str(entry.get("caption", "")).strip(),
                "credit": str(entry.get("credit", "")).strip(),
                "source_name": str(entry.get("source_name", "")).strip(),
                "source_url": str(entry.get("source_url", "")).strip(),
                "license": str(entry.get("license", "")).strip(),
                "media_kind": media_kind,
                "media_kind_label": MEDIA_KIND_LABELS.get(media_kind, media_kind),
            }
        )
    return normalized


def resolve_media_entries(plant_id: str) -> list[dict[str, str]]:
    manifest = load_media_manifest()
    return normalize_media_entries(manifest.get(plant_id, []))


def photo_entries_only(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    return [entry for entry in entries if entry.get("media_kind") == "photo"]


def attach_photo_metadata(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    manifest = load_media_manifest()
    for row in rows:
        plant_id = str(row.get("plant_id") or "").strip()
        media_entries = normalize_media_entries(manifest.get(plant_id, [])) if plant_id else []
        photo_entries = photo_entries_only(media_entries)
        primary_photo = photo_entries[0] if photo_entries else None
        row["photos"] = photo_entries
        row["primary_photo"] = primary_photo["src"] if primary_photo else None
        row["primary_photo_alt"] = primary_photo["alt"] if primary_photo else None
        row["primary_photo_credit"] = primary_photo["credit"] if primary_photo else None
        row["primary_photo_source_name"] = primary_photo["source_name"] if primary_photo else None
        row["primary_photo_source_url"] = primary_photo["source_url"] if primary_photo else None
        row["primary_photo_kind"] = primary_photo["media_kind"] if primary_photo else None
        row["primary_photo_kind_label"] = primary_photo["media_kind_label"] if primary_photo else None
    return rows


def processing_methods_for_use(conn: sqlite3.Connection, use_id: str) -> list[dict[str, str]]:
    rows = conn.execute(
        """
        SELECT
            upm.processing_method_id,
            vpm.label,
            vpm.group_label,
            upm.method_order
        FROM use_processing_methods upm
        JOIN vocab_processing_methods vpm ON vpm.processing_method_id = upm.processing_method_id
        WHERE upm.use_id = ?
        ORDER BY upm.method_order ASC, vpm.display_order ASC, vpm.label ASC
        """,
        (use_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def render_use_markdown(detail: dict) -> str:
    lines = [
        f"# {detail['raw_record_id']} · {detail['cesky_nazev_hlavni']}",
        "",
        f"- Vědecký název: {detail['vedecky_nazev_hlavni']}",
        f"- Doména: {detail['domena']}",
        f"- Poddoména: {detail['poddomena_text']}",
        f"- Část rostliny: {detail['cast_rostliny_text']}",
        f"- Období: {detail.get('obdobi_ziskani_text') or 'neuvedeno'}",
        f"- Důkaznost: {detail['dukaznost_skore']}",
        f"- Aplikovatelnost v ČR: {detail.get('aplikovatelnost_v_cr') or 'neuvedeno'}",
    ]
    if detail.get("processing_methods_text"):
        lines.append(f"- Metody dlouhodobého zpracování: {detail['processing_methods_text']}")
    if detail.get("forma_uchovani_text"):
        lines.extend(
            [
                f"- Forma uchování: {detail['forma_uchovani_text']}",
                f"- Orientační trvanlivost: {detail.get('orientacni_trvanlivost_text') or 'neuvedeno'}",
            ]
        )

    lines.extend(
        [
            "",
            "## Praktický popis",
            "",
            detail.get("zpusob_pripravy") or "Bez popisu přípravy.",
            "",
            "## Cílový efekt",
            "",
            detail.get("cilovy_efekt") or "Bez popisu.",
            "",
            "## Jak sbírat správně",
            "",
            detail.get("sber_doporuceni") or "Bez odvozeného doporučení ke sběru.",
            "",
            "## Sběr a lokalita",
            "",
            f"- Fenologie: {detail.get('fenologicka_faze') or 'neuvedeno'}",
            f"- Lokality: {detail.get('typicke_lokality_text') or 'neuvedeno'}",
            "",
            "## Rizika a legalita",
            "",
            f"- Rizika: {detail.get('hlavni_rizika') or 'neuvedeno'}",
            f"- Kontraindikace: {detail.get('kontraindikace_interakce') or 'neuvedeno'}",
            f"- Právo a sběr: {detail.get('legalita_poznamka_cr') or 'neuvedeno'}",
            "",
            "## Metody zpracování",
            "",
        ]
    )

    if detail.get("processing_methods"):
        for method in detail["processing_methods"]:
            lines.append(f"- {method['label']}")
    else:
        lines.append("- Neuvedeno")

    lines.extend(["", "## Aliasy", ""])
    for alias in detail.get("aliases", []):
        lines.append(f"- {alias['alias']} ({alias['jazyk']}, {alias['typ_aliasu']})")

    lines.extend(["", "## Zdroje", ""])
    for source in detail.get("sources", []):
        lines.append(f"- {source['raw_source_id']} · {source['nazev']} · {source['url']}")

    if detail.get("photos"):
        lines.extend(["", "## Fotky", ""])
        for photo in detail["photos"]:
            extras = [photo.get("media_kind_label") or photo.get("media_kind") or "media"]
            if photo.get("credit"):
                extras.append(photo["credit"])
            if photo.get("license"):
                extras.append(photo["license"])
            if photo.get("source_url"):
                extras.append(photo["source_url"])
            lines.append(f"- {photo['src']} ({' | '.join(extras)})")

    return "\n".join(lines) + "\n"


def render_plant_markdown(detail: dict) -> str:
    lines = [
        f"# {detail['cesky_nazev_hlavni']}",
        "",
        f"- Plant ID: {detail['plant_id']}",
        f"- Vědecký název: {detail['vedecky_nazev_hlavni']}",
        f"- Status v ČR: {detail.get('status_v_cr_text') or 'neuvedeno'}",
        f"- Počet použití: {detail['stats']['use_count']}",
        f"- Trvanlivá použití: {detail['stats']['durable_use_count']}",
        f"- Jádrová použití: {detail['stats']['core_use_count']}",
        "",
        "## Aliasy",
        "",
    ]
    for alias in detail.get("aliases", []):
        lines.append(f"- {alias['alias']} ({alias['jazyk']}, {alias['typ_aliasu']})")

    lines.extend(["", "## Použití", ""])
    for use in detail.get("uses", []):
        lines.extend(
            [
                f"### {use['raw_record_id']} · {use['poddomena_text']}",
                "",
                f"- Doména: {use['domena']}",
                f"- Část rostliny: {use['cast_rostliny_text']}",
                f"- Období: {use.get('obdobi_ziskani_text') or 'neuvedeno'}",
                f"- Důkaznost: {use['dukaznost_skore']}",
                f"- Aplikovatelnost v ČR: {use.get('aplikovatelnost_v_cr') or 'neuvedeno'}",
                f"- Cílový efekt: {use.get('cilovy_efekt') or 'neuvedeno'}",
                f"- Metody zpracování: {use.get('processing_methods_text') or 'neuvedeno'}",
                f"- Jak sbírat správně: {use.get('sber_doporuceni') or 'neuvedeno'}",
                "",
            ]
        )

    lines.extend(["## Zdroje napříč rostlinou", ""])
    for source in detail.get("sources", []):
        lines.append(f"- {source['raw_source_id']} · {source['nazev']} · {source['url']} ({source['use_count']} použití)")

    if detail.get("photos"):
        lines.extend(["", "## Fotky", ""])
        for photo in detail["photos"]:
            extras = [photo.get("media_kind_label") or photo.get("media_kind") or "media"]
            if photo.get("credit"):
                extras.append(photo["credit"])
            if photo.get("license"):
                extras.append(photo["license"])
            if photo.get("source_url"):
                extras.append(photo["source_url"])
            lines.append(f"- {photo['src']} ({' | '.join(extras)})")

    return "\n".join(lines) + "\n"


class CatalogHandler(BaseHTTPRequestHandler):
    db_path: Path | None = None
    static_dir: Path = STATIC_DIR

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path in {"/", "/index.html"}:
            self.serve_static_file(self.static_dir / "index.html")
            return

        if path in {"/plants", "/plants/", "/plants.html"}:
            self.serve_static_file(self.static_dir / "plants.html")
            return

        if path in {"/detail.html", "/detail"}:
            self.serve_static_file(self.static_dir / "detail.html")
            return

        if path.startswith("/plant/") or path.startswith("/use/"):
            self.serve_static_file(self.static_dir / "detail.html")
            return

        if path.startswith("/export/use/"):
            self.handle_export_use(path)
            return

        if path.startswith("/export/plant/"):
            self.handle_export_plant(path)
            return

        if path.startswith("/static/"):
            relative = path.removeprefix("/static/")
            file_path = (self.static_dir / relative).resolve()
            static_root = self.static_dir.resolve()
            if not str(file_path).startswith(str(static_root)) or not file_path.exists():
                self.send_error(HTTPStatus.NOT_FOUND, "Static file not found.")
                return
            self.serve_static_file(file_path)
            return

        if path.startswith("/media/"):
            relative = path.removeprefix("/media/")
            file_path = (MEDIA_DIR / relative).resolve()
            media_root = MEDIA_DIR.resolve()
            if not str(file_path).startswith(str(media_root)) or not file_path.exists():
                self.send_error(HTTPStatus.NOT_FOUND, "Media file not found.")
                return
            self.serve_static_file(file_path)
            return

        if path == "/api/summary":
            self.handle_summary()
            return

        if path == "/api/options":
            self.handle_options()
            return

        if path == "/api/plants":
            self.handle_plants_index(parsed)
            return

        if path == "/api/search":
            self.handle_search(parsed)
            return

        if path == "/api/use":
            self.handle_use_detail(parsed)
            return

        if path == "/api/plant":
            self.handle_plant_detail(parsed)
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Route not found.")

    def serve_static_file(self, file_path: Path) -> None:
        content_type, _ = mimetypes.guess_type(str(file_path))
        if not content_type:
            content_type = "application/octet-stream"
        if file_path.suffix in {".html", ".css", ".js"}:
            content_type = f"{content_type}; charset=utf-8"

        data = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def json_response(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_bytes_response(body, "application/json; charset=utf-8", status=status)

    def send_bytes_response(
        self,
        body: bytes,
        content_type: str,
        *,
        status: int = 200,
        filename: str | None = None,
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(body)

    @classmethod
    def current_db_path(cls) -> Path:
        return cls.db_path.resolve() if cls.db_path is not None else choose_db_path(PROJECT_DIR)

    def get_db(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.current_db_path())
        connection.row_factory = sqlite3.Row
        return connection

    def handle_summary(self) -> None:
        current_db_path = self.current_db_path()
        with self.get_db() as conn:
            payload = {
                "db_path": str(current_db_path),
                "counts": {
                    "plants": conn.execute("SELECT COUNT(*) FROM plants").fetchone()[0],
                    "uses": conn.execute("SELECT COUNT(*) FROM uses").fetchone()[0],
                    "durable_forms": conn.execute("SELECT COUNT(*) FROM durable_forms").fetchone()[0],
                    "sources": conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0],
                    "core_items": conn.execute("SELECT COUNT(*) FROM durable_forms WHERE is_core_item = 1").fetchone()[0],
                    "processing_method_links": conn.execute("SELECT COUNT(*) FROM use_processing_methods").fetchone()[0],
                },
                "domain_counts": [
                    dict(row)
                    for row in conn.execute(
                        """
                        SELECT domena, COUNT(*) AS count
                        FROM uses
                        GROUP BY domena
                        ORDER BY count DESC, domena
                        """
                    )
                ],
            }
        self.json_response(payload)

    def handle_options(self) -> None:
        seasonal_default = seasonal_window_payload()
        with self.get_db() as conn:
            payload = {
                "domains": [row["domena"] for row in conn.execute("SELECT DISTINCT domena FROM uses ORDER BY domena")],
                "part_categories": [
                    row["part_category_id"]
                    for row in conn.execute("SELECT part_category_id FROM vocab_part_categories ORDER BY part_category_id")
                ],
                "subdomain_categories": [
                    row["subdomain_category_id"]
                    for row in conn.execute("SELECT subdomain_category_id FROM vocab_subdomain_categories ORDER BY subdomain_category_id")
                ],
                "processing_methods": [
                    {"value": row["processing_method_id"], "label": row["label"]}
                    for row in conn.execute(
                        "SELECT processing_method_id, label FROM vocab_processing_methods ORDER BY display_order ASC, label ASC"
                    )
                ],
                "evidence_scores": [
                    row["dukaznost_skore"]
                    for row in conn.execute("SELECT DISTINCT dukaznost_skore FROM uses ORDER BY dukaznost_rank DESC")
                ],
                "months": [{"value": index, "label": label} for index, label in enumerate(MONTH_LABELS) if index],
                "seasonal_default": seasonal_default,
            }
        self.json_response(payload)

    def handle_plants_index(self, parsed) -> None:
        params = parse_qs(parsed.query)
        query_text = params.get("q", [""])[0].strip().lower()
        durable_only = params.get("trvanlive", ["0"])[0] == "1"
        core_only = params.get("jadro", ["0"])[0] == "1"
        month_value = params.get("month", [""])[0].strip()
        seasonal_requested = params.get("seasonal", ["0"])[0] == "1" and not month_value
        seasonal_default = seasonal_window_payload()
        limit = min(max(int(params.get("limit", ["120"])[0]), 1), 300)

        sql = """
            SELECT
                p.plant_id,
                p.cesky_nazev_hlavni,
                p.vedecky_nazev_hlavni,
                p.status_v_cr_text,
                p.status_cetnost_reprezentativni,
                p.pocet_pouziti,
                p.pocet_ceskych_aliasu,
                COUNT(u.use_id) AS use_count,
                SUM(CASE WHEN u.je_trvanlive_1m_plus = 1 THEN 1 ELSE 0 END) AS durable_use_count,
                SUM(CASE WHEN u.je_v_jadru_bezne_1m_plus = 1 THEN 1 ELSE 0 END) AS core_use_count,
                MAX(u.dukaznost_rank) AS top_evidence_rank,
                SUM(CASE WHEN u.ma_potravinove_konzervacni_metody = 1 THEN 1 ELSE 0 END) AS processing_use_count
            FROM plants p
            JOIN uses u ON u.plant_id = p.plant_id
            WHERE 1 = 1
        """
        sql_params: list[object] = []

        if query_text:
            sql += """
                AND (
                    lower(p.cesky_nazev_hlavni) LIKE ?
                    OR lower(p.vedecky_nazev_hlavni) LIKE ?
                    OR EXISTS (
                        SELECT 1
                        FROM plant_aliases pa
                        WHERE pa.plant_id = p.plant_id
                          AND lower(pa.alias) LIKE ?
                    )
                )
            """
            like_term = f"%{query_text}%"
            sql_params.extend([like_term, like_term, like_term])

        if month_value:
            month = int(month_value)
            month_clause, month_params = month_filter_sql(month, alias="u")
            sql += month_clause
            sql_params.extend(month_params)
        elif seasonal_requested:
            month_clause, month_params = month_filter_any_sql(list(seasonal_default["months"]), alias="u")
            sql += month_clause
            sql_params.extend(month_params)

        sql += " GROUP BY p.plant_id, p.cesky_nazev_hlavni, p.vedecky_nazev_hlavni, p.status_v_cr_text, p.status_cetnost_reprezentativni, p.pocet_pouziti, p.pocet_ceskych_aliasu"

        having_clauses = []
        if durable_only:
            having_clauses.append("SUM(CASE WHEN u.je_trvanlive_1m_plus = 1 THEN 1 ELSE 0 END) > 0")
        if core_only:
            having_clauses.append("SUM(CASE WHEN u.je_v_jadru_bezne_1m_plus = 1 THEN 1 ELSE 0 END) > 0")
        if having_clauses:
            sql += " HAVING " + " AND ".join(having_clauses)

        sql += """
            ORDER BY
                core_use_count DESC,
                durable_use_count DESC,
                processing_use_count DESC,
                top_evidence_rank DESC,
                p.cesky_nazev_hlavni ASC
            LIMIT ?
        """
        sql_params.append(limit)

        with self.get_db() as conn:
            rows = [dict(row) for row in conn.execute(sql, sql_params).fetchall()]

        attach_photo_metadata(rows)

        self.json_response(
            {
                "count": len(rows),
                "results": rows,
                "seasonal_applied": seasonal_requested and not month_value,
                "seasonal_window": seasonal_default if seasonal_requested and not month_value else None,
            }
        )

    def handle_search(self, parsed) -> None:
        params = parse_qs(parsed.query)
        query_text = params.get("q", [""])[0].strip().lower()
        domain = params.get("domena", [""])[0].strip()
        durable = params.get("trvanlive", ["0"])[0] == "1"
        core_only = params.get("jadro", ["0"])[0] == "1"
        part_category = params.get("part_category", [""])[0].strip()
        subdomain_category = params.get("subdomain_category", [""])[0].strip()
        processing_method = params.get("processing_method", [""])[0].strip()
        evidence_min = params.get("evidence_min", [""])[0].strip()
        month_value = params.get("month", [""])[0].strip()
        seasonal_requested = params.get("seasonal", ["0"])[0] == "1" and not month_value
        seasonal_default = seasonal_window_payload()
        limit = min(max(int(params.get("limit", ["60"])[0]), 1), 200)

        sql = """
            SELECT
                u.use_id,
                u.raw_record_id,
                p.plant_id,
                p.cesky_nazev_hlavni,
                p.vedecky_nazev_hlavni,
                u.cesky_nazev_display,
                u.domena,
                u.poddomena_text,
                u.poddomena_kategorie,
                u.cast_rostliny_text,
                u.cast_rostliny_kategorie,
                u.typicke_lokality_text,
                u.obdobi_ziskani_text,
                u.mesic_od,
                u.mesic_do,
                u.cilovy_efekt,
                u.sber_doporuceni,
                u.hlavni_rizika,
                u.legalita_poznamka_cr,
                u.dukaznost_skore,
                u.dukaznost_rank,
                u.status_znalosti,
                u.aplikovatelnost_v_cr,
                u.je_trvanlive_1m_plus,
                u.je_v_jadru_bezne_1m_plus,
                u.processing_methods_text,
                u.processing_methods_count,
                d.forma_uchovani_text,
                d.orientacni_trvanlivost_text,
                d.proc_je_v_jadru
            FROM uses u
            JOIN plants p ON p.plant_id = u.plant_id
            LEFT JOIN durable_forms d ON d.use_id = u.use_id
            WHERE 1 = 1
        """
        sql_params: list[object] = []

        if query_text:
            sql += """
                AND (
                    lower(p.cesky_nazev_hlavni) LIKE ?
                    OR lower(p.vedecky_nazev_hlavni) LIKE ?
                    OR lower(u.cesky_nazev_display) LIKE ?
                    OR lower(u.poddomena_text) LIKE ?
                    OR lower(u.cast_rostliny_text) LIKE ?
                    OR lower(u.cilovy_efekt) LIKE ?
                    OR lower(COALESCE(u.processing_methods_text, '')) LIKE ?
                )
            """
            like_term = f"%{query_text}%"
            sql_params.extend([like_term] * 7)

        if domain:
            sql += " AND u.domena = ?"
            sql_params.append(domain)

        if durable:
            sql += " AND u.je_trvanlive_1m_plus = 1"

        if core_only:
            sql += " AND u.je_v_jadru_bezne_1m_plus = 1"

        if part_category:
            sql += " AND u.cast_rostliny_kategorie = ?"
            sql_params.append(part_category)

        if subdomain_category:
            sql += " AND u.poddomena_kategorie = ?"
            sql_params.append(subdomain_category)

        if processing_method:
            sql += """
                AND EXISTS (
                    SELECT 1
                    FROM use_processing_methods upm
                    WHERE upm.use_id = u.use_id
                      AND upm.processing_method_id = ?
                )
            """
            sql_params.append(processing_method)

        if evidence_min:
            rank_map = {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1}
            threshold = rank_map.get(evidence_min)
            if threshold is not None:
                sql += " AND u.dukaznost_rank >= ?"
                sql_params.append(threshold)

        if month_value:
            month = int(month_value)
            month_clause, month_params = month_filter_sql(month, alias="u")
            sql += month_clause
            sql_params.extend(month_params)
        elif seasonal_requested:
            month_clause, month_params = month_filter_any_sql(list(seasonal_default["months"]), alias="u")
            sql += month_clause
            sql_params.extend(month_params)

        sql += """
            ORDER BY
                u.je_v_jadru_bezne_1m_plus DESC,
                u.je_trvanlive_1m_plus DESC,
                u.processing_methods_count DESC,
                u.dukaznost_rank DESC,
                p.cesky_nazev_hlavni ASC,
                u.poddomena_text ASC
            LIMIT ?
        """
        sql_params.append(limit)

        with self.get_db() as conn:
            rows = [dict(row) for row in conn.execute(sql, sql_params).fetchall()]

        attach_photo_metadata(rows)
        self.json_response(
            {
                "count": len(rows),
                "results": rows,
                "seasonal_applied": seasonal_requested and not month_value,
                "seasonal_window": seasonal_default if seasonal_requested and not month_value else None,
            }
        )

    def build_use_detail(self, conn: sqlite3.Connection, use_id: str) -> dict | None:
        row = conn.execute(
            """
            SELECT
                u.*,
                p.vedecky_nazev_hlavni,
                p.cesky_nazev_hlavni,
                p.plant_id,
                d.forma_uchovani_text,
                d.orientacni_trvanlivost_text,
                d.poznamka_k_skladovani,
                d.proc_je_v_jadru
            FROM uses u
            JOIN plants p ON p.plant_id = u.plant_id
            LEFT JOIN durable_forms d ON d.use_id = u.use_id
            WHERE u.use_id = ?
            """,
            (use_id,),
        ).fetchone()

        if row is None:
            return None

        aliases = [
            dict(alias_row)
            for alias_row in conn.execute(
                """
                SELECT alias, jazyk, typ_aliasu, je_preferovany, pocet_vyskytu
                FROM plant_aliases
                WHERE plant_id = ?
                ORDER BY jazyk, je_preferovany DESC, alias
                """,
                (row["plant_id"],),
            ).fetchall()
        ]
        sources = [
            dict(source_row)
            for source_row in conn.execute(
                """
                SELECT
                    us.role_zdroje,
                    us.poradi,
                    s.raw_source_id,
                    s.nazev,
                    s.url,
                    s.source_family,
                    s.poznamka
                FROM use_sources us
                JOIN sources s ON s.source_id = us.source_id
                WHERE us.use_id = ?
                ORDER BY us.poradi ASC, s.raw_source_id ASC
                """,
                (use_id,),
            ).fetchall()
        ]

        payload = dict(row)
        payload["aliases"] = aliases
        payload["sources"] = sources
        payload["photos"] = photo_entries_only(resolve_media_entries(row["plant_id"]))
        payload["processing_methods"] = processing_methods_for_use(conn, use_id)
        return payload

    def build_plant_detail(self, conn: sqlite3.Connection, plant_id: str) -> dict | None:
        plant_row = conn.execute(
            """
            SELECT *
            FROM plants
            WHERE plant_id = ?
            """,
            (plant_id,),
        ).fetchone()

        if plant_row is None:
            return None

        aliases = [
            dict(alias_row)
            for alias_row in conn.execute(
                """
                SELECT alias, jazyk, typ_aliasu, je_preferovany, pocet_vyskytu
                FROM plant_aliases
                WHERE plant_id = ?
                ORDER BY jazyk, je_preferovany DESC, alias
                """,
                (plant_id,),
            ).fetchall()
        ]

        uses = [
            dict(use_row)
            for use_row in conn.execute(
                """
                SELECT
                    u.use_id,
                    u.raw_record_id,
                    u.domena,
                    u.poddomena_text,
                    u.poddomena_kategorie,
                    u.cast_rostliny_text,
                    u.cast_rostliny_kategorie,
                    u.obdobi_ziskani_text,
                    u.cilovy_efekt,
                    u.dukaznost_skore,
                    u.dukaznost_rank,
                    u.status_znalosti,
                    u.aplikovatelnost_v_cr,
                    u.je_trvanlive_1m_plus,
                    u.je_v_jadru_bezne_1m_plus,
                    u.processing_methods_text,
                    u.processing_methods_count,
                    u.sber_doporuceni,
                    d.forma_uchovani_text,
                    d.orientacni_trvanlivost_text
                FROM uses u
                LEFT JOIN durable_forms d ON d.use_id = u.use_id
                WHERE u.plant_id = ?
                ORDER BY
                    u.je_v_jadru_bezne_1m_plus DESC,
                    u.je_trvanlive_1m_plus DESC,
                    u.processing_methods_count DESC,
                    u.dukaznost_rank DESC,
                    u.domena ASC,
                    u.poddomena_text ASC
                """,
                (plant_id,),
            ).fetchall()
        ]

        source_rows = [
            dict(source_row)
            for source_row in conn.execute(
                """
                SELECT
                    s.raw_source_id,
                    s.nazev,
                    s.url,
                    s.source_family,
                    COUNT(*) AS use_count
                FROM use_sources us
                JOIN uses u ON u.use_id = us.use_id
                JOIN sources s ON s.source_id = us.source_id
                WHERE u.plant_id = ?
                GROUP BY s.raw_source_id, s.nazev, s.url, s.source_family
                ORDER BY use_count DESC, s.raw_source_id ASC
                """,
                (plant_id,),
            ).fetchall()
        ]

        payload = dict(plant_row)
        payload["aliases"] = aliases
        payload["uses"] = uses
        payload["sources"] = source_rows
        payload["photos"] = photo_entries_only(resolve_media_entries(plant_id))
        payload["stats"] = {
            "use_count": len(uses),
            "durable_use_count": sum(1 for use in uses if use["je_trvanlive_1m_plus"]),
            "core_use_count": sum(1 for use in uses if use["je_v_jadru_bezne_1m_plus"]),
            "processing_use_count": sum(1 for use in uses if use.get("processing_methods_count")),
            "top_evidence_rank": max((use["dukaznost_rank"] for use in uses), default=None),
        }
        return payload

    def handle_use_detail(self, parsed) -> None:
        params = parse_qs(parsed.query)
        use_id = params.get("use_id", [""])[0].strip().lower()
        if not use_id:
            self.json_response({"error": "Missing use_id parameter."}, status=400)
            return

        with self.get_db() as conn:
            payload = self.build_use_detail(conn, use_id)

        if payload is None:
            self.json_response({"error": "Use not found."}, status=404)
            return

        self.json_response(payload)

    def handle_plant_detail(self, parsed) -> None:
        params = parse_qs(parsed.query)
        plant_id = params.get("plant_id", [""])[0].strip()
        if not plant_id:
            self.json_response({"error": "Missing plant_id parameter."}, status=400)
            return

        with self.get_db() as conn:
            payload = self.build_plant_detail(conn, plant_id)

        if payload is None:
            self.json_response({"error": "Plant not found."}, status=404)
            return

        self.json_response(payload)

    def handle_export_use(self, path: str) -> None:
        tail = path.removeprefix("/export/use/")
        if "." not in tail:
            self.send_error(HTTPStatus.BAD_REQUEST, "Missing export extension.")
            return
        use_id, ext = tail.rsplit(".", 1)
        use_id = use_id.strip().lower()
        ext = ext.strip().lower()

        with self.get_db() as conn:
            payload = self.build_use_detail(conn, use_id)

        if payload is None:
            self.send_error(HTTPStatus.NOT_FOUND, "Use not found.")
            return

        if ext == "json":
            body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_bytes_response(body, "application/json; charset=utf-8", filename=f"use_{use_id}.json")
            return
        if ext == "md":
            body = render_use_markdown(payload).encode("utf-8")
            self.send_bytes_response(body, "text/markdown; charset=utf-8", filename=f"use_{use_id}.md")
            return

        self.send_error(HTTPStatus.BAD_REQUEST, "Unsupported export format.")

    def handle_export_plant(self, path: str) -> None:
        tail = path.removeprefix("/export/plant/")
        if "." not in tail:
            self.send_error(HTTPStatus.BAD_REQUEST, "Missing export extension.")
            return
        plant_id, ext = tail.rsplit(".", 1)
        plant_id = plant_id.strip()
        ext = ext.strip().lower()

        with self.get_db() as conn:
            payload = self.build_plant_detail(conn, plant_id)

        if payload is None:
            self.send_error(HTTPStatus.NOT_FOUND, "Plant not found.")
            return

        if ext == "json":
            body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_bytes_response(body, "application/json; charset=utf-8", filename=f"{plant_id}.json")
            return
        if ext == "md":
            body = render_plant_markdown(payload).encode("utf-8")
            self.send_bytes_response(body, "text/markdown; charset=utf-8", filename=f"{plant_id}.md")
            return

        self.send_error(HTTPStatus.BAD_REQUEST, "Unsupported export format.")

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="Local Czech plants catalog server.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host. Default: 127.0.0.1")
    parser.add_argument("--port", type=int, default=8765, help="Bind port. Default: 8765")
    parser.add_argument("--db", type=Path, default=None, help="Optional path to v7_dataset.sqlite")
    args = parser.parse_args()

    if args.db is not None:
        CatalogHandler.db_path = args.db.resolve()

    server = ThreadingHTTPServer((args.host, args.port), CatalogHandler)
    print(f"Catalog server running on http://{args.host}:{args.port}")
    print(f"Using database: {CatalogHandler.current_db_path()}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
