# Mathlib ML Architect Plugin

This plugin does one job: keep ML architecture reviews honest about what is
formally verified in Lean/mathlib, what is only engineering inference, and what
remains empirical or unavailable for formal verification in the current
workspace.

## Official Flow

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

4. Validate the final review bundle:

   ```bash
   python scripts/validate_artifact_bundle.py --bundle-dir <dir>
   ```

## Supported Product Surface

- `scripts/doctor.py`
- `scripts/setup_plugin.py`
- `scripts/search_mathlib.py`
- `scripts/lean_check.py`
- `scripts/validate_artifact_bundle.py`
- `references/architecture_contract.md`
- `references/mathlib_scope.md`
- `skills/mathlib-ml-arch/SKILL.md`

Low-level repair helpers such as `bootstrap_toolchain.py` and
`bootstrap_proofs.py` remain available for advanced/manual recovery, but they
are not the primary entry path.

## What This Plugin Does Not Do

- It does not present a fixture replay as a live architecture audit.
- It does not label a claim as formal support when Lean verification was not obtained.
- It does not ship the EML/formula tooling as part of the supported product surface.

## Example Only

`examples/run_demo_review.py` copies the bundled demo bundle from
`examples/demo-review/` into an output directory and validates it. It is an
example, not the main review flow.
