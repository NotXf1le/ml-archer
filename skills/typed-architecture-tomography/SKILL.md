---
name: typed-architecture-tomography
description: Analyze an ML architecture via typed states, operator-state matrices, supervision reachability, shortcut paths, invariants, singularities, and train/infer congruence. Use when the user wants formula-driven or matrix-based structural analysis, semantic type checking, dimension-like reasoning, or formalization candidates for later Lean verification.
---

# Typed Architecture Tomography

Use this skill when the user wants a structural mathematical read of an ML architecture
before or without Lean verification.

## Required Reading

1. Read `../../references/tomography_contract.md` first.
2. Read `../../references/matrix_legend.md` for symbols, role names, and matrix cell meanings.
3. Read `../../references/claim_extraction_rules.md` to derive atomic structural claims from prose, formulas, or code.
4. Read `../../references/tomography_scope.md` to keep structural findings separate from empirical and formal claims.
5. Read `../../references/mathlib_scope.md` only when emitting formalization candidates for later handoff.

## Core Method

Assign each architecture state `x` a typed-dimension tuple:

```text
τ(x) = (shape, space, geometry, semantic_role, time_role, persistence)
```

Interpretation:

- `shape`: tensor or index layout
- `space`: carrier space or codomain
- `geometry`: metric, simplex, manifold chart, normalization regime, or comparison structure
- `semantic_role`: content, key, query, load, logit, probability, latent, target, parameter, control, etc.
- `time_role`: current, next-step, predicted, target, static
- `persistence`: ephemeral, persistent, parameter, buffer, observed, predicted

Shape compatibility alone never justifies an operation. A merge, residual, EMA update,
attention score, normalization, or projection is only structurally safe when semantic role
and geometry also match, or when an explicit cast/transport map is given.

## Workflow

1. Extract states, operators, losses, train/infer branches, and explicit equations from the prompt, paper excerpt, or code.
2. Build a typed state inventory with one record per state.
3. Build the operator-state matrix.
4. Build the supervision and gradient-reachability matrix.
5. Build shortcut/path-dominance analysis.
6. Build invariants and singularities analysis.
7. Compare train and inference paths for congruence.
8. Emit structural findings, redesign guidance, formalization candidates, and empirical-only claims.
9. For nontrivial reviews, emit `report.md` and `tomography.json`, then validate them:

```bash
python "../../scripts/validate_tomography_bundle.py" --bundle-dir "<dir>"
```

## Handoff to the Formal Skill

When a subclaim looks formalizable:

- restate it as a narrow, local, theorem-like claim;
- list side conditions explicitly;
- propose search terms and theorem families;
- hand it to `mathlib-ml-arch` as a candidate, never as evidence.

## Hard Rules

- Never use `Formal support`, `Partial formal support`, or `verified_in_lean` in this skill’s own findings.
- Never infer model quality, benchmark gains, or deployment wins from structural cleanliness.
- Never treat identical shape as semantic compatibility.
- When equations are missing, mark the affected finding as `underdetermined` or `assumption-backed`.
- Keep matrices, findings, and redesign guidance consistent with the tomography contract.
- Hand formalizable subclaims to `mathlib-ml-arch` only as candidates, never as evidence.
