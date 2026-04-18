# Tomography Scope

Use this file to decide what the structural layer may and may not claim.

## What Typed Architecture Tomography Can Support

- Shape/space/role mismatches between states.
- Missing cast or transport maps between spaces.
- Illegal or suspicious merges between unlike semantic roles.
- Hidden preconditions such as `||x|| > 0`, support constraints, bounded domains, or chart assumptions.
- Gradient disconnects, detachments, logged-only losses, and dead branches.
- Shortcut/bypass paths that threaten the intended bottleneck.
- Train/infer path mismatch.

## What Typed Architecture Tomography Cannot Prove

- Better accuracy, retrieval quality, robustness, or calibration in the real world.
- Faster convergence in a concrete training stack.
- Lower latency, memory cost, or deployment cost.
- Model-family superiority such as Transformer vs. Mamba.
- Product-level gains from local invariants alone.

## Boundary Rules

- Structural cleanliness is not benchmark evidence.
- A local invariant is not proof of end-to-end model quality.
- An undefined or suspicious operation is a real risk, but not itself proof of failure in every implementation.
- If formulas, code, or train/infer branches are missing, say that the corresponding finding is underdetermined.
