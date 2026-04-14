# Mathlib ML Architect Plugin

This plugin packages the `mathlib-ml-arch` skill as a production-ready Codex
plugin focused on disciplined ML architecture audits.

## What It Does

- separates formal support, engineering inference, and empirical gaps
- bootstraps a local `proofs/` project when the workspace does not already have one
- inspects the local Lean/mathlib environment with agent-friendly diagnostics
- searches local Lean/mathlib evidence before making formal claims
- returns ranked theorem candidates with names, import paths, and source locations
- verifies `ProofScratch.lean` through `lake env lean` with direct `lean` fallback
- emits a compact artifact bundle with `report.md` and `evidence.json`
- runs a lightweight post-write validation pass over audit artifacts

## Layout

- `.codex-plugin/plugin.json`
  - plugin manifest consumed by Codex
- `skills/mathlib-ml-arch/`
  - skill instructions, references, and local helper scripts
- `commands/`
  - workflow docs for review and recheck flows
- `fixtures/review-architecture/`
  - sample `report.md` and `evidence.json` bundle for smoke checks
- `hooks.json`
  - triggers the post-write artifact validation script
- `scripts/post_write_mathlib_audit_check.ps1`
  - validates report structure and evidence record completeness

## Artifact Contract

For nontrivial reviews, the plugin expects a compact bundle alongside the
written response:

- `report.md`
- `evidence.json`

The report must follow the required section order defined in
`skills/mathlib-ml-arch/references/architecture_contract.md`. The evidence file
must stay machine-readable and aligned with the report.

## Runtime Model

The plugin is skill-only. It does not ship a custom UI, widget runtime, or
local server layer. The only runtime behavior beyond the skill itself is the
post-write validation hook, which checks the latest review bundle for required
sections and evidence fields.

## Lean Prerequisites

Formal mathlib checks are workspace-dependent. This plugin does not bundle a
pre-fetched mathlib checkout, but it does ship bootstrap and diagnostics
helpers for the target workspace.

Recommended sequence:

1. Run `scripts/doctor.py` to inspect the current workspace state.
2. If `proofs/` is missing, run `scripts/bootstrap_proofs.py`.
3. Use `scripts/search_mathlib.py` to retrieve theorem candidates.
4. Use `scripts/lean_check.py` to validate `proofs/ProofScratch.lean`.

When `lake env lean` is unavailable but compiled package libraries exist,
`lean_check.py` can fall back to direct `lean` with a discovered `LEAN_PATH`
and records that verification method explicitly.

On sandboxed Windows runs, the plugin also injects temporary `git safe.directory`
entries for `proofs/.lake/packages/*`, which prevents `lake` from failing on
package repos owned by a different local user.

If `proofs/` is missing, agents should report that local formal verification is
unavailable rather than blaming `lake`, `git`, or missing theorems.
