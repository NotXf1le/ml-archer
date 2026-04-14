from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import (
    configure_stdout,
    discover_package_lib_dirs,
    find_existing_proofs_root,
    find_lake,
    find_lean,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect the local Lean/mathlib workspace and emit agent-friendly diagnostics."
    )
    parser.add_argument(
        "--workspace",
        help="Workspace root or child directory to inspect. Defaults to the current directory.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of text.",
    )
    return parser.parse_args()


def build_payload(workspace_root: Path) -> dict[str, object]:
    proofs_dir = workspace_root / "proofs"
    lake = find_lake()
    lean = find_lean(lake)
    lib_dirs = discover_package_lib_dirs(proofs_dir) if proofs_dir.exists() else []
    mathlib_source = proofs_dir / ".lake" / "packages" / "mathlib" / "Mathlib"
    proof_scratch = proofs_dir / "ProofScratch.lean"

    payload = {
        "workspace_root": str(workspace_root),
        "proofs_dir": str(proofs_dir),
        "proofs_exists": proofs_dir.is_dir(),
        "lean_toolchain_exists": (proofs_dir / "lean-toolchain").exists(),
        "lakefile_exists": (proofs_dir / "lakefile.toml").exists(),
        "manifest_exists": (proofs_dir / "lake-manifest.json").exists(),
        "proof_scratch_exists": proof_scratch.exists(),
        "mathlib_source_exists": mathlib_source.exists(),
        "package_library_paths": [str(path) for path in lib_dirs],
        "package_library_path_count": len(lib_dirs),
        "lake_path": str(lake) if lake else None,
        "lean_path": str(lean) if lean else None,
        "ready_for_search": proofs_dir.is_dir(),
        "ready_for_lake_check": proofs_dir.is_dir() and lake is not None and proof_scratch.exists(),
        "ready_for_direct_lean": proofs_dir.is_dir() and lean is not None and proof_scratch.exists() and len(lib_dirs) > 0,
        "next_steps": [],
    }

    next_steps: list[str] = []
    if not payload["proofs_exists"]:
        next_steps.append("Run bootstrap_proofs.py to create a local proofs/ project.")
    if payload["proofs_exists"] and not payload["lean_toolchain_exists"]:
        next_steps.append("Create proofs/lean-toolchain or rerun bootstrap_proofs.py.")
    if payload["proofs_exists"] and not payload["lakefile_exists"]:
        next_steps.append("Create proofs/lakefile.toml or rerun bootstrap_proofs.py.")
    if lake is None:
        next_steps.append("Install Lean 4 so `lake` is available.")
    if lean is None:
        next_steps.append("Install Lean 4 so `lean` is available.")
    if payload["proofs_exists"] and not payload["mathlib_source_exists"]:
        next_steps.append("Run `lake update` inside proofs/ to fetch mathlib sources.")
    if payload["proofs_exists"] and len(lib_dirs) == 0:
        next_steps.append("Run `lake exe cache get` or build the proofs project to populate `.olean` files.")
    if payload["proofs_exists"] and not payload["proof_scratch_exists"]:
        next_steps.append("Create proofs/ProofScratch.lean for theorem verification.")

    payload["next_steps"] = next_steps
    return payload


def print_human(payload: dict[str, object]) -> None:
    print(f"workspace: {payload['workspace_root']}")
    print(f"proofs/: {'present' if payload['proofs_exists'] else 'missing'}")
    print(f"lake: {payload['lake_path'] or 'not found'}")
    print(f"lean: {payload['lean_path'] or 'not found'}")
    print(f"mathlib sources: {'present' if payload['mathlib_source_exists'] else 'missing'}")
    print(f"compiled library paths: {payload['package_library_path_count']}")
    print(f"ready for search: {payload['ready_for_search']}")
    print(f"ready for lake check: {payload['ready_for_lake_check']}")
    print(f"ready for direct lean: {payload['ready_for_direct_lean']}")
    if payload["next_steps"]:
        print("next steps:")
        for step in payload["next_steps"]:
            print(f"  - {step}")


def main() -> int:
    configure_stdout()
    args = parse_args()
    workspace_root = find_existing_proofs_root(args.workspace) or (
        Path(args.workspace).resolve() if args.workspace else Path.cwd().resolve()
    )
    payload = build_payload(workspace_root)

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print_human(payload)

    return 0 if payload["ready_for_search"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
