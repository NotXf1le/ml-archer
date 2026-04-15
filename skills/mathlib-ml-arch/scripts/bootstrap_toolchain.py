from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from common import (
    configure_stdout,
    find_cached_tool,
    find_elan,
    prepare_writable_directory,
    resolve_fallback_tool_homes,
    safe_resolve,
    subprocess_env_for_tool,
    writability_error,
)


def plugin_root() -> Path:
    return Path(__file__).resolve().parents[3]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Populate a plugin-local Lean/Lake toolchain cache under CODEX_HOME instead of relying on the host profile."
    )
    parser.add_argument(
        "--toolchain",
        default="stable",
        help="Lean toolchain passed to `elan toolchain install` when a cached copy cannot be produced from the host toolchain.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-copy the active host toolchain into the plugin cache even when a cached toolchain already exists.",
    )
    parser.add_argument(
        "--skip-install",
        action="store_true",
        help="Do not call `elan toolchain install`; only copy an already-active host toolchain into the plugin cache.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=300,
        help="Per-command timeout for `elan` subprocesses.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable diagnostics.",
    )
    return parser.parse_args()


def detect_tool_version(tool: Path | None) -> str | None:
    if tool is None:
        return None

    try:
        result = subprocess.run(
            [str(tool), "--version"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
            env=subprocess_env_for_tool(tool),
        )
    except (OSError, subprocess.TimeoutExpired):
        return None

    output = (result.stdout or result.stderr).strip()
    if not output:
        return None
    return output.splitlines()[0]


def append_unique(items: list[str], message: str | None) -> None:
    if message and message not in items:
        items.append(message)


def emit_payload(args: argparse.Namespace, payload: dict[str, object]) -> None:
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print_human(payload)


def run_command(
    command: list[str],
    cwd: Path,
    env: dict[str, str],
    timeout_seconds: int,
) -> dict[str, object]:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
        )
        return {
            "command": command,
            "cwd": str(cwd),
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0,
            "timed_out": False,
            "timeout_seconds": timeout_seconds,
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else str(exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else str(exc.stderr or "")
        return {
            "command": command,
            "cwd": str(cwd),
            "returncode": None,
            "stdout": stdout,
            "stderr": f"{stderr.rstrip()}\nCommand timed out after {timeout_seconds} seconds.".strip(),
            "success": False,
            "timed_out": True,
            "timeout_seconds": timeout_seconds,
        }


def build_tool_env(elan: Path, target_home: Path, target_elan_home: Path) -> dict[str, str]:
    env = subprocess_env_for_tool(elan)
    env["HOME"] = str(target_home)
    env["USERPROFILE"] = str(target_home)
    env["ELAN_HOME"] = str(target_elan_home)
    env["PATH"] = f"{target_elan_home / 'bin'}{os.pathsep}{env.get('PATH', '')}"
    return env


def cache_elan_binary(source_elan: Path, target_elan_home: Path) -> Path:
    target_bin = target_elan_home / "bin"
    target_bin.mkdir(parents=True, exist_ok=True)
    target = safe_resolve(target_bin / source_elan.name)
    if safe_resolve(source_elan) != target:
        shutil.copy2(source_elan, target)
    return target


def active_toolchain_root(elan: Path, timeout_seconds: int) -> tuple[Path | None, dict[str, object]]:
    step = run_command(
        [str(elan), "which", "lean"],
        cwd=plugin_root(),
        env=subprocess_env_for_tool(elan),
        timeout_seconds=timeout_seconds,
    )
    step["name"] = "elan which lean"
    if not step["success"]:
        return None, step

    line = next((part.strip() for part in str(step.get("stdout", "")).splitlines() if part.strip()), "")
    candidate = Path(line).expanduser() if line else None
    if candidate is None or not candidate.exists() or candidate.parent.name != "bin":
        step["success"] = False
        step["stderr"] = f"{step.get('stderr', '')}\nCould not resolve the active Lean toolchain root.".strip()
        return None, step

    return safe_resolve(candidate.parent.parent), step


def copy_toolchain_tree(source_root: Path, target_elan_home: Path, force: bool) -> tuple[Path, dict[str, object]]:
    target_root = safe_resolve(target_elan_home / "toolchains" / source_root.name)
    target_root.parent.mkdir(parents=True, exist_ok=True)

    if target_root.exists() and not force:
        return target_root, {
            "name": "copy active toolchain",
            "success": True,
            "stdout": f"Toolchain already cached at {target_root}.",
            "stderr": "",
            "returncode": 0,
        }

    shutil.copytree(source_root, target_root, dirs_exist_ok=True)
    return target_root, {
        "name": "copy active toolchain",
        "success": True,
        "stdout": f"Copied {source_root} to {target_root}.",
        "stderr": "",
        "returncode": 0,
    }


def refresh_cached_tools(payload: dict[str, object]) -> tuple[Path | None, Path | None, Path | None]:
    cached_elan = find_cached_tool("elan")
    cached_lake = find_cached_tool("lake")
    cached_lean = find_cached_tool("lean")
    payload["cached_elan_path"] = str(cached_elan) if cached_elan else None
    payload["cached_lake_path"] = str(cached_lake) if cached_lake else None
    payload["cached_lean_path"] = str(cached_lean) if cached_lean else None
    payload["cached_lake_version"] = detect_tool_version(cached_lake)
    payload["cached_lean_version"] = detect_tool_version(cached_lean)
    return cached_elan, cached_lake, cached_lean


def print_human(payload: dict[str, object]) -> None:
    print(f"status: {payload['status']}")
    print(f"target HOME: {payload['target_home']}")
    print(f"target ELAN_HOME: {payload['target_elan_home']}")
    print(f"source elan: {payload.get('source_elan_path') or 'missing'}")
    print(f"cached elan: {payload.get('cached_elan_path') or 'missing'}")
    print(f"cached lake: {payload.get('cached_lake_path') or 'missing'}")
    if payload.get("cached_lake_version"):
        print(f"  version: {payload['cached_lake_version']}")
    print(f"cached lean: {payload.get('cached_lean_path') or 'missing'}")
    if payload.get("cached_lean_version"):
        print(f"  version: {payload['cached_lean_version']}")
    for step in payload["steps"]:
        outcome = "ok" if step.get("success") else "failed"
        print(f"{step['name']}: {outcome}")
        stderr = str(step.get("stderr", "")).strip()
        if stderr:
            print(f"  stderr: {stderr.splitlines()[-1]}")
    if payload["warnings"]:
        print("warnings:")
        for warning in payload["warnings"]:
            print(f"  - {warning}")
    if payload["next_steps"]:
        print("next steps:")
        for step in payload["next_steps"]:
            print(f"  - {step}")


def main() -> int:
    configure_stdout()
    args = parse_args()
    target_home, target_elan_home = resolve_fallback_tool_homes()
    payload: dict[str, object] = {
        "status": "failure",
        "target_home": str(target_home),
        "target_elan_home": str(target_elan_home),
        "source_elan_path": None,
        "cached_elan_path": None,
        "cached_lake_path": None,
        "cached_lean_path": None,
        "cached_lake_version": None,
        "cached_lean_version": None,
        "steps": [],
        "warnings": [],
        "next_steps": [],
        "success": False,
    }

    home_error = writability_error(target_home)
    elan_error = writability_error(target_elan_home)
    if home_error is not None and not prepare_writable_directory(target_home):
        append_unique(payload["next_steps"], f"Tool HOME is not writable: {target_home} ({home_error}).")
    if elan_error is not None and not prepare_writable_directory(target_elan_home):
        append_unique(payload["next_steps"], f"ELAN_HOME is not writable: {target_elan_home} ({elan_error}).")
    if payload["next_steps"]:
        append_unique(
            payload["next_steps"],
            "Set CODEX_HOME to a writable directory and rerun bootstrap_toolchain.py.",
        )
        emit_payload(args, payload)
        return 3

    _, cached_lake, cached_lean = refresh_cached_tools(payload)
    if cached_lake is not None and cached_lean is not None and not args.force:
        payload["success"] = True
        payload["status"] = "success"
        emit_payload(args, payload)
        return 0

    elan = find_elan()
    payload["source_elan_path"] = str(elan) if elan else None
    if elan is None:
        append_unique(
            payload["next_steps"],
            "No `elan` executable was found. Install Lean once globally or provide a portable `elan` binary, then rerun bootstrap_toolchain.py.",
        )
        emit_payload(args, payload)
        return 2

    cached_elan = cache_elan_binary(elan, target_elan_home)
    payload["steps"].append(
        {
            "name": "cache elan binary",
            "success": True,
            "stdout": f"Cached elan at {cached_elan}.",
            "stderr": "",
            "returncode": 0,
        }
    )

    active_root, host_step = active_toolchain_root(elan, args.timeout_seconds)
    payload["steps"].append(host_step)
    if active_root is not None:
        copied_root, copy_step = copy_toolchain_tree(active_root, target_elan_home, args.force)
        payload["steps"].append(copy_step)
        if safe_resolve(copied_root) == safe_resolve(active_root):
            append_unique(
                payload["warnings"],
                "The active Lean toolchain was already under the plugin cache; no host-to-cache copy was needed.",
            )

    _, cached_lake, cached_lean = refresh_cached_tools(payload)
    if (cached_lake is None or cached_lean is None) and not args.skip_install:
        target_elan = cached_elan if cached_elan.exists() else elan
        tool_env = build_tool_env(target_elan, target_home, target_elan_home)
        install_step = run_command(
            [str(target_elan), "toolchain", "install", args.toolchain],
            cwd=plugin_root(),
            env=tool_env,
            timeout_seconds=args.timeout_seconds,
        )
        install_step["name"] = "elan toolchain install"
        payload["steps"].append(install_step)

        if install_step["success"]:
            default_step = run_command(
                [str(target_elan), "default", args.toolchain],
                cwd=plugin_root(),
                env=tool_env,
                timeout_seconds=args.timeout_seconds,
            )
            default_step["name"] = "elan default"
            payload["steps"].append(default_step)
            if not default_step["success"]:
                append_unique(
                    payload["warnings"],
                    "`elan default` did not complete cleanly. The plugin will still use direct toolchain binaries when they are present in the cache.",
                )

    _, cached_lake, cached_lean = refresh_cached_tools(payload)
    payload["success"] = cached_lake is not None and cached_lean is not None
    payload["status"] = "success" if payload["success"] else "failure"

    if not payload["success"]:
        if args.skip_install:
            append_unique(
                payload["next_steps"],
                "No cached `lake` / `lean` binaries were produced from the active host toolchain. Rerun without `--skip-install` to let `elan` install into the plugin cache.",
            )
        else:
            append_unique(
                payload["next_steps"],
                "The plugin-local toolchain is still incomplete. Check the `elan` stderr above and rerun once network access or toolchain installation is available.",
            )

    emit_payload(args, payload)
    return 0 if payload["success"] else 5


if __name__ == "__main__":
    raise SystemExit(main())
