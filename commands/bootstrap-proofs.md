# /bootstrap-proofs

Prepare the current workspace for mathlib-backed verification.

## Workflow

1. Use the root CLI entrypoint: `python scripts/doctor.py`.
2. If this repo needs its own Lean project, create it with `python scripts/bootstrap_proofs.py --scope local`.
3. Otherwise run `python scripts/bootstrap_proofs.py` and let it create or reuse the shared proofs workspace under `$CODEX_HOME/cache/mathlib-ml-arch/shared_workspace`.
4. Fetch mathlib sources and cache only when they are actually missing.
5. Create or preserve `proofs/ProofScratch.lean`.
6. Run `python scripts/lean_check.py` and record the verification method.

## Expected Outputs

- a ready repo-local or shared `proofs/` project
- `ProofScratch.lean`
- machine-readable bootstrap diagnostics when `--json` is used
