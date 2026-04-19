from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def run_python(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=cwd or PLUGIN_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def failure_message(result: subprocess.CompletedProcess[str]) -> str:
    return f"exit={result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"


class ScriptEntrypointTests(unittest.TestCase):
    def test_archer_script_validates_demo_bundle(self) -> None:
        result = run_python(
            "scripts/archer.py",
            "tomography",
            "validate",
            "--bundle-dir",
            "examples/demo-tomography",
            "--json",
        )

        self.assertEqual(result.returncode, 0, failure_message(result))
        payload = json.loads(result.stdout)
        self.assertTrue(payload["valid"])

    def test_validator_script_validates_demo_bundle(self) -> None:
        result = run_python(
            "scripts/validate_tomography_bundle.py",
            "--bundle-dir",
            "examples/demo-tomography",
            "--json",
        )

        self.assertEqual(result.returncode, 0, failure_message(result))
        payload = json.loads(result.stdout)
        self.assertTrue(payload["valid"])

    def test_demo_runner_reports_successful_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "demo-output"
            result = run_python(
                "examples/run_demo_tomography.py",
                "--output-dir",
                str(output_dir),
                "--json",
            )

        self.assertEqual(result.returncode, 0, failure_message(result))
        payload = json.loads(result.stdout)
        self.assertEqual(payload["report_path"], str(output_dir / "report.md"))
        self.assertEqual(payload["tomography_path"], str(output_dir / "tomography.json"))
        self.assertTrue(payload["validation"]["valid"])
        self.assertEqual(payload["validation"]["validator_exit_code"], 0)


if __name__ == "__main__":
    unittest.main()
