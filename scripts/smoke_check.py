from __future__ import annotations

import argparse
import dataclasses
import json
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import urlopen


@dataclasses.dataclass
class FetchResult:
    url: str
    status: int
    content_type: str
    charset: str
    body: bytes

    @property
    def text(self) -> str:
        return self.body.decode(self.charset, errors="replace")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run smoke checks against the Czech plants project.")
    parser.add_argument("--db", type=Path, default=None, help="Optional path to SQLite database.")
    parser.add_argument("--host", default="127.0.0.1", help="Host for temporary local server.")
    parser.add_argument("--port", type=int, default=8780, help="Port for temporary local server.")
    parser.add_argument("--startup-wait", type=float, default=2.5, help="Seconds to wait before probing the server.")
    return parser.parse_args()


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def choose_default_db(root: Path) -> Path:
    matches = [path for path in root.glob("exports/*/v7_canonical/*.sqlite") if path.exists()]
    if not matches:
        raise FileNotFoundError("No SQLite database found for smoke checks.")
    return max(matches, key=lambda path: path.stat().st_mtime)


def fetch_url(url: str) -> FetchResult:
    try:
        with urlopen(url) as response:
            body = response.read()
            return FetchResult(
                url=url,
                status=getattr(response, "status", 200),
                content_type=response.headers.get_content_type(),
                charset=response.headers.get_content_charset() or "utf-8",
                body=body,
            )
    except HTTPError as error:
        body = error.read()
        return FetchResult(
            url=url,
            status=error.code,
            content_type=error.headers.get_content_type() if error.headers else "application/octet-stream",
            charset=error.headers.get_content_charset() if error.headers else "utf-8",
            body=body,
        )


def read_text_url(url: str) -> tuple[str, FetchResult]:
    result = fetch_url(url)
    return result.text, result


def parse_json_result(result: FetchResult, label: str) -> dict:
    try:
        payload = json.loads(result.text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{label} did not return valid JSON.") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"{label} did not return a JSON object.")
    return payload


def read_json_url(url: str) -> dict:
    result = fetch_url(url)
    require(result.status == 200, f"{url} returned unexpected status {result.status}.")
    return parse_json_result(result, url)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def require_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise RuntimeError(f"{label} is missing `{needle}`.")


def month_matches_range(month: int, start: int | None, end: int | None) -> bool:
    if start is None or end is None:
        return False
    if start <= end:
        return start <= month <= end
    return month >= start or month <= end


def wait_for_server(base_url: str, timeout_seconds: float) -> None:
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            read_json_url(f"{base_url}/api/summary")
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(0.25)
    if last_error:
        raise RuntimeError(f"Server did not start in time: {last_error}") from last_error
    raise RuntimeError("Server did not start in time.")


def run_sqlite_checks(db_path: Path) -> dict[str, int]:
    conn = sqlite3.connect(db_path)
    try:
        counts = {
            "plants": conn.execute("SELECT COUNT(*) FROM plants").fetchone()[0],
            "uses": conn.execute("SELECT COUNT(*) FROM uses").fetchone()[0],
            "durable_forms": conn.execute("SELECT COUNT(*) FROM durable_forms").fetchone()[0],
            "sources": conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0],
            "views": conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type = 'view'").fetchone()[0],
        }
    finally:
        conn.close()

    require(counts["plants"] > 0 and counts["uses"] > 0, f"SQLite counts look invalid: {counts}")
    require(counts["views"] >= 2, f"Expected at least 2 SQLite views, got {counts['views']}")
    return counts


PHOTO_TEST_PLANT_ID = "plant_allium_ursinum"


def run_server_checks(root: Path, db_path: Path, host: str, port: int, startup_wait: float) -> dict[str, object]:
    server_script = root / "app" / "catalog_server.py"
    command = [sys.executable, str(server_script), "--host", host, "--port", str(port), "--db", str(db_path)]
    process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    base_url = f"http://{host}:{port}"
    try:
        wait_for_server(base_url, startup_wait + 5)
        summary = read_json_url(f"{base_url}/api/summary")
        options = read_json_url(f"{base_url}/api/options")
        search = read_json_url(f"{base_url}/api/search?q=bez&limit=2")
        plants = read_json_url(f"{base_url}/api/plants?limit=20")
        seasonal_search = read_json_url(f"{base_url}/api/search?seasonal=1&limit=10")
        seasonal_plants = read_json_url(f"{base_url}/api/plants?seasonal=1&limit=10")
        use_detail = read_json_url(f"{base_url}/api/use?use_id={quote('r001')}")
        functional_plant_detail = read_json_url(
            f"{base_url}/api/plant?plant_id={quote(str(use_detail.get('plant_id') or ''))}"
        )
        plant_detail = read_json_url(f"{base_url}/api/plant?plant_id={quote(PHOTO_TEST_PLANT_ID)}")
        compounds_search = read_json_url(f"{base_url}/api/search?q={quote('flavonoidy')}&limit=10")
        durable_search = read_json_url(f"{base_url}/api/search?trvanlive=1&limit=10")
        core_search = read_json_url(f"{base_url}/api/search?jadro=1&limit=10")
        durable_plants = read_json_url(f"{base_url}/api/plants?trvanlive=1&limit=10")
        core_plants = read_json_url(f"{base_url}/api/plants?jadro=1&limit=10")

        evidence_target = "B" if "B" in options.get("evidence_scores", []) else options["evidence_scores"][0]
        evidence_rank_threshold = {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1}[evidence_target]
        evidence_search = read_json_url(f"{base_url}/api/search?evidence_min={quote(evidence_target)}&limit=10")

        domain_target = options["domains"][0]
        domain_search = read_json_url(f"{base_url}/api/search?domena={quote(domain_target)}&limit=10")

        processing_method_target = options["processing_methods"][0]["value"]
        processing_method_label = options["processing_methods"][0]["label"]
        processing_method_search = read_json_url(
            f"{base_url}/api/search?processing_method={quote(processing_method_target)}&limit=10"
        )

        month_target = None
        month_search = None
        for candidate_month in [1, 6, 9, 12]:
            candidate_result = read_json_url(f"{base_url}/api/search?month={candidate_month}&limit=10")
            if candidate_result["count"] > 0:
                month_target = candidate_month
                month_search = candidate_result
                break
        require(month_target is not None and month_search is not None, "Month filter returned no results for tested months.")

        require(summary["counts"]["plants"] > 0 and summary["counts"]["uses"] > 0, f"API summary looks invalid: {summary}")
        require(len(options.get("domains", [])) > 0, "Options endpoint returned no domains.")
        require(len(options.get("evidence_scores", [])) > 0, "Options endpoint returned no evidence scores.")
        require(len(options.get("months", [])) == 12, "Options endpoint should expose 12 months.")
        require(len(options.get("processing_methods", [])) > 0, "Options endpoint returned no processing methods.")
        require(bool(options.get("seasonal_default")), "Options endpoint returned no seasonal default payload.")
        require(bool(options["seasonal_default"].get("months")), "Seasonal default payload does not expose months.")
        require(search["count"] > 0, "Search endpoint returned no results for `bez`.")
        require(plants["count"] > 0, "Plant index returned no results.")
        require(seasonal_search["count"] > 0, "Seasonal search returned no results.")
        require(seasonal_plants["count"] > 0, "Seasonal plant index returned no results.")
        require(search["results"][0].get("primary_photo"), "Search results do not expose primary_photo on main cards.")
        require(bool(search["results"][0].get("hlavni_prinos_text")), "Search results do not expose benefit summary.")
        require("zpusob_pripravy" in search["results"][0], "Search results do not expose usage method field.")
        require(seasonal_search.get("seasonal_applied") is True, "Seasonal search did not report applied seasonal window.")
        require(seasonal_plants.get("seasonal_applied") is True, "Seasonal plant index did not report applied seasonal window.")
        gallery_photo_row = next((row for row in plants["results"] if row.get("primary_photo_kind_label")), None)
        require(bool(gallery_photo_row), "Plant index does not expose media provenance label.")
        require(use_detail.get("use_id") == "r001", "Use detail returned unexpected use_id.")
        require(bool(use_detail.get("aliases")), "Use detail returned no aliases.")
        require(bool(use_detail.get("sources")), "Use detail returned no sources.")
        require(bool(use_detail.get("sber_doporuceni")), "Use detail returned no gathering guidance.")
        require(bool(use_detail.get("hlavni_prinos_text")), "Use detail returned no functional benefit summary.")
        require(bool(use_detail.get("aktivni_latky_text")), "Use detail returned no active compounds summary.")
        require(bool(plant_detail.get("aliases")), "Plant detail returned no aliases.")
        require(bool(plant_detail.get("uses")), "Plant detail returned no uses.")
        require(bool(plant_detail.get("sources")), "Plant detail returned no sources.")
        require(bool(plant_detail.get("photos")), "Plant detail returned no photos.")
        require(
            bool(functional_plant_detail.get("hlavni_prinos_text")),
            "Functional plant detail returned no plant-level benefit summary.",
        )
        require(
            bool(functional_plant_detail.get("aktivni_latky_text")),
            "Functional plant detail returned no plant-level compounds summary.",
        )
        require(compounds_search["count"] > 0, "Compound search returned no results.")
        require(
            any(use.get("sber_doporuceni") for use in plant_detail.get("uses", [])),
            "Plant detail uses do not expose gathering guidance.",
        )
        require(
            any(use.get("hlavni_prinos_text") for use in functional_plant_detail.get("uses", [])),
            "Functional plant detail uses do not expose benefit summaries.",
        )
        require(bool(plant_detail["photos"][0].get("source_name")), "Plant detail photo is missing source_name.")
        require(bool(plant_detail["photos"][0].get("source_url")), "Plant detail photo is missing source_url.")
        photo_use_id = plant_detail["uses"][0]["use_id"]
        require(durable_search["count"] > 0, "Durable search returned no results.")
        require(core_search["count"] > 0, "Core search returned no results.")
        require(durable_plants["count"] > 0, "Durable plant filter returned no results.")
        require(core_plants["count"] > 0, "Core plant filter returned no results.")
        require(evidence_search["count"] > 0, f"Evidence filter `{evidence_target}` returned no results.")
        require(domain_search["count"] > 0, f"Domain filter `{domain_target}` returned no results.")
        require(
            processing_method_search["count"] > 0,
            f"Processing method filter `{processing_method_target}` returned no results.",
        )

        for row in durable_search["results"]:
            require(row.get("je_trvanlive_1m_plus") == 1, "Durable search returned a non-durable use.")
        for row in core_search["results"]:
            require(row.get("je_v_jadru_bezne_1m_plus") == 1, "Core search returned a non-core use.")
        for row in durable_plants["results"]:
            require((row.get("durable_use_count") or 0) > 0, "Durable plant filter returned plant without durable uses.")
        for row in core_plants["results"]:
            require((row.get("core_use_count") or 0) > 0, "Core plant filter returned plant without core uses.")
        for row in evidence_search["results"]:
            require((row.get("dukaznost_rank") or 0) >= evidence_rank_threshold, "Evidence filter returned lower-evidence result.")
        for row in domain_search["results"]:
            require(row.get("domena") == domain_target, "Domain filter returned a result from another domain.")
        for row in processing_method_search["results"]:
            require(
                processing_method_label in str(row.get("processing_methods_text") or ""),
                "Processing method filter returned a result without the requested processing method label.",
            )
        for row in month_search["results"]:
            require(
                month_matches_range(month_target, row.get("mesic_od"), row.get("mesic_do")),
                f"Month filter returned result outside month range for month {month_target}.",
            )
        seasonal_months = seasonal_search["seasonal_window"]["months"]
        for row in seasonal_search["results"]:
            require(
                any(month_matches_range(month, row.get("mesic_od"), row.get("mesic_do")) for month in seasonal_months),
                "Seasonal search returned result outside every month in the seasonal window.",
            )

        html_routes = {}
        for route in ["/", "/plants", f"/plant/{PHOTO_TEST_PLANT_ID}", "/use/r001"]:
            html_result = fetch_url(f"{base_url}{route}")
            require(html_result.content_type == "text/html", f"Route `{route}` did not return HTML.")
            html_routes[route] = html_result.status

        plant_export_md, plant_export_md_result = read_text_url(f"{base_url}/export/plant/{PHOTO_TEST_PLANT_ID}.md")
        use_export_md, use_export_md_result = read_text_url(f"{base_url}/export/use/{photo_use_id}.md")
        plant_export_json = read_json_url(f"{base_url}/export/plant/{PHOTO_TEST_PLANT_ID}.json")
        use_export_json = read_json_url(f"{base_url}/export/use/{photo_use_id}.json")

        require(plant_export_md_result.content_type == "text/markdown", "Plant Markdown export returned unexpected content type.")
        require(use_export_md_result.content_type == "text/markdown", "Use Markdown export returned unexpected content type.")
        require(plant_export_md.startswith("# "), "Plant Markdown export is missing a top-level heading.")
        require(use_export_md.startswith("# "), "Use Markdown export is missing a top-level heading.")
        require_contains(plant_export_md, "## Aliasy", "Plant Markdown export")
        require_contains(plant_export_md, "## Fotky", "Plant Markdown export")
        require_contains(use_export_md, "## Jak sbírat správně", "Use Markdown export")
        require_contains(use_export_md, "## Zdroje", "Use Markdown export")
        require_contains(use_export_md, "## Fotky", "Use Markdown export")
        require(plant_export_json.get("plant_id") == PHOTO_TEST_PLANT_ID, "Plant JSON export returned unexpected plant_id.")
        require(use_export_json.get("use_id") == photo_use_id, "Use JSON export returned unexpected use_id.")
        require(bool(plant_export_json.get("photos")), "Plant JSON export returned no photos.")
        require(bool(use_export_json.get("sources")), "Use JSON export returned no sources.")
        require(bool(use_export_json.get("sber_doporuceni")), "Use JSON export returned no gathering guidance.")

        local_media_path = None
        local_media_content_type = None
        for photo in plant_detail["photos"]:
            src = str(photo.get("src") or "").strip()
            if src.startswith("/media/"):
                media_result = fetch_url(f"{base_url}{src}")
                require(media_result.content_type.startswith("image/"), f"Media route `{src}` did not return image content.")
                local_media_path = src
                local_media_content_type = media_result.content_type
                break

        missing_use_result = fetch_url(f"{base_url}/api/use?use_id={quote('use_missing_404')}")
        missing_use_payload = parse_json_result(missing_use_result, "Missing use API response")
        require(missing_use_result.status == 404, "Missing use endpoint did not return 404.")
        require("Use not found" in missing_use_payload.get("error", ""), "Missing use endpoint returned unexpected error payload.")

        missing_plant_result = fetch_url(f"{base_url}/api/plant?plant_id={quote('plant_missing_404')}")
        missing_plant_payload = parse_json_result(missing_plant_result, "Missing plant API response")
        require(missing_plant_result.status == 404, "Missing plant endpoint did not return 404.")
        require("Plant not found" in missing_plant_payload.get("error", ""), "Missing plant endpoint returned unexpected error payload.")

        missing_use_param_result = fetch_url(f"{base_url}/api/use")
        missing_use_param_payload = parse_json_result(missing_use_param_result, "Missing use_id API response")
        require(missing_use_param_result.status == 400, "Missing use_id endpoint did not return 400.")
        require("Missing use_id parameter" in missing_use_param_payload.get("error", ""), "Missing use_id response returned unexpected payload.")

        invalid_export_result = fetch_url(f"{base_url}/export/use/r001.txt")
        require(invalid_export_result.status == 400, "Unsupported export format did not return 400.")

        missing_export_result = fetch_url(f"{base_url}/export/plant/plant_missing_404.json")
        require(missing_export_result.status == 404, "Missing plant export did not return 404.")

        return {
            "summary_plants": summary["counts"]["plants"],
            "summary_uses": summary["counts"]["uses"],
            "options_domains": len(options["domains"]),
            "options_evidence_scores": len(options["evidence_scores"]),
            "options_months": len(options["months"]),
            "options_processing_methods": len(options["processing_methods"]),
            "seasonal_window_label": options["seasonal_default"]["label"],
            "seasonal_window_today": options["seasonal_default"]["today_label"],
            "search_count": search["count"],
            "seasonal_search_count": seasonal_search["count"],
            "plants_route_count": plants["count"],
            "seasonal_plants_count": seasonal_plants["count"],
            "first_media_kind": gallery_photo_row.get("primary_photo_kind_label"),
            "use_detail_aliases": len(use_detail["aliases"]),
            "use_detail_sources": len(use_detail["sources"]),
            "use_detail_has_gathering_guidance": bool(use_detail.get("sber_doporuceni")),
            "plant_detail_use_count": plant_detail["stats"]["use_count"],
            "plant_detail_media_kind": plant_detail["photos"][0].get("media_kind_label"),
            "plant_detail_source_name": plant_detail["photos"][0].get("source_name"),
            "photo_test_plant_id": PHOTO_TEST_PLANT_ID,
            "photo_test_use_id": photo_use_id,
            "durable_search_count": durable_search["count"],
            "core_search_count": core_search["count"],
            "durable_plants_count": durable_plants["count"],
            "core_plants_count": core_plants["count"],
            "domain_filter_name": domain_target,
            "domain_filter_count": domain_search["count"],
            "processing_filter_name": processing_method_label,
            "processing_filter_count": processing_method_search["count"],
            "evidence_filter_name": evidence_target,
            "evidence_filter_count": evidence_search["count"],
            "month_filter_value": month_target,
            "month_filter_count": month_search["count"],
            "plant_export_title": plant_export_md.splitlines()[0],
            "use_export_title": use_export_md.splitlines()[0],
            "plant_export_photos": len(plant_export_json["photos"]),
            "use_export_sources": len(use_export_json["sources"]),
            "html_routes": html_routes,
            "local_media_path": local_media_path,
            "local_media_content_type": local_media_content_type,
            "missing_use_status": missing_use_result.status,
            "missing_plant_status": missing_plant_result.status,
            "missing_use_param_status": missing_use_param_result.status,
            "invalid_export_status": invalid_export_result.status,
            "missing_export_status": missing_export_result.status,
        }
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


def write_report(root: Path, db_path: Path, sqlite_counts: dict[str, int], server_result: dict[str, object]) -> Path:
    report_path = root / "SMOKE_CHECK_PROJEKTU.md"
    photo_route = f"/plant/{server_result['photo_test_plant_id']}"
    lines = [
        "# Smoke Check Projektu",
        "",
        "## Výsledek",
        "",
        "- Stav: `PASS`",
        f"- Databáze: `{db_path}`",
        "",
        "## SQLite",
        "",
        f"- plants: {sqlite_counts['plants']}",
        f"- uses: {sqlite_counts['uses']}",
        f"- durable_forms: {sqlite_counts['durable_forms']}",
        f"- sources: {sqlite_counts['sources']}",
        f"- views: {sqlite_counts['views']}",
        "",
        "## API",
        "",
        f"- /api/summary plants: {server_result['summary_plants']}",
        f"- /api/summary uses: {server_result['summary_uses']}",
        f"- /api/options domains: {server_result['options_domains']}",
        f"- /api/options evidence scores: {server_result['options_evidence_scores']}",
        f"- /api/options months: {server_result['options_months']}",
        f"- /api/options processing methods: {server_result['options_processing_methods']}",
        f"- /api/options seasonal default: {server_result['seasonal_window_label']} ({server_result['seasonal_window_today']})",
        f"- /api/search?q=bez count: {server_result['search_count']}",
        f"- /api/search?seasonal=1 count: {server_result['seasonal_search_count']}",
        f"- /api/plants count: {server_result['plants_route_count']}",
        f"- /api/plants?seasonal=1 count: {server_result['seasonal_plants_count']}",
        f"- první nalezený media kind v plant galerii: {server_result['first_media_kind']}",
        f"- aliasy v detailu `r001`: {server_result['use_detail_aliases']}",
        f"- zdroje v detailu `r001`: {server_result['use_detail_sources']}",
        f"- detail `r001` má `sber_doporuceni`: {server_result['use_detail_has_gathering_guidance']}",
        f"- foto test plant: `{server_result['photo_test_plant_id']}`",
        f"- foto test use: `{server_result['photo_test_use_id']}`",
        f"- počet použití v detailu test plant: {server_result['plant_detail_use_count']}",
        f"- source name v detailu test plant: {server_result['plant_detail_source_name']}",
        f"- media kind v detailu test plant: {server_result['plant_detail_media_kind']}",
        "",
        "## HTML Route",
        "",
        f"- / status: {server_result['html_routes']['/']}",
        f"- /plants status: {server_result['html_routes']['/plants']}",
        f"- {photo_route} status: {server_result['html_routes'][photo_route]}",
        f"- /use/r001 status: {server_result['html_routes']['/use/r001']}",
        "",
        "## Exporty",
        "",
        f"- plant Markdown title: `{server_result['plant_export_title']}`",
        f"- use Markdown title: `{server_result['use_export_title']}`",
        f"- plant JSON photos: {server_result['plant_export_photos']}",
        f"- use JSON sources: {server_result['use_export_sources']}",
        "",
        "## Filter Invariants",
        "",
        f"- trvanlivé use výsledky: {server_result['durable_search_count']}",
        f"- jádrové use výsledky: {server_result['core_search_count']}",
        f"- trvanlivé plant výsledky: {server_result['durable_plants_count']}",
        f"- jádrové plant výsledky: {server_result['core_plants_count']}",
        f"- domain filtr `{server_result['domain_filter_name']}` count: {server_result['domain_filter_count']}",
        f"- processing filtr `{server_result['processing_filter_name']}` count: {server_result['processing_filter_count']}",
        f"- evidence filtr `{server_result['evidence_filter_name']}` count: {server_result['evidence_filter_count']}",
        f"- month filtr `{server_result['month_filter_value']}` count: {server_result['month_filter_count']}",
        "",
        "## Negative Scenarios",
        "",
        f"- missing use status: {server_result['missing_use_status']}",
        f"- missing plant status: {server_result['missing_plant_status']}",
        f"- missing use_id status: {server_result['missing_use_param_status']}",
        f"- invalid export format status: {server_result['invalid_export_status']}",
        f"- missing export status: {server_result['missing_export_status']}",
        "",
        "## Media",
        "",
        f"- lokální media route: `{server_result['local_media_path']}`",
        f"- content-type: `{server_result['local_media_content_type']}`",
        "",
        "## Co bylo ověřeno",
        "",
        "- otevření SQLite databáze",
        "- existence základních tabulek a view",
        "- běh lokálního katalog serveru nad zvolenou DB",
        "- summary endpoint",
        "- options endpoint",
        "- plant index endpoint",
        "- use search endpoint",
        "- sezónní default okno a jeho aplikace v search/plants API",
        "- use detail endpoint",
        "- plant detail endpoint",
        "- standalone HTML route pro katalog, plant detail a use detail",
        "- export route pro plant/use v JSON i Markdown",
        "- základní kontrola struktury export payloadů",
        "- invarianty pro durable/core/domain/evidence/month/processing filtry",
        "- odvozené `sber_doporuceni` v detailu a exportech",
        "- očekávané 400/404 chování u chybových scénářů",
        "- dostupnost media provenance v API",
        "- foto zdroje a provenance v detailu/exportech",
        "",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def main() -> None:
    args = parse_args()
    root = project_root()
    db_path = args.db.resolve() if args.db else choose_default_db(root)
    if not db_path.exists():
        raise FileNotFoundError(f"SQLite database not found: {db_path}")

    sqlite_counts = run_sqlite_checks(db_path)
    server_result = run_server_checks(root, db_path, args.host, args.port, args.startup_wait)
    report_path = write_report(root, db_path, sqlite_counts, server_result)

    print(f"Smoke check PASS for database: {db_path}")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, FileNotFoundError, URLError, sqlite3.Error) as exc:
        print(f"Smoke check FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
