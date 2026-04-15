# /setup-plugin

Check whether the mathlib plugin is ready, then guide the user through the
required dependency download and shared-workspace setup.

## Workflow

1. Run `python scripts/setup_plugin.py --target search` for normal onboarding.
2. The script performs the same preflight checks as `doctor.py` and reports one of three states: `incomplete`, `search-ready`, or `verification-ready`.
3. If setup work is needed, it lists the missing components, asks for confirmation, and then runs the required phases with staged progress.
4. Use `python scripts/setup_plugin.py --target verify --yes` only when you intentionally want full Lean verification artifacts such as `Mathlib.olean`.
5. Use `--check-only` when you want a dry run and the recommended next command without mutating the environment.
6. Use `--timeout-seconds <n>` in slow or sandboxed environments.

## Expected Outputs

- a preflight readiness summary
- guided setup with confirmation before mutating state
- a shared `proofs/` workspace prepared for theorem search or full verification
- machine-readable JSON when `--json` is used
