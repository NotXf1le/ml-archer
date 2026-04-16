from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

from artifact_bundle_service import ArtifactBundleValidator
from script_output import PayloadEmitter

REQUIRED_SECTIONS = [
    "Architecture decomposition",
    "Typed state inventory",
    "Operator-state matrix",
    "Supervision and gradient reachability",
    "Shortcut and path dominance",
    "Invariants and singularities",
    "Train/infer congruence",
    "Formalization candidates for mathlib",
    "Empirical-only claims",
    "Risks and redesign guidance",
]

REQUIRED_TOP_LEVEL_FIELDS = [
    "architecture_name",
    "architecture_summary",
    "assumptions",
    "typed_states",
    "operators",
    "operator_state_matrix",
    "supervision_matrix",
    "shortcut_paths",
    "invariants",
    "train_infer_congruence",
    "findings",
    "formalization_candidates",
    "empirical_only_claims",
]

REQUIRED_TYPED_STATE_FIELDS = [
    "state_id",
    "symbol",
    "semantic_role",
    "shape",
    "space",
    "geometry",
    "time_role",
    "persistence",
    "producer_ops",
    "consumer_ops",
]

REQUIRED_OPERATOR_FIELDS = [
    "operator_id",
    "equation_or_rule",
    "purpose",
    "reads",
    "writes",
    "mode",
]

REQUIRED_SHORTCUT_FIELDS = [
    "shortcut_id",
    "claim_or_output",
    "intended_path",
    "shortcut_path",
    "status",
    "risk_summary",
]

REQUIRED_INVARIANT_FIELDS = [
    "invariant_id",
    "statement",
    "statuses",
    "boundary",
]

REQUIRED_FINDING_FIELDS = [
    "finding_id",
    "finding_label",
    "severity",
    "summary",
    "basis",
    "confidence",
    "evidence_refs",
    "boundary",
    "recommended_action",
]

REQUIRED_FORMALIZATION_FIELDS = [
    "candidate_id",
    "natural_language_claim",
    "reason_it_is_formalizable",
    "theorem_family",
    "search_terms",
    "suggested_import_nouns",
    "side_conditions",
]

REQUIRED_EMPIRICAL_FIELDS = [
    "claim_id",
    "claim",
    "why_empirical",
    "required_evidence",
]

FORBIDDEN_KEYS = {"verified_in_lean", "verification_method", "claim_label"}
FORBIDDEN_FORMAL_LABELS = {
    "Formal support",
    "Partial formal support",
    "No direct formal support found in mathlib",
}
VALID_OPERATOR_MODES = {"train", "infer", "both"}
VALID_FINDING_LABELS = {
    "Structural finding",
    "Type violation risk",
    "Invariant risk",
    "Gradient reachability finding",
    "Shortcut risk",
    "Train/infer mismatch risk",
    "Formalization candidate",
    "Empirical-only claim",
}
VALID_CONFIDENCE = {"high", "medium", "low"}
VALID_SEVERITY = {"low", "medium", "high", "critical"}
VALID_BASIS = {
    "explicit_equation",
    "textual_description",
    "naming_inference",
    "assumption_backed",
    "missing_information",
}
VALID_CONGRUENCE_STATUS = {"aligned", "partial_mismatch", "mismatch", "underdetermined"}


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


def default_workspace_root() -> Path:
    return Path.cwd().resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a typed-architecture-tomography artifact bundle without relying on hooks."
    )
    parser.add_argument("--bundle-dir", help="Directory containing report.md and tomography.json.")
    parser.add_argument(
        "--report",
        help="Path to a report file. tomography.json is resolved next to it unless --tomography is passed.",
    )
    parser.add_argument("--tomography", help="Path to tomography.json.")
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Inspect the most recent bundle under plugin-root/reports or workspace-root/reports.",
    )
    parser.add_argument(
        "--workspace",
        help="Workspace root used when --latest is selected. Defaults to the current directory.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable output.")
    return parser.parse_args()


def candidate_report_dirs(workspace_root: Path) -> list[Path]:
    candidates = [plugin_root() / "reports", workspace_root / "reports"]
    return [path.resolve() for path in candidates if path.exists()]


def latest_report(candidate_dirs: list[Path]) -> Path | None:
    reports: list[Path] = []
    for directory in candidate_dirs:
        reports.extend(
            path
            for path in directory.rglob("*")
            if path.is_file() and (path.name == "report.md" or path.name.startswith("architecture_tomography_report"))
        )
    if not reports:
        return None
    return max(reports, key=lambda path: path.stat().st_mtime)


def report_in_bundle_dir(bundle_dir: Path) -> Path | None:
    if not bundle_dir.exists():
        return None
    report = bundle_dir / "report.md"
    if report.exists():
        return report
    candidates = [
        path
        for path in bundle_dir.iterdir()
        if path.is_file() and path.name.startswith("architecture_tomography_report")
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def resolve_targets(args: argparse.Namespace) -> tuple[Path | None, Path | None]:
    if args.bundle_dir:
        bundle_dir = Path(args.bundle_dir).expanduser().resolve()
        report = report_in_bundle_dir(bundle_dir)
        tomography = Path(args.tomography).expanduser().resolve() if args.tomography else bundle_dir / "tomography.json"
        return report, tomography

    if args.report:
        report = Path(args.report).expanduser().resolve()
        tomography = Path(args.tomography).expanduser().resolve() if args.tomography else report.with_name("tomography.json")
        return report, tomography

    if args.latest:
        workspace_root = Path(args.workspace).expanduser().resolve() if args.workspace else default_workspace_root()
        report = latest_report(candidate_report_dirs(workspace_root))
        if report is None:
            return None, None
        tomography = Path(args.tomography).expanduser().resolve() if args.tomography else report.with_name("tomography.json")
        return report, tomography

    return None, None


def _report_validator() -> ArtifactBundleValidator:
    return ArtifactBundleValidator(
        required_sections=REQUIRED_SECTIONS,
        required_evidence_fields=[],
        required_side_condition_fields=[],
    )


def heading_positions(report_text: str) -> dict[str, int]:
    return _report_validator().heading_positions(report_text)


def validate_report(report_path: Path) -> tuple[list[str], dict[str, int]]:
    return _report_validator().validate_report(report_path)


def _missing_or_blank(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, dict, tuple, set)):
        return len(value) == 0
    return False


def _require_fields(record: dict[str, object], fields: Iterable[str], prefix: str) -> list[str]:
    issues: list[str] = []
    for field in fields:
        if _missing_or_blank(record.get(field)):
            issues.append(f"{prefix} is missing '{field}'.")
    return issues


def _scan_forbidden_keys(value: object, prefix: str = "$") -> list[str]:
    issues: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in FORBIDDEN_KEYS:
                issues.append(f"Forbidden formal key '{key}' found at {prefix}.{key}.")
            issues.extend(_scan_forbidden_keys(nested, f"{prefix}.{key}"))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            issues.extend(_scan_forbidden_keys(nested, f"{prefix}[{index}]"))
    return issues


def validate_tomography(tomography_path: Path) -> tuple[list[str], dict[str, object] | None]:
    if not tomography_path.exists():
        return [f"Missing tomography file: {tomography_path}"], None

    try:
        payload = json.loads(tomography_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"tomography.json is not valid JSON: {exc.msg}"], None

    if not isinstance(payload, dict):
        return ["tomography.json must be a JSON object."], None

    issues: list[str] = []
    issues.extend(_scan_forbidden_keys(payload))

    for field in REQUIRED_TOP_LEVEL_FIELDS:
        if _missing_or_blank(payload.get(field)):
            issues.append(f"tomography.json is missing top-level field '{field}'.")

    assumptions = payload.get("assumptions")
    if assumptions is not None and not isinstance(assumptions, list):
        issues.append("'assumptions' must be an array.")

    typed_states = payload.get("typed_states")
    if isinstance(typed_states, list):
        for index, record in enumerate(typed_states, start=1):
            if not isinstance(record, dict):
                issues.append(f"typed_states[{index}] must be an object.")
                continue
            issues.extend(_require_fields(record, REQUIRED_TYPED_STATE_FIELDS, f"typed_states[{index}]"))
    else:
        issues.append("'typed_states' must be an array.")

    operators = payload.get("operators")
    if isinstance(operators, list):
        for index, record in enumerate(operators, start=1):
            if not isinstance(record, dict):
                issues.append(f"operators[{index}] must be an object.")
                continue
            issues.extend(_require_fields(record, REQUIRED_OPERATOR_FIELDS, f"operators[{index}]"))
            mode = record.get("mode")
            if isinstance(mode, str) and mode not in VALID_OPERATOR_MODES:
                issues.append(f"operators[{index}] has invalid mode '{mode}'.")
    else:
        issues.append("'operators' must be an array.")

    operator_state_matrix = payload.get("operator_state_matrix")
    if isinstance(operator_state_matrix, dict):
        if _missing_or_blank(operator_state_matrix.get("states")):
            issues.append("operator_state_matrix is missing 'states'.")
        rows = operator_state_matrix.get("rows")
        if not isinstance(rows, list) or not rows:
            issues.append("operator_state_matrix must provide non-empty 'rows'.")
        else:
            for index, row in enumerate(rows, start=1):
                if not isinstance(row, dict):
                    issues.append(f"operator_state_matrix.rows[{index}] must be an object.")
                    continue
                issues.extend(_require_fields(row, ["operator_id", "cells"], f"operator_state_matrix.rows[{index}]"))
                cells = row.get("cells")
                if cells is not None and not isinstance(cells, dict):
                    issues.append(f"operator_state_matrix.rows[{index}].cells must be an object.")
    else:
        issues.append("'operator_state_matrix' must be an object.")

    supervision_matrix = payload.get("supervision_matrix")
    if isinstance(supervision_matrix, dict):
        rows = supervision_matrix.get("rows")
        if not isinstance(rows, list) or not rows:
            issues.append("supervision_matrix must provide non-empty 'rows'.")
        else:
            for index, row in enumerate(rows, start=1):
                if not isinstance(row, dict):
                    issues.append(f"supervision_matrix.rows[{index}] must be an object.")
                    continue
                issues.extend(_require_fields(row, ["loss_id", "cells", "notes"], f"supervision_matrix.rows[{index}]"))
                cells = row.get("cells")
                if cells is not None and not isinstance(cells, dict):
                    issues.append(f"supervision_matrix.rows[{index}].cells must be an object.")
    else:
        issues.append("'supervision_matrix' must be an object.")

    shortcut_paths = payload.get("shortcut_paths")
    if isinstance(shortcut_paths, list):
        for index, record in enumerate(shortcut_paths, start=1):
            if not isinstance(record, dict):
                issues.append(f"shortcut_paths[{index}] must be an object.")
                continue
            issues.extend(_require_fields(record, REQUIRED_SHORTCUT_FIELDS, f"shortcut_paths[{index}]"))
    else:
        issues.append("'shortcut_paths' must be an array.")

    invariants = payload.get("invariants")
    if isinstance(invariants, list):
        for index, record in enumerate(invariants, start=1):
            if not isinstance(record, dict):
                issues.append(f"invariants[{index}] must be an object.")
                continue
            issues.extend(_require_fields(record, REQUIRED_INVARIANT_FIELDS, f"invariants[{index}]"))
            statuses = record.get("statuses")
            if statuses is not None and not isinstance(statuses, dict):
                issues.append(f"invariants[{index}].statuses must be an object.")
    else:
        issues.append("'invariants' must be an array.")

    congruence = payload.get("train_infer_congruence")
    if isinstance(congruence, dict):
        issues.extend(
            _require_fields(
                congruence,
                ["status", "train_path", "infer_path", "mismatch_points", "notes"],
                "train_infer_congruence",
            )
        )
        status = congruence.get("status")
        if isinstance(status, str) and status not in VALID_CONGRUENCE_STATUS:
            issues.append(f"train_infer_congruence has invalid status '{status}'.")
        mismatch_points = congruence.get("mismatch_points")
        if mismatch_points is not None and not isinstance(mismatch_points, list):
            issues.append("train_infer_congruence.mismatch_points must be an array.")
    else:
        issues.append("'train_infer_congruence' must be an object.")

    findings = payload.get("findings")
    if isinstance(findings, list):
        for index, record in enumerate(findings, start=1):
            if not isinstance(record, dict):
                issues.append(f"findings[{index}] must be an object.")
                continue
            issues.extend(_require_fields(record, REQUIRED_FINDING_FIELDS, f"findings[{index}]"))
            label = record.get("finding_label")
            if isinstance(label, str):
                if label in FORBIDDEN_FORMAL_LABELS:
                    issues.append(f"findings[{index}] uses forbidden formal label '{label}'.")
                elif label not in VALID_FINDING_LABELS:
                    issues.append(f"findings[{index}] has unknown finding_label '{label}'.")
            severity = record.get("severity")
            if isinstance(severity, str) and severity not in VALID_SEVERITY:
                issues.append(f"findings[{index}] has invalid severity '{severity}'.")
            basis = record.get("basis")
            if isinstance(basis, str) and basis not in VALID_BASIS:
                issues.append(f"findings[{index}] has invalid basis '{basis}'.")
            confidence = record.get("confidence")
            if isinstance(confidence, str) and confidence not in VALID_CONFIDENCE:
                issues.append(f"findings[{index}] has invalid confidence '{confidence}'.")
    else:
        issues.append("'findings' must be an array.")

    candidates = payload.get("formalization_candidates")
    if isinstance(candidates, list):
        for index, record in enumerate(candidates, start=1):
            if not isinstance(record, dict):
                issues.append(f"formalization_candidates[{index}] must be an object.")
                continue
            issues.extend(
                _require_fields(
                    record,
                    REQUIRED_FORMALIZATION_FIELDS,
                    f"formalization_candidates[{index}]",
                )
            )
    else:
        issues.append("'formalization_candidates' must be an array.")

    empirical = payload.get("empirical_only_claims")
    if isinstance(empirical, list):
        for index, record in enumerate(empirical, start=1):
            if not isinstance(record, dict):
                issues.append(f"empirical_only_claims[{index}] must be an object.")
                continue
            issues.extend(_require_fields(record, REQUIRED_EMPIRICAL_FIELDS, f"empirical_only_claims[{index}]"))
    else:
        issues.append("'empirical_only_claims' must be an array.")

    return issues, payload


def summary_from_payload(payload: dict[str, object] | None) -> dict[str, object]:
    if not isinstance(payload, dict):
        return {
            "typed_state_count": 0,
            "finding_count": 0,
            "formalization_candidate_count": 0,
            "congruence_status": None,
        }
    return {
        "typed_state_count": len(payload.get("typed_states", [])) if isinstance(payload.get("typed_states"), list) else 0,
        "finding_count": len(payload.get("findings", [])) if isinstance(payload.get("findings"), list) else 0,
        "formalization_candidate_count": len(payload.get("formalization_candidates", [])) if isinstance(payload.get("formalization_candidates"), list) else 0,
        "congruence_status": payload.get("train_infer_congruence", {}).get("status") if isinstance(payload.get("train_infer_congruence"), dict) else None,
    }


def print_human(payload: dict[str, object]) -> None:
    status = "valid" if payload["valid"] else "invalid"
    print(f"bundle: {status}")
    if payload.get("report_path"):
        print(f"report: {payload['report_path']}")
    if payload.get("tomography_path"):
        print(f"tomography: {payload['tomography_path']}")
    print(f"typed states: {payload.get('typed_state_count', 0)}")
    print(f"findings: {payload.get('finding_count', 0)}")
    print(f"formalization candidates: {payload.get('formalization_candidate_count', 0)}")
    if payload.get("congruence_status"):
        print(f"train/infer congruence: {payload['congruence_status']}")
    if payload["issues"]:
        print("issues:")
        for issue in payload["issues"]:
            print(f" - {issue}")


def main() -> int:
    configure_stdout()
    args = parse_args()
    report_path, tomography_path = resolve_targets(args)

    if report_path is None or tomography_path is None:
        payload = {
            "valid": False,
            "report_path": None,
            "tomography_path": None,
            "issues": ["No tomography bundle could be located."],
        }
        PayloadEmitter(json_enabled=args.json, human_printer=print_human).emit(payload)
        return 2

    report_issues, _ = validate_report(report_path)
    tomography_issues, tomography_payload = validate_tomography(tomography_path)
    summary = summary_from_payload(tomography_payload)
    issues = [*report_issues, *tomography_issues]
    payload = {
        "valid": not issues,
        "report_path": str(report_path),
        "tomography_path": str(tomography_path),
        "issues": issues,
        **summary,
    }
    PayloadEmitter(json_enabled=args.json, human_printer=print_human).emit(payload)
    return 0 if payload["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
