# /bootstrap-proofs

Low-level shared-workspace bootstrap for mathlib-backed search or verification.

## Workflow

1. Use the root CLI entrypoint: `python scripts/doctor.py`.
2. Prefer `python scripts/setup_plugin.py --target search` for normal onboarding. Use `bootstrap_proofs.py` directly only when you need low-level control.
3. If `doctor.py` reports that `lake` / `lean` are unavailable, run `python scripts/bootstrap_toolchain.py` first so the plugin can use a cache-local toolchain.
4. Run `python scripts/bootstrap_proofs.py --target search` to create or repair the shared proofs workspace under `$CODEX_HOME/cache/mathlib-ml-arch/shared_workspace`.
5. Use `python scripts/bootstrap_proofs.py --target verify` only when you intentionally want full Lean verification artifacts. The default search target does not silently fall through to `lake build Mathlib`.
6. Fetch mathlib sources and cache only when they are actually missing.
7. Create or preserve `proofs/ProofScratch.lean`.
8. Run `python scripts/lean_check.py` and record the verification method when the target is verification-ready.
9. Use `--timeout-seconds <n>` in slow or sandboxed environments.
10. Read warnings in the bootstrap payload before retrying: late cleanup failures are non-fatal when required postconditions already hold.

## Expected Outputs

- a shared `proofs/` project at either `search-ready` or `verification-ready`
- `ProofScratch.lean`
- machine-readable bootstrap diagnostics when `--json` is used
- actionable fallback guidance when the shared CODEX_HOME cache is not writable
