# Typed tomography demo for a slot-based retrieval controller

## Architecture decomposition

The controller separates persistent slot keys, live slot queries, slot memory content,
and a residual bypass branch.

## Typed state inventory

`slot_key` is persistent address state, `q_slot` is live query state, `slot_memory` is
content state, and `z_residual` is a bypass write signal.

## Operator-state matrix

The risky operator is `key_update: K' <- EMA(K, phi(q_ctx))`. Without an explicit `phi`,
the update mixes a persistent key role with a live query role.

## Supervision and gradient reachability

The alignment loss reaches `slot_memory` directly, but only reaches `slot_key` indirectly
through the updater. The bypass branch is partially supervised.

## Shortcut and path dominance

A residual route can inject `z_residual` directly into the decoder path and weaken the
intended bottleneck.

## Invariants and singularities

Key/query separation requires an explicit cast. Direction normalization requires
`||x|| > 0` when used.

## Train/infer congruence

Training uses teacher-forced context in the updater, while inference reuses
self-generated state, so congruence is only partial.

## Empirical-only claims

Retrieval quality, convergence speed, and deployment efficiency still require
benchmarks and implementation evidence.

## Risks and redesign guidance

Introduce an explicit query-to-key map, audit the bypass branch, and state all
normalization preconditions in the architecture spec.
