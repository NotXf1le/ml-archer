# Matrix Legend

Use these canonical tokens unless the user explicitly needs different notation.

## Typed-Dimension Tuple

```text
tau(x) = (shape, space, geometry, semantic_role, time_role, persistence)
```

## Canonical Semantic Roles

Use short machine-friendly strings when possible:

- `content`
- `persistent_key`
- `query`
- `value`
- `load`
- `address`
- `logit`
- `probability`
- `latent`
- `prediction`
- `target`
- `parameter`
- `control`
- `memory`
- `residual`
- `mask`

This list is extensible. Do not force a bad fit.

## Canonical Geometry Hints

Examples:

- `euclidean`
- `inner_product`
- `probability_simplex`
- `logit_space`
- `normalized_sphere`
- `bounded_ball`
- `manifold_chart`
- `index_space`
- `measure_space`
- `phase_angle`

## Operator-State Matrix Cell Codes

Use one code or a comma-separated set of codes per cell.

- `R` - read
- `W` - overwrite or write
- `U` - update using the previous value and a new signal
- `P` - produce or predict
- `T` - target or supervise
- `C` - cast, map, or transport between spaces
- `M` - merge, add, concatenate, or compose
- `D` - detach or stop-gradient
- `.` - no direct relation
- `!` - illegal or suspicious relation unless extra structure is supplied

## Supervision Matrix Statuses

- `direct`
- `indirect`
- `detached`
- `logged_only`
- `none`
- `unknown`

## Invariant Statuses

- `preserved`
- `violated`
- `requires_precondition`
- `unknown`

## Train/Infer Congruence Statuses

- `aligned`
- `partial_mismatch`
- `mismatch`
- `underdetermined`

## Finding Labels

Use one of these exact values in `tomography.json`:

- `Structural finding`
- `Type violation risk`
- `Invariant risk`
- `Gradient reachability finding`
- `Shortcut risk`
- `Train/infer mismatch risk`
- `Empirical-only claim`

## Severity Scale

- `low`
- `medium`
- `high`
- `critical`
