from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def configure_stdout() -> None:
    stream = getattr(sys, "stdout", None)
    if stream is None or not hasattr(stream, "reconfigure"):
        return
    try:
        stream.reconfigure(encoding="utf-8", errors="replace")
    except ValueError:
        pass


def plugin_root() -> Path:
    return Path(__file__).resolve().parents[1]


def fixture_dir() -> Path:
    return plugin_root() / "examples" / "demo-review"


def default_output_dir() -> Path:
    return Path.cwd().resolve() / "demo_review_output"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy the bundled demo architecture review into an output directory and validate it."
    )
    parser.add_argument(
        "--output-dir",
        help="Directory where report.md and evidence.json should be written.",
    )
    parser.add_argument(
        "--skip-validate",
        action="store_true",
        help="Skip the final artifact validation step.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable output.",
    )
    return parser.parse_args()


def run_validation(output_dir: Path) -> dict[str, object]:
    validator = plugin_root() / "scripts" / "validate_artifact_bundle.py"
    result = subprocess.run(
        [sys.executable, str(validator), "--bundle-dir", str(output_dir), "--json"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    try:
        payload = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        payload = {
            "valid": False,
            "issues": ["Validator returned unreadable output."],
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    payload["validator_exit_code"] = result.returncode
    return payload


def print_human(payload: dict[str, object]) -> None:
    print(f"source: {payload['source_dir']}")
    print(f"report: {payload['report_path']}")
    print(f"evidence: {payload['evidence_path']}")
    if payload.get("validation"):
        validation = payload["validation"]
        print(f"bundle valid: {validation.get('valid', False)}")
        for issue in validation.get("issues", []):
            print(f"  - {issue}")


def main() -> int:
    configure_stdout()
    args = parse_args()
    source_dir = fixture_dir()
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else default_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    report_source = source_dir / "report.md"
    evidence_source = source_dir / "evidence.json"
    notes_source = source_dir / "architecture_notes.md"
    report_target = output_dir / "report.md"
    evidence_target = output_dir / "evidence.json"

    shutil.copyfile(report_source, report_target)
    shutil.copyfile(evidence_source, evidence_target)
    if notes_source.exists():
        shutil.copyfile(notes_source, output_dir / notes_source.name)

    validation = None if args.skip_validate else run_validation(output_dir)
    payload = {
        "source_dir": str(source_dir),
        "report_path": str(report_target),
        "evidence_path": str(evidence_target),
        "validation": validation,
    }

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print_human(payload)

    if validation is None:
        return 0
    return 0 if validation.get("valid") else 1


if __name__ == "__main__":
    raise SystemExit(main())
