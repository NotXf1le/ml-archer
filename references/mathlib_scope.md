# Mathlib Scope

Use this file to decide whether a claim belongs in the formal layer or outside it.

## What Mathlib Can Support

- Algebraic identities and tensor-free linear algebra reasoning.
- Matrix, vector space, linear map, and bilinear form properties.
- Normed space and inner product space facts.
- Measure-theoretic and probability-theoretic definitions and lemmas.
- Local analysis facts such as continuity, Lipschitz conditions, convexity, and boundedness when explicit theorems exist.

## What Mathlib Does Not Prove For You

- Model-family choice such as Transformer vs. Mamba.
- Dataset fit, generalization quality, and benchmark outcomes.
- Hardware latency, memory tradeoffs, or deployment cost.
- Training stability in a concrete stack unless the exact setup is formalized and verified.

## Search Playbook

- Start with domain nouns and structure names: `LinearMap`, `Matrix`, `InnerProductSpace`, `Norm`, `Measure`, `ProbabilityTheory`, `ConditionalExpectation`, `Independent`, `Lipschitz`, `convex`.
- Narrow from definitions to theorem names before citing anything.
- Prefer exact import paths and theorem names over broad paraphrases.
- Use `python "../../scripts/search_mathlib.py" "<query>"` for candidate search.
- Treat the result as formal support only after `python "../../scripts/lean_check.py" --json` succeeds.

## Local Workflow Boundary

- Start with `python "../../scripts/doctor.py"`.
- If the shared workspace is incomplete, use `python "../../scripts/setup_plugin.py" --target search`.
- Use `--target verify --yes` only when you need full Lean verification artifacts.
- Low-level bootstrap commands are advanced recovery tools, not the supported first step.
- If setup cannot complete in the current environment, say that formal verification is unavailable here.
