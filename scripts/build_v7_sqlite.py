from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime
from pathlib import Path


TABLE_ORDER = [
    "plants",
    "plant_aliases",
    "uses",
    "durable_forms",
    "sources",
    "use_sources",
    "use_processing_methods",
    "vocab_part_categories",
    "vocab_subdomain_categories",
    "vocab_storage_categories",
    "vocab_processing_methods",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build SQLite database from v7 canonical JSON tables.")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output path for the generated SQLite database.",
    )
    parser.add_argument(
        "--promote-rebuild",
        action="store_true",
        help="Promote the latest rebuild SQLite file to the primary output path and exit.",
    )
    parser.add_argument(
        "--rebuild-path",
        type=Path,
        default=None,
        help="Optional explicit rebuild SQLite file to promote.",
    )
    return parser.parse_args()


def choose_workbook_stem(project_dir: Path) -> str:
    preferred = project_dir / "cz_rostliny_rozsireny_dataset_v6_jadro_bezne_trvanlive.xlsx"
    if preferred.exists():
        return preferred.stem

    workbooks = sorted(project_dir.glob("*.xlsx"))
    if not workbooks:
        raise FileNotFoundError("No .xlsx workbook found in the workspace.")
    return workbooks[0].stem


def sqlite_type_for_value(value):
    if isinstance(value, bool):
        return "INTEGER"
    if isinstance(value, int):
        return "INTEGER"
    if isinstance(value, float):
        return "REAL"
    return "TEXT"


def create_table(conn: sqlite3.Connection, table_name: str, rows: list[dict]) -> None:
    if not rows:
        conn.execute(f'DROP TABLE IF EXISTS "{table_name}"')
        conn.execute(f'CREATE TABLE "{table_name}" ("empty" TEXT)')
        return

    columns = list(rows[0].keys())
    sample_types = {column: sqlite_type_for_value(rows[0][column]) for column in columns}
    column_defs = ", ".join(f'"{column}" {sample_types[column]}' for column in columns)
    conn.execute(f'DROP TABLE IF EXISTS "{table_name}"')
    conn.execute(f'CREATE TABLE "{table_name}" ({column_defs})')

    placeholders = ", ".join("?" for _ in columns)
    quoted_columns = ", ".join(f'"{column}"' for column in columns)
    insert_sql = f'INSERT INTO "{table_name}" ({quoted_columns}) VALUES ({placeholders})'
    values = []
    for row in rows:
        values.append(
            tuple(
                int(row[column]) if isinstance(row[column], bool) else row[column]
                for column in columns
            )
        )
    conn.executemany(insert_sql, values)


def create_indexes(conn: sqlite3.Connection) -> None:
    statements = [
        'CREATE INDEX IF NOT EXISTS idx_uses_plant_id ON uses (plant_id)',
        'CREATE INDEX IF NOT EXISTS idx_uses_domena_slug ON uses (domena_slug)',
        'CREATE INDEX IF NOT EXISTS idx_uses_poddomena_kategorie ON uses (poddomena_kategorie)',
        'CREATE INDEX IF NOT EXISTS idx_uses_record_id ON uses (raw_record_id)',
        'CREATE INDEX IF NOT EXISTS idx_durable_use_id ON durable_forms (use_id)',
        'CREATE INDEX IF NOT EXISTS idx_use_sources_use_id ON use_sources (use_id)',
        'CREATE INDEX IF NOT EXISTS idx_use_sources_source_id ON use_sources (source_id)',
        'CREATE INDEX IF NOT EXISTS idx_use_processing_methods_use_id ON use_processing_methods (use_id)',
        'CREATE INDEX IF NOT EXISTS idx_use_processing_methods_method_id ON use_processing_methods (processing_method_id)',
        'CREATE INDEX IF NOT EXISTS idx_aliases_plant_id ON plant_aliases (plant_id)',
        'CREATE INDEX IF NOT EXISTS idx_aliases_alias ON plant_aliases (alias)',
    ]
    for statement in statements:
        conn.execute(statement)


def create_views(conn: sqlite3.Connection) -> None:
    conn.execute("DROP VIEW IF EXISTS vw_use_search")
    conn.execute(
        """
        CREATE VIEW vw_use_search AS
        SELECT
            u.use_id,
            u.raw_record_id,
            p.plant_id,
            p.vedecky_nazev_hlavni,
            p.cesky_nazev_hlavni,
            u.cesky_nazev_display,
            u.domena,
            u.domena_slug,
            u.poddomena_text,
            u.poddomena_kategorie,
            u.cast_rostliny_text,
            u.cast_rostliny_kategorie,
            u.status_znalosti,
            u.aplikovatelnost_v_cr,
            u.obdobi_ziskani_text,
            u.mesic_od,
            u.mesic_do,
            u.je_trvanlive_1m_plus,
            u.je_v_jadru_bezne_1m_plus,
            u.dukaznost_skore,
            u.dukaznost_rank,
            d.forma_uchovani_text,
            d.orientacni_trvanlivost_text,
            d.is_core_item
        FROM uses u
        JOIN plants p ON p.plant_id = u.plant_id
        LEFT JOIN durable_forms d ON d.use_id = u.use_id
        """
    )

    conn.execute("DROP VIEW IF EXISTS vw_durable_core")
    conn.execute(
        """
        CREATE VIEW vw_durable_core AS
        SELECT
            d.durable_id,
            d.use_id,
            u.raw_record_id,
            p.vedecky_nazev_hlavni,
            p.cesky_nazev_hlavni,
            u.domena,
            u.poddomena_text,
            d.forma_uchovani_text,
            d.orientacni_trvanlivost_text,
            d.poznamka_k_skladovani,
            d.proc_je_v_jadru
        FROM durable_forms d
        JOIN uses u ON u.use_id = d.use_id
        JOIN plants p ON p.plant_id = u.plant_id
        WHERE d.is_core_item = 1
        """
    )


def temp_db_path_for(target_path: Path) -> Path:
    return target_path.with_name(f"{target_path.stem}.tmp{target_path.suffix}")


def fallback_db_path_for(target_path: Path) -> Path:
    candidate = target_path.with_name(f"{target_path.stem}.rebuild{target_path.suffix}")
    if not candidate.exists():
        return candidate
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return target_path.with_name(f"{target_path.stem}.rebuild_{timestamp}{target_path.suffix}")


def backup_primary_path_for(target_path: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return target_path.with_name(f"{target_path.stem}.pre_promote_{timestamp}{target_path.suffix}")


def find_rebuild_candidates(target_path: Path) -> list[Path]:
    pattern = f"{target_path.stem}.rebuild*{target_path.suffix}"
    return sorted(target_path.parent.glob(pattern), key=lambda path: (path.stat().st_mtime, path.name))


def promote_rebuild_database(target_path: Path, explicit_rebuild_path: Path | None = None) -> tuple[Path, Path, Path | None]:
    rebuild_path = explicit_rebuild_path.resolve() if explicit_rebuild_path else None
    if rebuild_path is None:
        candidates = find_rebuild_candidates(target_path)
        if not candidates:
            raise FileNotFoundError(f"No rebuild SQLite file found for target: {target_path}")
        rebuild_path = candidates[-1].resolve()

    if not rebuild_path.exists():
        raise FileNotFoundError(f"Rebuild SQLite file not found: {rebuild_path}")
    if rebuild_path == target_path:
        raise RuntimeError(f"Rebuild path already matches the primary target: {target_path}")

    backup_path = None
    try:
        if target_path.exists():
            backup_path = backup_primary_path_for(target_path)
            target_path.replace(backup_path)
        rebuild_path.replace(target_path)
    except PermissionError as exc:
        if backup_path is not None and backup_path.exists() and not target_path.exists():
            backup_path.replace(target_path)
        raise RuntimeError(
            f"Primary SQLite target is locked and rebuild could not be promoted: {target_path}"
        ) from exc
    except OSError as exc:
        if backup_path is not None and backup_path.exists() and not target_path.exists():
            backup_path.replace(target_path)
        raise RuntimeError(
            f"Failed to promote rebuild SQLite `{rebuild_path}` to primary target `{target_path}`."
        ) from exc

    return target_path, rebuild_path, backup_path


def finalize_database(temp_path: Path, target_path: Path) -> tuple[Path, str | None]:
    try:
        temp_path.replace(target_path)
        return target_path, None
    except PermissionError:
        fallback_path = fallback_db_path_for(target_path)
        temp_path.replace(fallback_path)
        return (
            fallback_path,
            (
                f"Primary target was locked and could not be replaced: {target_path}. "
                f"SQLite database was written to fallback path instead: {fallback_path}. "
                "Run `build_v7_sqlite.py --promote-rebuild` after the lock is gone to promote the newest rebuild file."
            ),
        )


def main() -> None:
    args = parse_args()
    if args.rebuild_path and not args.promote_rebuild:
        raise SystemExit("--rebuild-path can only be used together with --promote-rebuild.")

    project_dir = Path(__file__).resolve().parents[1]
    workbook_stem = choose_workbook_stem(project_dir)
    canonical_dir = project_dir / "exports" / workbook_stem / "v7_canonical"
    canonical_json_dir = canonical_dir / "json"
    db_path = args.output.resolve() if args.output else canonical_dir / "v7_dataset.sqlite"

    if args.promote_rebuild:
        promoted_path, source_rebuild_path, backup_path = promote_rebuild_database(db_path, args.rebuild_path)
        print(f"Promoted rebuild SQLite to primary: {promoted_path}")
        print(f"Source rebuild: {source_rebuild_path}")
        if backup_path is not None:
            print(f"Previous primary backed up to: {backup_path}")
        return

    if not canonical_json_dir.exists():
        raise FileNotFoundError(
            f"Canonical JSON directory not found at {canonical_json_dir}. Run build_v7_canonical.py first."
        )

    table_payloads = {}
    for table_name in TABLE_ORDER:
        json_path = canonical_json_dir / f"{table_name}.json"
        if not json_path.exists():
            raise FileNotFoundError(f"Missing canonical table file: {json_path}")
        table_payloads[table_name] = json.loads(json_path.read_text(encoding="utf-8"))

    db_path.parent.mkdir(parents=True, exist_ok=True)
    temp_db_path = temp_db_path_for(db_path)
    if temp_db_path.exists():
        temp_db_path.unlink()

    conn = sqlite3.connect(temp_db_path)
    try:
        for table_name in TABLE_ORDER:
            create_table(conn, table_name, table_payloads[table_name])

        create_indexes(conn)
        create_views(conn)
        conn.commit()
    finally:
        conn.close()

    written_path, warning = finalize_database(temp_db_path, db_path)
    print(f"SQLite database written to: {written_path}")
    if warning:
        print(warning)


if __name__ == "__main__":
    main()
