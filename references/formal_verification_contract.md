# Formal Verification Contract

Use this contract whenever the `formal-mathlib-verification` skill is active.

## Required Output Order

1. Proposed architecture
2. Formal evidence from mathlib
3. Engineering inference built on top of formal facts
4. Gaps requiring benchmarks or papers
5. Risks

## Claim Labels

- `Formal support`
- `Partial formal support`
- `No direct formal support found in mathlib`
- `Empirical gap`

If Lean verification was unavailable or not run, say that directly.

## Evidence Record

Each cited theorem or definition must record:

- `name`
- `import_path`
- `plain_language_meaning`
- `supported_subclaim`
- `unsupported_boundary`
- `claim_label`
- `verified_in_lean`
- `verification_method`
- `side_conditions`

Each side condition must include:

- `kind`
- `condition`
- `status`

## Artifact Bundle

For nontrivial requests, produce:

- `report.md`
- `evidence.json`
- `session_log.json` when setup or verification diagnostics materially affect the result

Validate with:

`python scripts/formal/validate_formal_bundle.py --bundle-dir <dir>`
