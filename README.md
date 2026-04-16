# Mathlib ML Architect Plugin

A plugin for **honest ML architecture review** with two companion workflows:

1. **Typed architecture tomography**  
   Structural analysis through typed states, matrices, invariants, shortcut-path inspection, and train/infer congruence.

2. **Mathlib-backed verification**  
   Local formal checking in Lean/mathlib for the subset of claims that can actually be verified.

## Core Contract

This plugin enforces a strict separation between kinds of evidence:

- **Structural findings are not Lean verification**
- **Engineering inference remains separate from formal support**
- **Benchmark, deployment, and training claims remain empirical unless explicitly proven otherwise**

## Official Workflows

### 1. Structural workflow

Use the `typed-architecture-tomography` skill to decompose an architecture into:

- typed states
- operators
- matrices
- risks
- formalization candidates

For non-trivial requests, generate a bundle and validate it:

```bash
python scripts/validate_tomography_bundle.py --bundle-dir <dir>
````

### 2. Formal workflow

#### Step 1 — Check environment readiness

```bash
python scripts/doctor.py
```

#### Step 2 — Prepare the shared workspace

```bash
python scripts/setup_plugin.py --target search
python scripts/setup_plugin.py --target verify --yes
```

#### Step 3 — Search candidate facts and verify the exact Lean claim

```bash
python scripts/search_mathlib.py "<query>"
python scripts/lean_check.py --json
```

#### Step 4 — Validate the final formal review bundle

```bash
python scripts/validate_artifact_bundle.py --bundle-dir <dir>
```

## Supported Product Surface

### Scripts

* `scripts/doctor.py`
* `scripts/setup_plugin.py`
* `scripts/search_mathlib.py`
* `scripts/lean_check.py`
* `scripts/validate_artifact_bundle.py`
* `scripts/validate_tomography_bundle.py`

### Reference documents

* `references/architecture_contract.md`
* `references/mathlib_scope.md`
* `references/tomography_contract.md`
* `references/tomography_scope.md`
* `references/matrix_legend.md`
* `references/claim_extraction_rules.md`

### Skills

* `skills/mathlib-ml-arch/SKILL.md`
* `skills/typed-architecture-tomography/SKILL.md`

## Advanced / Manual Recovery

Low-level repair helpers remain available for advanced recovery workflows, but they are **not** the primary entry path:

* `bootstrap_toolchain.py`
* `bootstrap_proofs.py`

## Non-Goals

This plugin does **not**:

* present a fixture replay as a live architecture audit
* label a structural finding as formal support when Lean verification was not obtained
* infer benchmark wins, optimizer stability, or deployment gains from clean matrices
* treat shape equality as semantic compatibility

## Examples

These example scripts demonstrate the bundled demo flows only:

* `examples/run_demo_review.py`
  Copies the bundled formal demo bundle from `examples/demo-review/` into an output directory and validates it.

* `examples/run_demo_tomography.py`
  Copies the bundled structural demo bundle from `examples/demo-tomography/` into an output directory and validates it.

> These are examples only, not the main audit flow.
