from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from common import (
    add_git_safe_directories,
    build_lean_path,
    configure_stdout,
    discover_package_lib_dirs,
    find_existing_proofs_root,
    git_safe_directories_for_proofs,
    find_lake,
    find_lean,
    subprocess_env_for_tool,
)


def missing_proofs_message() -> str:
    return (
        "No local Lean proofs project was found. Expected a `proofs/` directory in the current "
        "workspace or one of its parent directories. Run bootstrap_proofs.py first or create "
        "`proofs/lean-toolchain`, `proofs/lakefile.toml`, and `proofs/ProofScratch.lean` "
        "before retrying."
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Typecheck a Lean scratch file inside the local proofs project."
    )
    parser.add_argument(
        "--workspace",
        help="Workspace root or child directory to search from. Defaults to the current directory.",
    )
    parser.add_argument(
        "--file",
        default="ProofScratch.lean",
        help="Lean file inside proofs/ to typecheck.",
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "lake", "direct"],
        default="auto",
        help="Verification mode. `auto` tries `lake env lean` first, then falls back to direct lean.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON diagnostics.",
    )
    return parser.parse_args()


def run_command(command: list[str], cwd: Path, env: dict[str, str]) -> dict[str, object]:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "success": result.returncode == 0,
    }


def print_human_summary(payload: dict[str, object]) -> None:
    if payload["success"]:
        method = payload.get("verification_method", "unknown")
        print(f"Verified {payload['target']} via {method}.")
    else:
        print(f"Verification failed for {payload['target']}.", file=sys.stderr)

    print(f"workspace: {payload['workspace_root']}")
    print(f"proofs: {payload['proofs_dir']}")
    print(f"lake: {payload.get('lake_path') or 'not found'}")
    print(f"lean: {payload.get('lean_path') or 'not found'}")
    print(f"library paths: {payload['library_path_count']}")

    for method in payload["methods"]:
        label = method["name"]
        outcome = "ok" if method["success"] else f"failed ({method['returncode']})"
        print(f"{label}: {outcome}")
        stderr = str(method.get("stderr", "")).strip()
        if stderr:
            print(f"  stderr: {stderr.splitlines()[-1]}")


def main() -> int:
    configure_stdout()
    args = parse_args()
    root = find_existing_proofs_root(args.workspace)
    if root is None:
        payload = {
            "success": False,
            "error": missing_proofs_message(),
            "workspace_root": str(Path(args.workspace).resolve()) if args.workspace else str(Path.cwd().resolve()),
        }
        if args.json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print(missing_proofs_message(), file=sys.stderr)
        return 4

    proofs_dir = root / "proofs"
    target = Path(args.file)
    if not target.is_absolute():
        target = proofs_dir / target
    target = target.resolve()

    if not target.exists():
        payload = {
            "success": False,
            "error": f"Lean target not found: {target}",
            "workspace_root": str(root),
            "proofs_dir": str(proofs_dir),
            "target": str(target),
        }
        if args.json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print(f"Lean target not found: {target}", file=sys.stderr)
        return 1

    lake = find_lake()
    lean = find_lean(lake)
    lib_dirs = discover_package_lib_dirs(proofs_dir)
    relative_target = str(target.relative_to(proofs_dir))

    payload: dict[str, object] = {
        "success": False,
        "workspace_root": str(root),
        "proofs_dir": str(proofs_dir),
        "target": str(target),
        "lake_path": str(lake) if lake else None,
        "lean_path": str(lean) if lean else None,
        "library_paths": [str(path) for path in lib_dirs],
        "library_path_count": len(lib_dirs),
        "methods": [],
        "verification_method": None,
    }

    if args.mode in {"auto", "lake"} and lake is not None:
        lake_env = subprocess_env_for_tool(lake)
        add_git_safe_directories(lake_env, git_safe_directories_for_proofs(proofs_dir))
        record = run_command(
            [str(lake), "env", "lean", relative_target],
            cwd=proofs_dir,
            env=lake_env,
        )
        record["name"] = "lake env lean"
        payload["methods"].append(record)
        if record["success"]:
            payload["success"] = True
            payload["verification_method"] = "lake env lean"

    can_try_direct = args.mode in {"auto", "direct"} and lean is not None and len(lib_dirs) > 0
    if not payload["success"] and can_try_direct:
        env = subprocess_env_for_tool(lean)
        discovered_path = build_lean_path(proofs_dir)
        existing_path = env.get("LEAN_PATH", "")
        env["LEAN_PATH"] = (
            f"{discovered_path}{Path.pathsep}{existing_path}" if existing_path else discovered_path
        )
        record = run_command([str(lean), relative_target], cwd=proofs_dir, env=env)
        record["name"] = "direct lean with LEAN_PATH"
        payload["methods"].append(record)
        if record["success"]:
            payload["success"] = True
            payload["verification_method"] = "direct lean with LEAN_PATH fallback"

    if not payload["success"] and not payload["methods"]:
        missing = []
        if args.mode in {"auto", "lake"} and lake is None:
            missing.append("lake executable not found")
        if args.mode in {"auto", "direct"}:
            if lean is None:
                missing.append("lean executable not found")
            if not lib_dirs:
                missing.append("no compiled package libraries were found under proofs/.lake")
        payload["error"] = "; ".join(missing) or "No verification method could be attempted."

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print_human_summary(payload)

    return 0 if payload["success"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
