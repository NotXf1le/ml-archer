# Mathlib ML Architect Plugin

This plugin now supports two companion flows for honest ML architecture review:

1. **Typed architecture tomography** for structural analysis via typed states, matrices,
   invariants, shortcut-path inspection, and train/infer congruence.
2. **Mathlib-backed verification** for the subset of subclaims that can be checked locally
   in Lean/mathlib.

The contract is strict:

- structural findings are **not** Lean verification;
- engineering inference stays separate from formal support;
- benchmark, deployment, and training claims stay empirical unless proven otherwise.

## Official Flows

### A. Structural flow

Use the `typed-architecture-tomography` skill to decompose the architecture into typed
states, operators, matrices, risks, and formalization candidates.

For nontrivial requests, emit a bundle and validate it:

```bash
python scripts/validate_tomography_bundle.py --bundle-dir <dir>
```

### B. Formal flow

1. Inspect readiness:

   ```bash
   python scripts/doctor.py
   ```

2. Prepare the shared workspace:

   ```bash
   python scripts/setup_plugin.py --target search
   python scripts/setup_plugin.py --target verify --yes
   ```

3. Search candidate facts and verify the exact Lean claim you want to cite:

   ```bash
   python scripts/search_mathlib.py "<query>"
   python scripts/lean_check.py --json
   ```

4. Validate the final formal review bundle:

   ```bash
   python scripts/validate_artifact_bundle.py --bundle-dir <dir>
   ```

## Supported Product Surface

- `scripts/doctor.py`
- `scripts/setup_plugin.py`
- `scripts/search_mathlib.py`
- `scripts/lean_check.py`
- `scripts/validate_artifact_bundle.py`
- `scripts/validate_tomography_bundle.py`
- `references/architecture_contract.md`
- `references/mathlib_scope.md`
- `references/tomography_contract.md`
- `references/tomography_scope.md`
- `references/matrix_legend.md`
- `references/claim_extraction_rules.md`
- `skills/mathlib-ml-arch/SKILL.md`
- `skills/typed-architecture-tomography/SKILL.md`

Low-level repair helpers such as `bootstrap_toolchain.py` and `bootstrap_proofs.py`
remain available for advanced/manual recovery, but they are not the primary entry path.

## What This Plugin Does Not Do

- It does not present a fixture replay as a live architecture audit.
- It does not label a structural finding as formal support when Lean verification was not obtained.
- It does not infer benchmark wins, optimizer stability, or deployment gains from clean matrices.
- It does not treat shape equality as semantic compatibility.

## Example Only

- `examples/run_demo_review.py` copies the bundled formal demo bundle from
  `examples/demo-review/` into an output directory and validates it.
- `examples/run_demo_tomography.py` copies the bundled structural demo bundle from
  `examples/demo-tomography/` into an output directory and validates it.

Both are examples, not the main audit flow.
