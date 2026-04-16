from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

from ml_archer.formal import bootstrap_toolchain


class BootstrapToolchainTests(unittest.TestCase):
    def tool_name(self, base: str) -> str:
        return f"{base}.exe" if sys.platform == "win32" else base

    def test_main_reports_success_when_cached_toolchain_is_already_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target_home = Path(tmp) / "toolchains" / "home"
            target_elan = Path(tmp) / "toolchains" / "elan"
            cached_lake = target_elan / "toolchains" / "demo" / "bin" / self.tool_name("lake")
            cached_lean = target_elan / "toolchains" / "demo" / "bin" / self.tool_name("lean")
            cached_lake.parent.mkdir(parents=True, exist_ok=True)
            cached_lake.write_text("", encoding="utf-8")
            cached_lean.write_text("", encoding="utf-8")

            args = Namespace(toolchain="stable", force=False, skip_install=False, timeout_seconds=5, json=True)
            stdout = io.StringIO()

            def fake_find_cached_tool(name: str):
                mapping = {
                    "elan": None,
                    "lake": cached_lake if cached_lake.exists() else None,
                    "lean": cached_lean if cached_lean.exists() else None,
                }
                return mapping.get(name)

            with (
                patch.object(bootstrap_toolchain, "parse_args", return_value=args),
                patch.object(bootstrap_toolchain, "resolve_fallback_tool_homes", return_value=(target_home, target_elan)),
                patch.object(bootstrap_toolchain, "writability_error", return_value=None),
                patch.object(bootstrap_toolchain, "find_cached_tool", side_effect=fake_find_cached_tool),
                patch.object(
                    bootstrap_toolchain,
                    "detect_tool_version",
                    side_effect=lambda path: f"fake:{Path(path).name}" if path else None,
                ),
                patch("sys.stdout", stdout),
            ):
                exit_code = bootstrap_toolchain.main()

            payload = json.loads(stdout.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertTrue(payload["success"])
            self.assertEqual(payload["status"], "success")
            self.assertEqual(Path(payload["cached_lake_path"]), cached_lake.resolve())
            self.assertEqual(Path(payload["cached_lean_path"]), cached_lean.resolve())

    def test_main_copies_active_host_toolchain_into_plugin_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target_home = root / "toolchains" / "home"
            target_elan = root / "toolchains" / "elan"
            source_elan = root / self.tool_name("elan")
            source_elan.write_text("", encoding="utf-8")
            source_toolchain = root / "host-toolchain"
            source_lake = source_toolchain / "bin" / self.tool_name("lake")
            source_lean = source_toolchain / "bin" / self.tool_name("lean")
            source_lake.parent.mkdir(parents=True, exist_ok=True)
            source_lake.write_text("", encoding="utf-8")
            source_lean.write_text("", encoding="utf-8")

            args = Namespace(toolchain="stable", force=False, skip_install=True, timeout_seconds=5, json=True)
            stdout = io.StringIO()

            def fake_find_cached_tool(name: str):
                cached = {
                    "elan": target_elan / "bin" / source_elan.name,
                    "lake": target_elan / "toolchains" / source_toolchain.name / "bin" / source_lake.name,
                    "lean": target_elan / "toolchains" / source_toolchain.name / "bin" / source_lean.name,
                }.get(name)
                if cached is not None and cached.exists():
                    return cached.resolve()
                return None

            with (
                patch.object(bootstrap_toolchain, "parse_args", return_value=args),
                patch.object(bootstrap_toolchain, "resolve_fallback_tool_homes", return_value=(target_home, target_elan)),
                patch.object(bootstrap_toolchain, "writability_error", return_value=None),
                patch.object(bootstrap_toolchain, "prepare_writable_directory", return_value=True),
                patch.object(bootstrap_toolchain, "find_cached_tool", side_effect=fake_find_cached_tool),
                patch.object(bootstrap_toolchain, "find_elan", return_value=source_elan),
                patch.object(
                    bootstrap_toolchain,
                    "active_toolchain_root",
                    return_value=(
                        source_toolchain,
                        {
                            "name": "elan which lean",
                            "success": True,
                            "stdout": str(source_lean),
                            "stderr": "",
                            "returncode": 0,
                        },
                    ),
                ),
                patch.object(
                    bootstrap_toolchain,
                    "detect_tool_version",
                    side_effect=lambda path: f"fake:{Path(path).name}" if path else None,
                ),
                patch("sys.stdout", stdout),
            ):
                exit_code = bootstrap_toolchain.main()

            payload = json.loads(stdout.getvalue())
            copied_lake = target_elan / "toolchains" / source_toolchain.name / "bin" / source_lake.name
            copied_lean = target_elan / "toolchains" / source_toolchain.name / "bin" / source_lean.name
            copied_elan = target_elan / "bin" / source_elan.name

            self.assertEqual(exit_code, 0)
            self.assertTrue(payload["success"])
            self.assertTrue(copied_elan.exists())
            self.assertTrue(copied_lake.exists())
            self.assertTrue(copied_lean.exists())
            self.assertEqual(Path(payload["cached_lake_path"]), copied_lake.resolve())
            self.assertEqual(Path(payload["cached_lean_path"]), copied_lean.resolve())


if __name__ == "__main__":
    unittest.main()

