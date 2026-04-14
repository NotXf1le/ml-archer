from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from common import (
    add_git_safe_directories,
    configure_stdout,
    default_project_name,
    discover_package_lib_dirs,
    find_existing_proofs_root,
    find_lake,
    git_safe_directories_for_proofs,
    is_shared_workspace,
    requested_workspace_root,
    resolve_proofs_workspace,
    shared_workspace_root,
    subprocess_env_for_tool,
)


DEFAULT_SCRATCH = """import Mathlib

#check True.intro
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bootstrap a local proofs/ project, fetch mathlib, and validate the environment."
    )
    parser.add_argument(
        "--workspace",
        help="Workspace root or child directory. Defaults to the current directory.",
    )
    parser.add_argument(
        "--scope",
        choices=["auto", "local", "shared"],
        default="auto",
        help="Where to create or reuse the proofs project. `auto` prefers a repo-local proofs/ project and otherwise uses the shared CODEX_HOME cache.",
    )
    parser.add_argument(
        "--proofs-dir",
        default="proofs",
        help="Proof project directory relative to the workspace root.",
    )
    parser.add_argument(
        "--name",
        help="Lean project name used for `lake init`. Defaults to <WorkspaceName>Proofs.",
    )
    parser.add_argument(
        "--skip-update",
        action="store_true",
        help="Do not run `lake update` even if mathlib sources are missing.",
    )
    parser.add_argument(
        "--skip-cache",
        action="store_true",
        help="Do not run `lake exe cache get` even if compiled libraries are missing.",
    )
    parser.add_argument(
        "--skip-verify",
        action="store_true",
        help="Skip the final `lean_check.py` smoke test.",
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
        "cwd": str(cwd),
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "success": result.returncode == 0,
    }


def ensure_scratch_file(path: Path) -> None:
    if path.exists():
        return
    path.write_text(DEFAULT_SCRATCH, encoding="utf-8")


def print_human(payload: dict[str, object]) -> None:
    print(f"requested workspace: {payload['requested_workspace']}")
    print(f"selected workspace: {payload['workspace_root']} ({payload['selected_scope']})")
    print(f"proofs: {payload['proofs_dir']}")
    print(f"project initialized: {payload['project_initialized']}")
    print(f"scratch file present: {payload['proof_scratch_exists']}")
    for step in payload["steps"]:
        outcome = "ok" if step["success"] else f"failed ({step['returncode']})"
        print(f"{step['name']}: {outcome}")
        stderr = str(step.get("stderr", "")).strip()
        if stderr:
            print(f"  stderr: {stderr.splitlines()[-1]}")
    if payload.get("verification"):
        verification = payload["verification"]
        status = "ok" if verification.get("success") else "failed"
        print(f"verification: {status}")
        if verification.get("verification_method"):
            print(f"  method: {verification['verification_method']}")
    if payload["next_steps"]:
        print("next steps:")
        for step in payload["next_steps"]:
            print(f"  - {step}")


def main() -> int:
    configure_stdout()
    args = parse_args()
    requested_workspace = requested_workspace_root(args.workspace)
    local_workspace = find_existing_proofs_root(requested_workspace)
    resolved_workspace, resolved_scope = resolve_proofs_workspace(requested_workspace, args.scope)

    if args.scope == "local":
        workspace_root = resolved_workspace or requested_workspace
        selected_scope = "shared" if is_shared_workspace(workspace_root) else "local"
    elif args.scope == "shared":
        workspace_root = shared_workspace_root()
        selected_scope = "shared"
    else:
        workspace_root = resolved_workspace or shared_workspace_root()
        selected_scope = resolved_scope or "shared"

    proofs_dir = (workspace_root / args.proofs_dir).resolve()
    project_name = args.name or default_project_name(workspace_root)
    lake = find_lake()

    payload: dict[str, object] = {
        "requested_workspace": str(requested_workspace),
        "workspace_root": str(workspace_root),
        "selected_scope": selected_scope,
        "local_workspace_root": str(local_workspace) if local_workspace else None,
        "shared_workspace_root": str(shared_workspace_root()),
        "proofs_dir": str(proofs_dir),
        "project_initialized": False,
        "proof_scratch_exists": False,
        "steps": [],
        "verification": None,
        "next_steps": [],
        "success": False,
    }

    if lake is None:
        payload["next_steps"].append("Install Lean 4 so `lake` is available, then rerun bootstrap_proofs.py.")
        if args.json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print_human(payload)
        return 2

    env = subprocess_env_for_tool(lake)
    add_git_safe_directories(env, git_safe_directories_for_proofs(proofs_dir))
    project_ready = (proofs_dir / "lean-toolchain").exists() and (proofs_dir / "lakefile.toml").exists()

    if not project_ready:
        if proofs_dir.exists() and any(proofs_dir.iterdir()):
            payload["next_steps"].append(
                "The proofs/ directory already exists but is not a Lean project. Empty it or initialize it manually."
            )
            if args.json:
                print(json.dumps(payload, indent=2, ensure_ascii=False))
            else:
                print_human(payload)
            return 3

        proofs_dir.mkdir(parents=True, exist_ok=True)
        init_step = run_command([str(lake), "init", project_name, "math.toml"], cwd=proofs_dir, env=env)
        init_step["name"] = "lake init"
        payload["steps"].append(init_step)
        if not init_step["success"]:
            payload["next_steps"].append("Fix the `lake init` failure and rerun bootstrap_proofs.py.")
            if args.json:
                print(json.dumps(payload, indent=2, ensure_ascii=False))
            else:
                print_human(payload)
            return 4
        project_ready = True

    payload["project_initialized"] = project_ready

    scratch_path = proofs_dir / "ProofScratch.lean"
    ensure_scratch_file(scratch_path)
    payload["proof_scratch_exists"] = scratch_path.exists()

    mathlib_source = proofs_dir / ".lake" / "packages" / "mathlib" / "Mathlib"
    if not args.skip_update and not mathlib_source.exists():
        update_step = run_command([str(lake), "update"], cwd=proofs_dir, env=env)
        update_step["name"] = "lake update"
        payload["steps"].append(update_step)
        if not update_step["success"]:
            payload["next_steps"].append("`lake update` failed. Check network access and package state, then retry.")

    if not args.skip_cache and len(discover_package_lib_dirs(proofs_dir)) == 0:
        cache_step = run_command([str(lake), "exe", "cache", "get"], cwd=proofs_dir, env=env)
        cache_step["name"] = "lake exe cache get"
        payload["steps"].append(cache_step)
        if not cache_step["success"]:
            payload["next_steps"].append("`lake exe cache get` failed. Retry after `lake update` succeeds.")

    if not args.skip_verify:
        lean_check = Path(__file__).with_name("lean_check.py")
        verify_proc = subprocess.run(
            [sys.executable, str(lean_check), "--workspace", str(workspace_root), "--json"],
            cwd=proofs_dir,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        try:
            payload["verification"] = json.loads(verify_proc.stdout or "{}")
        except json.JSONDecodeError:
            payload["verification"] = {
                "success": False,
                "stdout": verify_proc.stdout,
                "stderr": verify_proc.stderr,
            }
        if not payload["verification"].get("success"):
            payload["next_steps"].append(
                "Verification did not pass. Inspect the JSON diagnostics from lean_check.py and retry."
            )

    payload["success"] = payload["project_initialized"] and not payload["next_steps"]

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print_human(payload)

    return 0 if payload["success"] else 5


if __name__ == "__main__":
    raise SystemExit(main())
