# /bootstrap-toolchain

Populate a plugin-local Lean/Lake toolchain cache under `$CODEX_HOME/cache/mathlib-ml-arch/toolchains`, with automatic temp-cache fallback when that root is not writable.

## Workflow

1. Use the root CLI entrypoint: `python scripts/bootstrap_toolchain.py`.
2. Cache the `elan` launcher into the plugin toolchain cache.
3. Prefer copying the currently active host Lean toolchain into the plugin cache instead of downloading again.
4. If no usable host toolchain is active, let `elan toolchain install` populate the plugin-local `ELAN_HOME`.
5. Confirm the plugin-local cache exposes `lake` and `lean`.
6. Run `python scripts/doctor.py` after bootstrap if you want to confirm that future plugin runs will use the cached toolchain.

## Expected Outputs

- plugin-local `lake` / `lean` binaries under `$CODEX_HOME/cache/mathlib-ml-arch/toolchains` or the temp fallback cache
- machine-readable bootstrap diagnostics when `--json` is used
- no requirement to keep the target repo itself under `proofs/` or to rely on the host profile `~/.elan`
