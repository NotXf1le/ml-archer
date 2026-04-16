from __future__ import annotations

import io
import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

from ml_archer.formal import setup as formal_setup


class SetupPluginTests(unittest.TestCase):
    def test_check_only_reports_needed_verify_setup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            args = Namespace(
                workspace=str(workspace),
                target="verify",
                check_only=True,
                yes=False,
                allow_network=False,
                timeout_seconds=30,
                json=True,
            )
            preflight = {
                "shared_workspace_writable": True,
                "ready_for_search": True,
                "ready_for_verification": False,
                "readiness_level": "search-ready",
                "lake_path": str(workspace / "lake.exe"),
                "lean_path": str(workspace / "lean.exe"),
                "proofs_exists": True,
                "mathlib_source_exists": True,
                "toolchain_compatible": True,
                "package_library_path_count": 1,
                "mathlib_artifact_exists": False,
                "next_steps": ["Run verify setup."],
            }

            stdout = io.StringIO()
            with (
                patch.object(formal_setup, "parse_args", return_value=args),
                patch.object(formal_setup.doctor, "build_payload", return_value=preflight),
                patch("sys.stdout", stdout),
            ):
                exit_code = formal_setup.main()

            payload = json.loads(stdout.getvalue())
            self.assertEqual(exit_code, 1)
            self.assertEqual(payload["status"], "needs_setup")
            self.assertEqual(payload["planned_steps"], ["Prepare shared verification workspace"])
            self.assertIn("Mathlib.olean is missing", payload["missing_requirements"])

    def test_json_mode_requires_yes_before_mutating_setup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            args = Namespace(
                workspace=str(workspace),
                target="search",
                check_only=False,
                yes=False,
                allow_network=False,
                timeout_seconds=30,
                json=True,
            )
            preflight = {
                "shared_workspace_writable": True,
                "ready_for_search": False,
                "ready_for_verification": False,
                "readiness_level": "incomplete",
                "lake_path": None,
                "lean_path": None,
                "proofs_exists": False,
                "mathlib_source_exists": False,
                "toolchain_compatible": False,
                "package_library_path_count": 0,
                "mathlib_artifact_exists": False,
                "next_steps": [],
            }

            stdout = io.StringIO()
            with (
                patch.object(formal_setup, "parse_args", return_value=args),
                patch.object(formal_setup.doctor, "build_payload", return_value=preflight),
                patch("sys.stdout", stdout),
            ):
                exit_code = formal_setup.main()

            payload = json.loads(stdout.getvalue())
            self.assertEqual(exit_code, 4)
            self.assertEqual(payload["status"], "needs_confirmation")
            self.assertEqual(
                payload["planned_steps"],
                ["Bootstrap Lean toolchain", "Prepare shared search workspace"],
            )

    def test_yes_mode_runs_toolchain_then_verify_setup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            args = Namespace(
                workspace=str(workspace),
                target="verify",
                check_only=False,
                yes=True,
                allow_network=True,
                timeout_seconds=30,
                json=True,
            )
            before = {
                "shared_workspace_writable": True,
                "ready_for_search": False,
                "ready_for_verification": False,
                "readiness_level": "incomplete",
                "lake_path": None,
                "lean_path": None,
                "proofs_exists": False,
                "mathlib_source_exists": False,
                "toolchain_compatible": False,
                "package_library_path_count": 0,
                "mathlib_artifact_exists": False,
                "next_steps": [],
            }
            after_toolchain = {
                **before,
                "lake_path": str(workspace / "lake.exe"),
                "lean_path": str(workspace / "lean.exe"),
            }
            final = {
                **after_toolchain,
                "ready_for_search": True,
                "ready_for_verification": True,
                "readiness_level": "verification-ready",
                "proofs_exists": True,
                "mathlib_source_exists": True,
                "toolchain_compatible": True,
                "package_library_path_count": 1,
                "mathlib_artifact_exists": True,
            }

            stdout = io.StringIO()
            with (
                patch.object(formal_setup, "parse_args", return_value=args),
                patch.object(formal_setup.doctor, "build_payload", side_effect=[before, before, after_toolchain, final, final]),
                patch.object(
                    formal_setup,
                    "run_json_step",
                    side_effect=[
                        {"success": True, "status": "success", "exit_code": 0},
                        {"success": True, "status": "success", "exit_code": 0},
                    ],
                ),
                patch("sys.stdout", stdout),
            ):
                exit_code = formal_setup.main()

            payload = json.loads(stdout.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertTrue(payload["success"])
            self.assertEqual(payload["readiness_after"], "verification-ready")
            self.assertEqual(
                [step["label"] for step in payload["steps"]],
                ["Bootstrap Lean toolchain", "Prepare shared verification workspace"],
            )


if __name__ == "__main__":
    unittest.main()

