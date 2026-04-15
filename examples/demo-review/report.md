# Typed residual audit for retrieval controller

## Proposed architecture

Use typed projections for retrieval controller branches and keep address-space and content-space metrics separated.

## Formal evidence from mathlib

Orthogonal projection idempotence supports the local invariant for the projection branch.

## Engineering inference built on top of formal facts

Typed-interface separation reduces the chance of mixing score-space and state-space semantics in residual paths.

## Gaps requiring benchmarks or papers

Gradient damping and end-to-end retrieval quality still need empirical confirmation.

## Risks

Residual merges can remain shape-compatible while staying semantically unsafe.

## RECHECK

Do not treat local invariants as proof of optimizer or product-level gains.