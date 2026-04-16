---
name: mathlib-ml-arch
description: Ground ML architecture reasoning in Lean mathlib evidence. Use when the task involves ML architecture proposals, invariants, probabilistic semantics, linear algebra correctness, numerical stability, optimizer-side reasoning, or any mathematical claim that should be separated into formal support, engineering inference, and empirical gaps.
---

# Mathlib-Backed ML Architecture

Use this skill when the user needs one honest split:

- locally verified Lean/mathlib support
- engineering inference built on top of formal facts
- empirical gaps or places where formal verification is unavailable here

## Required Reading

1. Read `../../references/architecture_contract.md` first.
2. Read `../../references/mathlib_scope.md` when you need theorem-family boundaries or search strategy.
3. If the request originated from `typed-architecture-tomography`, treat its `formalization_candidates`
   as search seeds only. They are not evidence.

## Official Workflow

1. Inspect the environment:

```bash
python "../../scripts/doctor.py"
```

2. If the workspace is not ready, use the guided setup path:

```bash
python "../../scripts/setup_plugin.py" --target search
```

Use `--target verify --yes` only when the task requires actual Lean verification artifacts.

3. Search candidate theorems:

```bash
python "../../scripts/search_mathlib.py" "<query>"
```

4. Verify the concrete Lean claim before calling it formal support:

```bash
python "../../scripts/lean_check.py" --json
```

5. For nontrivial reviews, emit `report.md` and `evidence.json`, then validate them:

```bash
python "../../scripts/validate_artifact_bundle.py" --bundle-dir "<dir>"
```

## Companion Handoff Rules

- Preserve the original structural findings as structural findings.
- Upgrade a subclaim to `Formal support` only after local Lean verification succeeds.
- Keep the written answer and the formal artifact bundle aligned with `architecture_contract.md`.

## Hard Rules

- Never call a heuristic or unchecked draft proof "verified".
- If verification was unavailable in this environment, say that directly.
- Do not turn missing setup into negative theorem evidence.
- Keep the written answer and the bundle consistent with the contract.
- Treat `bootstrap_toolchain.py` and `bootstrap_proofs.py` as advanced recovery tools, not as the default path.
