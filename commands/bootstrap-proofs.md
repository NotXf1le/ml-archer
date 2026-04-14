# /bootstrap-proofs

Prepare the current workspace for mathlib-backed verification.

## Workflow

1. Inspect the workspace with `doctor.py`.
2. If `proofs/` is missing, create it with `bootstrap_proofs.py`.
3. Fetch mathlib sources and cache only when they are actually missing.
4. Create or preserve `proofs/ProofScratch.lean`.
5. Run `lean_check.py` and record the verification method.

## Expected Outputs

- a ready `proofs/` project
- `ProofScratch.lean`
- machine-readable bootstrap diagnostics when `--json` is used
