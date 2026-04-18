# Claim Extraction Rules

Use this file to turn architecture prose, equations, or code into atomic structural claims.

## Extraction Order

1. List explicit states.
2. List operators or update rules.
3. List losses and metrics.
4. Separate training and inference paths.
5. Split broad claims into local atomic claims.
6. Mark each atomic claim as one of:
   - structural finding
   - empirical-only claim

## Atomic Claim Families

### 1. Typing and Compatibility

Use for merges, EMA updates, residual adds, concatenations, projections, and attention-style scoring.

Examples:

- `K' <- EMA(K, phi(q_ctx))` requires either semantic-role compatibility or an explicit map `phi: query -> persistent_key`.
- `x + y` requires more than shape equality; space, geometry, and role must also match or be bridged.

### 2. Separation Claims

Use when the architecture distinguishes content, key, query, load, logit, or target spaces.

Examples:

- key/query separation
- address/content separation
- logit/probability separation

### 3. Precondition and Singularity Claims

Trigger on normalization, division, inverse, logarithm, softmax temperature, clipping, and coordinate charts.

Examples:

- `x / ||x||` requires `||x|| > 0`
- `log p` requires `p > 0`
- normalization on a manifold chart requires that the chosen chart is valid on the current domain

### 4. Invariance Claims

Use for idempotence, boundedness, conservation-like claims, monotonicity, contraction, or symmetry.

Examples:

- projection idempotence
- bounded radius preservation
- simplex preservation after softmax

### 5. Supervision Claims

Ask whether the intended states are actually reached by gradients.

Examples:

- a loss is only logged, not optimized;
- a state is detached before the loss;
- a target branch exists only during training.

### 6. Shortcut Claims

Compare intended path vs bypass path.

Examples:

- a residual route skips the bottleneck;
- the decoder can read an uncompressed branch directly;
- a predictor can exploit metadata instead of latent structure.

### 7. Train/Infer Congruence Claims

Ask whether the path optimized during training matches the path used at inference.

Examples:

- train uses teacher forcing, infer uses autoregressive recursion;
- train updates persistent memory, infer uses frozen memory;
- train path observes targets unavailable at inference.

## Structural Finding Rule

Keep an atomic claim in `structural finding` when it concerns typed states, compatibility,
preconditions, invariants, reachability, shortcut risk, or train/infer congruence.

The finding should stay local, explicit about boundaries, and tied to concrete equations,
code paths, or clearly marked assumptions.

## Empirical-Only Rule

Any claim about benchmark performance, training success in a concrete stack, hardware cost,
deployment speed, dataset fit, or model-family superiority belongs in `empirical_only_claims`.

## Missing Information Rule

If the architecture description is incomplete:

- reconstruct only what is necessary;
- mark the reconstruction as assumption-backed;
- lower confidence;
- keep missing-equation uncertainty explicit in the finding.
