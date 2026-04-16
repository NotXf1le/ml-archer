# Formal Mathlib Scope

Use this file to decide whether a claim belongs in the formal addon or outside it.

## What Mathlib Can Support

- Algebraic identities and tensor-free linear algebra reasoning
- Matrix, vector space, linear map, and bilinear form properties
- Normed space and inner product space facts
- Measure-theoretic and probability-theoretic definitions and lemmas
- Local analysis facts such as continuity, Lipschitz conditions, convexity, and boundedness when explicit theorems exist

## What It Does Not Prove For You

- Model-family choice
- Dataset fit and benchmark outcomes
- Hardware latency or deployment cost
- Training stability of a concrete stack unless the exact setup is formalized

## Search Playbook

- Start with domain nouns like `LinearMap`, `Matrix`, `Norm`, `ProbabilityTheory`, `convex`.
- Narrow from definitions to theorems before citing anything.
- Prefer exact import paths and theorem names over broad paraphrases.
- Use `python "../../scripts/formal/search_mathlib.py" "<query>"` for candidate search.
- Treat results as formal support only after `python "../../scripts/formal/lean_check.py" --json` succeeds.

## Local Workflow Boundary

- Start with `python "../../scripts/formal/doctor.py"`.
- If the formal workspace is incomplete, use `python "../../scripts/formal/setup.py" --target search --allow-network --yes`.
- Use `--target verify --allow-network --yes` only when full Lean verification artifacts are required.
