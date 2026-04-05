from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class StepResult:
    name: str
    command: list[str]
    stdout: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the full Czech plants build pipeline.")
    parser.add_argument("--skip-smoke", action="store_true", help="Skip smoke checks at the end.")
    parser.add_argument("--smoke-port", type=int, default=8780, help="Port for temporary smoke-check server.")
    parser.add_argument(
        "--promote-rebuild",
        action="store_true",
        help="If SQLite build writes a rebuild file, try to promote it to the primary database at the end.",
    )
    return parser.parse_args()


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def run_step(root: Path, name: str, command: list[str]) -> StepResult:
    completed = subprocess.run(
        command,
        cwd=root,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"Step `{name}` failed with code {completed.returncode}.\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    return StepResult(name=name, command=command, stdout=completed.stdout.strip())


def extract_first_match(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text)
    return match.group(1).strip() if match else None


def write_report(
    root: Path,
    steps: list[StepResult],
    sqlite_path: str | None,
    smoke_output: str | None,
    smoke_report_path: str | None,
    promotion_output: str | None,
    promotion_backup_path: str | None,
) -> Path:
    report_path = root / "BUILD_PIPELINE_REPORT.md"
    sqlite_kind = None
    if sqlite_path:
        sqlite_kind = "fallback rebuild" if ".rebuild" in sqlite_path else "primary"

    lines = [
        "# Build Pipeline Report",
        "",
        "## Stav",
        "",
        "- Výsledek: `PASS`",
        "",
        "## Kroky",
        "",
    ]
    for step in steps:
        lines.append(f"- `{step.name}`")
        lines.append(f"  příkaz: `{' '.join(step.command)}`")
        if step.stdout:
            first_line = step.stdout.splitlines()[0]
            lines.append(f"  výstup: `{first_line}`")
    if sqlite_path:
        lines.extend(
            [
                "",
                "## SQLite výstup",
                "",
                f"- `{sqlite_path}`",
            ]
        )
        if sqlite_kind:
            lines.append(f"- typ výstupu: `{sqlite_kind}`")
    if smoke_output:
        lines.extend(
            [
                "",
                "## Smoke Check",
                "",
                f"- `{smoke_output}`",
            ]
        )
    if smoke_report_path:
        lines.append(f"- report: `{smoke_report_path}`")
    if promotion_output:
        lines.extend(
            [
                "",
                "## Promotion",
                "",
                f"- `{promotion_output}`",
            ]
        )
        if promotion_backup_path:
            lines.append(f"- backup previous primary: `{promotion_backup_path}`")
    lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main() -> None:
    args = parse_args()
    root = project_root()
    python = sys.executable

    steps: list[StepResult] = []
    steps.append(run_step(root, "export_workbook", [python, str(root / "scripts" / "export_workbook.py")]))
    steps.append(run_step(root, "build_v7_canonical", [python, str(root / "scripts" / "build_v7_canonical.py")]))
    sqlite_step = run_step(root, "build_v7_sqlite", [python, str(root / "scripts" / "build_v7_sqlite.py")])
    steps.append(sqlite_step)
    steps.append(run_step(root, "build_pages_site", [python, str(root / "scripts" / "build_pages_site.py")]))

    sqlite_path = extract_first_match(r"SQLite database written to:\s*(.+)", sqlite_step.stdout)
    smoke_output = None
    smoke_report_path = None
    promotion_output = None
    promotion_backup_path = None
    if not args.skip_smoke:
        smoke_command = [
            python,
            str(root / "scripts" / "smoke_check.py"),
            "--port",
            str(args.smoke_port),
        ]
        if sqlite_path:
            smoke_command.extend(["--db", sqlite_path])
        smoke_step = run_step(root, "smoke_check", smoke_command)
        steps.append(smoke_step)
        smoke_output = smoke_step.stdout.splitlines()[0] if smoke_step.stdout else "PASS"
        smoke_report_path = extract_first_match(r"Report:\s*(.+)", smoke_step.stdout)

    if args.promote_rebuild and sqlite_path and ".rebuild" in sqlite_path:
        promote_command = [
            python,
            str(root / "scripts" / "build_v7_sqlite.py"),
            "--promote-rebuild",
            "--rebuild-path",
            sqlite_path,
        ]
        promote_step = run_step(root, "promote_rebuild", promote_command)
        steps.append(promote_step)
        promotion_output = promote_step.stdout.splitlines()[0] if promote_step.stdout else "Promoted"
        promotion_backup_path = extract_first_match(r"Previous primary backed up to:\s*(.+)", promote_step.stdout)
        sqlite_path = extract_first_match(r"Promoted rebuild SQLite to primary:\s*(.+)", promote_step.stdout) or sqlite_path

    report_path = write_report(
        root,
        steps,
        sqlite_path,
        smoke_output,
        smoke_report_path,
        promotion_output,
        promotion_backup_path,
    )
    print("Build pipeline PASS")
    if sqlite_path:
        print(f"SQLite database: {sqlite_path}")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(f"Build pipeline FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
