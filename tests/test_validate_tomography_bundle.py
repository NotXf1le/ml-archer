from __future__ import annotations

import json
import os
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

from ml_archer.tomography.validate_bundle import resolve_targets, validate_report, validate_tomography

VALID_REPORT = """## Architecture decomposition

- Example.

## Typed state inventory

- Example.

## Operator-state matrix

- Example.

## Supervision and gradient reachability

- Example.

## Shortcut and path dominance

- Example.

## Invariants and singularities

- Example.

## Train/infer congruence

- Example.

## Formalization candidates

- Example.

## Empirical-only claims

- Example.

## Risks and redesign guidance

- Example.
"""


class ValidateTomographyBundleTests(unittest.TestCase):
    def make_payload(self) -> dict[str, object]:
        return {
            "architecture_name": "Demo controller",
            "architecture_summary": "A typed controller with key/query separation.",
            "assumptions": ["Equations are explicit in the example."],
            "typed_states": [
                {
                    "state_id": "slot_key",
                    "symbol": "K",
                    "semantic_role": "persistent_key",
                    "shape": "B x S x D",
                    "space": "R^D",
                    "geometry": "euclidean",
                    "time_role": "t",
                    "persistence": "persistent",
                    "producer_ops": ["key_update"],
                    "consumer_ops": ["router"],
                }
            ],
            "operators": [
                {
                    "operator_id": "key_update",
                    "equation_or_rule": "K' <- EMA(K, φ(q_ctx))",
                    "purpose": "Refresh persistent keys.",
                    "reads": ["slot_key", "q_ctx"],
                    "writes": ["slot_key_next"],
                    "mode": "both",
                }
            ],
            "operator_state_matrix": {
                "states": ["slot_key"],
                "rows": [{"operator_id": "key_update", "cells": {"slot_key": "U"}}],
            },
            "supervision_matrix": {
                "rows": [{"loss_id": "align_loss", "cells": {"slot_key": "indirect"}, "notes": "Indirect only."}]
            },
            "shortcut_paths": [
                {
                    "shortcut_id": "shortcut_1",
                    "claim_or_output": "decoder output",
                    "intended_path": "encoder -> bottleneck -> decoder",
                    "shortcut_path": "metadata -> decoder",
                    "status": "present",
                    "risk_summary": "Metadata bypasses the bottleneck.",
                }
            ],
            "invariants": [
                {
                    "invariant_id": "inv_1",
                    "statement": "Key/query separation is preserved.",
                    "statuses": {"key_update": "requires_precondition"},
                    "boundary": "Needs an explicit map φ from query-space to key-space.",
                }
            ],
            "train_infer_congruence": {
                "status": "partial_mismatch",
                "train_path": "teacher-forced state updates",
                "infer_path": "self-fed recursive updates",
                "mismatch_points": ["teacher forcing removed at inference"],
                "notes": "Congruence is incomplete.",
            },
            "findings": [
                {
                    "finding_id": "finding_1",
                    "finding_label": "Type violation risk",
                    "severity": "high",
                    "summary": "Key update is unsafe without an explicit cast.",
                    "basis": "explicit_equation",
                    "confidence": "high",
                    "evidence_refs": ["key_update", "inv_1"],
                    "boundary": "The report does not prove runtime failure.",
                    "recommended_action": "Insert and document φ: query -> persistent_key.",
                }
            ],
            "formalization_candidates": [
                {
                    "candidate_id": "fc_1",
                    "natural_language_claim": "Projection used in the key normalizer is idempotent.",
                    "reason_it_is_formalizable": "This is a local linear-algebraic claim.",
                    "target_backend": "mathlib",
                    "theorem_family": "projection/idempotence",
                    "search_terms": ["projection idempotent", "orthogonal projection"],
                    "suggested_import_nouns": ["LinearMap", "Submodule", "Projection"],
                    "side_conditions": ["projection target is a well-defined subspace"],
                }
            ],
            "empirical_only_claims": [
                {
                    "claim_id": "emp_1",
                    "claim": "This controller improves retrieval quality.",
                    "why_empirical": "Depends on data and benchmarks.",
                    "required_evidence": ["ablation", "benchmark results"],
                }
            ],
        }

    def test_valid_bundle_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp)
            (bundle / "report.md").write_text(VALID_REPORT, encoding="utf-8")
            (bundle / "tomography.json").write_text(json.dumps(self.make_payload(), indent=2), encoding="utf-8")

            report_issues, _ = validate_report(bundle / "report.md")
            tomography_issues, _ = validate_tomography(bundle / "tomography.json")

            self.assertFalse(report_issues)
            self.assertFalse(tomography_issues)

    def test_forbidden_formal_key_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp)
            bad = self.make_payload()
            bad["findings"][0]["verified_in_lean"] = False
            (bundle / "tomography.json").write_text(json.dumps(bad, indent=2), encoding="utf-8")

            issues, _ = validate_tomography(bundle / "tomography.json")

            self.assertTrue(any("verified_in_lean" in issue for issue in issues))

    def test_missing_top_level_field_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp)
            bad = self.make_payload()
            bad.pop("train_infer_congruence")
            (bundle / "tomography.json").write_text(json.dumps(bad, indent=2), encoding="utf-8")

            issues, _ = validate_tomography(bundle / "tomography.json")

            self.assertTrue(any("train_infer_congruence" in issue for issue in issues))

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
            workspace_report = workspace_bundle / "architecture_tomography_report_demo.md"
            plugin_tomography = plugin_bundle / "tomography.json"
            workspace_tomography = workspace_bundle / "tomography.json"

            plugin_report.write_text(VALID_REPORT, encoding="utf-8")
            workspace_report.write_text(VALID_REPORT, encoding="utf-8")
            plugin_tomography.write_text(json.dumps(self.make_payload(), indent=2), encoding="utf-8")
            workspace_tomography.write_text(json.dumps(self.make_payload(), indent=2), encoding="utf-8")

            os.utime(plugin_report, (10, 10))
            os.utime(workspace_report, (20, 20))

            args = Namespace(
                bundle_dir=None,
                report=None,
                tomography=None,
                latest=True,
                workspace=str(workspace_root),
                json=False,
            )

            with patch("ml_archer.tomography.validate_bundle.plugin_root", return_value=plugin_root):
                report_path, tomography_path = resolve_targets(args)

            self.assertEqual(report_path, workspace_report.resolve())
            self.assertEqual(tomography_path, workspace_tomography.resolve())


if __name__ == "__main__":
    unittest.main()
