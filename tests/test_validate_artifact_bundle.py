from __future__ import annotations

import json
import os
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

from ml_archer.formal.validate_formal_bundle import resolve_targets, validate_evidence, validate_report


VALID_REPORT = """## Proposed architecture

- Example

## Formal evidence from mathlib

- Example

## Engineering inference built on top of formal facts

- Example

## Gaps requiring benchmarks or papers

- Example

## Risks

- Example
"""


class ValidateArtifactBundleTests(unittest.TestCase):
    def make_record(self) -> dict[str, object]:
        return {
            "name": "demo",
            "import_path": "generated::test",
            "plain_language_meaning": "Demo record.",
            "supported_subclaim": "Demo subclaim.",
            "unsupported_boundary": "Demo boundary.",
            "claim_label": "Formal support",
            "verified_in_lean": True,
            "verification_method": "lake env lean",
            "side_conditions": [
                {"kind": "domain", "condition": "x != 0", "status": "required"},
            ],
        }

    def test_valid_bundle_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp)
            (bundle / "report.md").write_text(VALID_REPORT, encoding="utf-8")
            (bundle / "evidence.json").write_text(
                json.dumps([self.make_record()], indent=2),
                encoding="utf-8",
            )

            report_issues, _ = validate_report(bundle / "report.md")
            evidence_issues, _ = validate_evidence(bundle / "evidence.json")

            self.assertFalse(report_issues)
            self.assertFalse(evidence_issues)

    def test_missing_verification_metadata_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp)
            bad = self.make_record()
            bad.pop("verified_in_lean")
            (bundle / "evidence.json").write_text(json.dumps([bad], indent=2), encoding="utf-8")

            evidence_issues, _ = validate_evidence(bundle / "evidence.json")

            self.assertTrue(any("verified_in_lean" in issue for issue in evidence_issues))

    def test_formal_support_requires_verified_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp)
            bad = self.make_record()
            bad["verified_in_lean"] = False
            (bundle / "evidence.json").write_text(json.dumps([bad], indent=2), encoding="utf-8")

            evidence_issues, _ = validate_evidence(bundle / "evidence.json")

            self.assertTrue(any("Formal support" in issue for issue in evidence_issues))

    def test_latest_resolution_uses_newest_report_across_plugin_and_workspace_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plugin_root = root / "plugin"
            workspace_root = root / "workspace"
            plugin_bundle = plugin_root / "reports" / "old_bundle"
            workspace_bundle = workspace_root / "reports" / "latest_bundle"
            plugin_bundle.mkdir(parents=True)
            workspace_bundle.mkdir(parents=True)

            plugin_report = plugin_bundle / "report.md"
            workspace_report = workspace_bundle / "architecture_audit_report_demo.md"
            plugin_evidence = plugin_bundle / "evidence.json"
            workspace_evidence = workspace_bundle / "evidence.json"

            plugin_report.write_text(VALID_REPORT, encoding="utf-8")
            workspace_report.write_text(VALID_REPORT, encoding="utf-8")
            plugin_evidence.write_text(json.dumps([self.make_record()], indent=2), encoding="utf-8")
            workspace_evidence.write_text(json.dumps([self.make_record()], indent=2), encoding="utf-8")

            os.utime(plugin_report, (10, 10))
            os.utime(workspace_report, (20, 20))

            args = Namespace(
                bundle_dir=None,
                report=None,
                evidence=None,
                latest=True,
                workspace=str(workspace_root),
                json=False,
            )

            with patch("ml_archer.formal.validate_formal_bundle.plugin_root", return_value=plugin_root):
                report_path, evidence_path = resolve_targets(args)

            self.assertEqual(report_path, workspace_report.resolve())
            self.assertEqual(evidence_path, workspace_evidence.resolve())


if __name__ == "__main__":
    unittest.main()
