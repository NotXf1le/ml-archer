# ml-archer

`ml-archer` is a tomography-first plugin for honest ML architecture review.

It focuses on one layer:

1. `typed-architecture-tomography`
   Structural analysis through typed states, matrices, shortcut paths, invariants, and
   train/infer congruence.

## Quick Start

Use the tomography skill, then validate the bundle:

```bash
python scripts/archer.py tomography validate --bundle-dir <dir>
```

You can also call the validator directly:

```bash
python scripts/validate_tomography_bundle.py --bundle-dir <dir>
```

You can also copy and validate the bundled demo:

```bash
python examples/run_demo_tomography.py --json
```

## Supported Surface

### Skills

* `skills/typed-architecture-tomography/SKILL.md`

### CLI entrypoints

* `scripts/archer.py`
* `scripts/validate_tomography_bundle.py`

### Reference documents

* `references/tomography_contract.md`
* `references/tomography_scope.md`
* `references/matrix_legend.md`
* `references/claim_extraction_rules.md`

## Non-Goals

This plugin does not:

* infer benchmark wins from clean matrices
* treat shape equality as semantic compatibility
* treat local invariants as proof of end-to-end model quality
