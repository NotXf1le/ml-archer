# ml-archer

`ml-archer` is a tomography-first plugin for honest ML architecture review.

It has two clearly separated layers:

1. `typed-architecture-tomography`
   Structural analysis through typed states, matrices, shortcut paths, invariants, and train/infer congruence.
2. `formal-mathlib-verification`
   Explicit Lean/mathlib verification for narrow subclaims that can actually be checked.

Structural findings are never treated as formal proof.

## Quick Start

### Default path: tomography

Use the tomography skill, then validate the bundle:

```bash
python scripts/archer.py tomography validate --bundle-dir <dir>
```

You can also call the validator directly:

```bash
python scripts/validate_tomography_bundle.py --bundle-dir <dir>
```

### Opt-in formal addon

Inspect readiness:

```bash
python scripts/archer.py formal doctor
```

Prepare the formal workspace explicitly:

```bash
python scripts/archer.py formal setup --target search --allow-network --yes
python scripts/archer.py formal setup --target verify --allow-network --yes
```

Search theorem candidates and verify the exact Lean claim:

```bash
python scripts/archer.py formal search "LinearMap"
python scripts/archer.py formal check --json
```

Validate a formal evidence bundle:

```bash
python scripts/archer.py formal validate-bundle --bundle-dir <dir>
```

## Formal Bundles

The formal addon can be packaged as a prewarmed bundle for offline reuse:

```bash
python scripts/formal/build_bundle.py --output dist/
python scripts/formal/install_bundle.py ./dist/<bundle>.tar
```

If `zstd` is available, bundle output is written as `.tar.zst`.

## Supported Surface

### Skills

* `skills/typed-architecture-tomography/SKILL.md`
* `skills/formal-mathlib-verification/SKILL.md`

### CLI entrypoints

* `scripts/archer.py`
* `scripts/validate_tomography_bundle.py`
* `scripts/formal/doctor.py`
* `scripts/formal/setup.py`
* `scripts/formal/search_mathlib.py`
* `scripts/formal/lean_check.py`
* `scripts/formal/validate_formal_bundle.py`
* `scripts/formal/build_bundle.py`
* `scripts/formal/install_bundle.py`

### Reference documents

* `references/tomography_contract.md`
* `references/tomography_scope.md`
* `references/matrix_legend.md`
* `references/claim_extraction_rules.md`
* `references/formal_verification_contract.md`
* `references/formal_mathlib_scope.md`

## Non-Goals

This plugin does not:

* label structural findings as formal support
* infer benchmark wins from clean matrices
* treat unchecked Lean drafts as verified evidence
* vendor mathlib into the repository
