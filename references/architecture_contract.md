# Architecture Contract

Use this output contract whenever the skill is active.

## Required Output Order

1. Proposed architecture
2. Formal evidence from mathlib
3. Engineering inference built on top of formal facts
4. Gaps requiring benchmarks or papers
5. Risks

## Claim Labels

- `Formal support`: the exact subclaim was verified locally in Lean.
- `Partial formal support`: a local property was verified, but not the full design claim.
- `No direct formal support found in mathlib`: no verified theorem or definition supports the claim.
- `Empirical gap`: the claim depends on benchmarks, hardware, data, training dynamics, or deployment constraints.

If Lean verification was unavailable or not run, say that explicitly. Do not turn missing verification into negative evidence.

## Evidence Record

For each cited theorem or definition, record:

- `name`
- `import_path`
- `plain_language_meaning`
- `supported_subclaim`
- `unsupported_boundary`
- `claim_label`
- `verified_in_lean`
- `verification_method`
- `side_conditions`

Each `side_conditions` entry must include:

- `kind`
- `condition`
- `status`

## Artifact Bundle

For nontrivial requests, produce:

- `report.md`
- `evidence.json`
- `session_log.json` when setup or verification diagnostics materially affect the result

Validate the bundle explicitly with:

`python scripts/validate_artifact_bundle.py --bundle-dir <dir>`

## Do Not Collapse Categories

- Do not present benchmark expectations as formal results.
- Do not present a local invariant as proof of end-to-end model quality.
- Do not treat an unchecked `ProofScratch.lean` edit as verified evidence.
- Do not treat absence of a counterexample as proof.
