from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from ml_archer.formal import doctor, install_bundle
from ml_archer.formal.setup_workflow import SetupPlanner, SetupWorkflow, SetupWorkflowDependencies
from ml_archer.shared.common import configure_stdout, requested_workspace_root
from ml_archer.shared.script_output import PayloadEmitter, append_unique as append_unique_message


SCRIPT_MODULES = {
    "bootstrap_proofs.py": "ml_archer.formal.bootstrap_proofs",
    "bootstrap_toolchain.py": "ml_archer.formal.bootstrap_toolchain",
}


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--workspace",
        help="Workspace root or child directory to inspect. Defaults to the current directory.",
    )
    parser.add_argument(
        "--target",
        choices=["search", "verify"],
        default="search",
        help="Desired readiness level. `search` prepares theorem search, `verify` additionally prepares Lean verification artifacts.",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only inspect readiness and print the recommended next action.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Run the required setup steps without interactive confirmation.",
    )
    parser.add_argument(
        "--bundle",
        help="Install a prewarmed formal bundle before checking readiness.",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Do not attempt network bootstrap. Requires an existing cache or --bundle.",
    )
    parser.add_argument(
        "--allow-network",
        action="store_true",
        help="Explicitly allow network-backed bootstrap for the formal addon.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=900,
        help="Per-command timeout for child setup steps.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON.",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check whether the formal addon is ready, then guide the user through explicit setup for theorem search or Lean verification."
    )
    configure_parser(parser)
    return parser.parse_args()


def append_unique(items: list[str], message: str | None) -> None:
    append_unique_message(items, message)


def target_ready(payload: dict[str, object], target: str) -> bool:
    return SetupPlanner.target_ready(payload, target)


def readiness_level(payload: dict[str, object]) -> str:
    return SetupPlanner.readiness_level(payload)


def render_progress(index: int, total: int) -> str:
    width = 28
    completed = 0 if total <= 0 else round((index / total) * width)
    bar = "#" * completed + "-" * (width - completed)
    percent = 0 if total <= 0 else round((index / total) * 100)
    return f"[{bar}] {percent:>3d}%"


def missing_requirements(payload: dict[str, object], target: str) -> list[str]:
    return SetupPlanner.missing_requirements(payload, target)


def planned_steps(payload: dict[str, object], target: str, timeout_seconds: int) -> list[dict[str, object]]:
    return [
        {"label": step.label, "script": step.script, "args": list(step.args)}
        for step in SetupPlanner.planned_steps(payload, target, timeout_seconds)
    ]


def step_command(script_name: str, workspace_root: Path, args: list[str]) -> list[str]:
    module_name = SCRIPT_MODULES[script_name]
    command = [sys.executable, "-m", module_name]
    if script_name == "bootstrap_proofs.py":
        command.extend(["--workspace", str(workspace_root), "--scope", "shared"])
    command.extend(args)
    command.append("--json")
    return command


def run_json_step(script_name: str, workspace_root: Path, args: list[str], timeout_seconds: int) -> dict[str, object]:
    command = step_command(script_name, workspace_root, args)
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds + 30,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else str(exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else str(exc.stderr or "")
        return {
            "success": False,
            "status": "failure",
            "error": f"{script_name} timed out after {timeout_seconds + 30} seconds.",
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": None,
            "command": command,
        }

    try:
        payload = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        payload = {
            "success": False,
            "status": "failure",
            "error": f"{script_name} returned unreadable output.",
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    payload["exit_code"] = result.returncode
    payload["command"] = command
    return payload


def confirm_setup() -> bool:
    try:
        answer = input("Run setup now? [y/N]: ").strip().lower()
    except EOFError:
        return False
    return answer in {"y", "yes"}


def print_human(payload: dict[str, object]) -> None:
    print(f"status: {payload['status']}")
    print(f"target: {payload['target']}")
    print(f"requested workspace: {payload['requested_workspace']}")
    print(f"readiness before: {payload['readiness_before']}")
    print(f"readiness after: {payload['readiness_after']}")
    if payload["missing_requirements"]:
        print("missing:")
        for item in payload["missing_requirements"]:
            print(f"  - {item}")
    if payload["steps"]:
        print("steps:")
        for step in payload["steps"]:
            outcome = "ok" if step.get("success") else "failed"
            print(f"  - {step['label']}: {outcome}")
            if step.get("status"):
                print(f"    status: {step['status']}")
    if payload["next_steps"]:
        print("next steps:")
        for step in payload["next_steps"]:
            print(f"  - {step}")


def emit_payload(args: argparse.Namespace, payload: dict[str, object]) -> None:
    PayloadEmitter(json_enabled=args.json, human_printer=print_human).emit(payload)


def _workflow() -> SetupWorkflow:
    return SetupWorkflow(
        SetupWorkflowDependencies(
            build_preflight=doctor.build_payload,
            run_step=run_json_step,
        )
    )


def main_from_args(args: argparse.Namespace) -> int:
    configure_stdout()
    workspace_root = requested_workspace_root(args.workspace)
    bundle = getattr(args, "bundle", None)
    offline = bool(getattr(args, "offline", False))
    allow_network = bool(getattr(args, "allow_network", False))
    if bundle:
        install_bundle.install_bundle(Path(bundle).expanduser().resolve())

    preflight = doctor.build_payload(workspace_root, "shared")
    if SetupPlanner.target_ready(preflight, args.target):
        payload = {
            "requested_workspace": str(workspace_root),
            "target": args.target,
            "status": "success",
            "success": True,
            "preflight": preflight,
            "readiness_before": preflight.get("readiness_level"),
            "readiness_after": preflight.get("readiness_level"),
            "missing_requirements": [],
            "planned_steps": [],
            "steps": [],
            "next_steps": list(preflight.get("next_steps", [])),
        }
        emit_payload(args, payload)
        return 0

    if offline and args.yes:
        payload = {
            "requested_workspace": str(workspace_root),
            "target": args.target,
            "status": "blocked",
            "success": False,
            "preflight": preflight,
            "readiness_before": preflight.get("readiness_level"),
            "readiness_after": preflight.get("readiness_level"),
            "missing_requirements": missing_requirements(preflight, args.target),
            "planned_steps": [step["label"] for step in planned_steps(preflight, args.target, args.timeout_seconds)],
            "steps": [],
            "next_steps": [
                "Offline mode is enabled. Provide `--bundle <path>` or install the formal cache before retrying."
            ],
        }
        emit_payload(args, payload)
        return 6

    if not allow_network and args.yes:
        payload = {
            "requested_workspace": str(workspace_root),
            "target": args.target,
            "status": "blocked",
            "success": False,
            "preflight": preflight,
            "readiness_before": preflight.get("readiness_level"),
            "readiness_after": preflight.get("readiness_level"),
            "missing_requirements": missing_requirements(preflight, args.target),
            "planned_steps": [step["label"] for step in planned_steps(preflight, args.target, args.timeout_seconds)],
            "steps": [],
            "next_steps": [
                f"Rerun `python scripts/formal/setup.py --target {args.target} --allow-network --yes` to permit formal bootstrap."
            ],
        }
        emit_payload(args, payload)
        return 6

    workflow = _workflow()
    payload, return_code = workflow.execute(args, workspace_root)

    if return_code == -1:
        steps = planned_steps(payload["preflight"], args.target, args.timeout_seconds)
        print(f"{render_progress(1, len(steps) + 1)} Preflight complete")
        if payload["missing_requirements"]:
            print("Setup will address:")
            for item in payload["missing_requirements"]:
                print(f"  - {item}")
        if not confirm_setup():
            payload["status"] = "cancelled"
            payload["next_steps"] = [
                f"Run `python scripts/formal/setup.py --target {args.target} --allow-network --yes` when you want to download and configure the shared formal environment."
            ]
            emit_payload(args, payload)
            return 4
        args.yes = True
        payload, return_code = workflow.execute(args, workspace_root)

    emit_payload(args, payload)
    return int(return_code)


def main() -> int:
    return main_from_args(parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
