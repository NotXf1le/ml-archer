---
name: formal-mathlib-verification
description: Ground ML architecture reasoning in Lean/mathlib evidence, but only when the user explicitly asks for formal verification or theorem-backed validation.
---

# Formal Mathlib Verification

Use this skill only for the explicit formal addon path.

## Required Reading

1. Read `../../references/formal_verification_contract.md` first.
2. Read `../../references/formal_mathlib_scope.md` for theorem-family boundaries and search strategy.
3. If the request came from `typed-architecture-tomography`, treat its `formalization_candidates` only as search seeds.

## Official Workflow

1. Inspect readiness:

```bash
python "../../scripts/formal/doctor.py"
```

2. Prepare the formal workspace explicitly:

```bash
python "../../scripts/formal/setup.py" --target search --allow-network --yes
```

Use `--target verify --allow-network --yes` only when actual Lean verification is required.

3. Search theorem candidates:

```bash
python "../../scripts/formal/search_mathlib.py" "<query>"
```

4. Verify the concrete Lean claim before calling it formal support:

```bash
python "../../scripts/formal/lean_check.py" --json
```

5. For nontrivial reviews, emit `report.md` and `evidence.json`, then validate them:

```bash
python "../../scripts/formal/validate_formal_bundle.py" --bundle-dir "<dir>"
```

## Hard Rules

- Never call a heuristic or unchecked draft proof "verified".
- If verification was unavailable or not run, say that directly.
- Keep the written answer and the bundle aligned with `formal_verification_contract.md`.
- Treat bootstrap commands as advanced repair tools, not the default user path.
