---
name: typed-architecture-tomography
description: Analyze an ML architecture via typed states, operator-state matrices, supervision reachability, shortcut paths, invariants, singularities, and train/infer congruence.
---

# Typed Architecture Tomography

Use this skill for the default `ml-archer` path.

## Required Reading

1. Read `../../references/tomography_contract.md` first.
2. Read `../../references/matrix_legend.md`.
3. Read `../../references/claim_extraction_rules.md`.
4. Read `../../references/tomography_scope.md`.

## Workflow

1. Extract states, operators, losses, train/infer branches, and equations from the prompt, code, or paper.
2. Build the typed state inventory.
3. Build the operator-state matrix.
4. Build the supervision and gradient-reachability matrix.
5. Analyze shortcut paths and path dominance.
6. Analyze invariants and singularities.
7. Compare train and inference paths for congruence.
8. Emit structural findings, redesign guidance, and empirical-only claims.
9. For nontrivial reviews, emit `report.md` and `tomography.json`, then validate them:

```bash
python "../../scripts/validate_tomography_bundle.py" --bundle-dir "<dir>"
```

## Hard Rules

- Never infer benchmark wins from structural cleanliness.
- Never treat shape equality as semantic compatibility.
- Mark missing equations as `underdetermined` or `assumption-backed`.
