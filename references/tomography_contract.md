# Typed Architecture Tomography Contract

Use this output contract whenever the `typed-architecture-tomography` skill is active.

## Core Method

Assign each architecture state a typed-dimension tuple:

```text
τ(x) = (shape, space, geometry, semantic_role, time_role, persistence)
```

Interpret these dimensions strictly:

- `shape` checks tensor/layout compatibility.
- `space` checks the carrier set or codomain.
- `geometry` checks metric, simplex, normalization regime, manifold chart, or comparison structure.
- `semantic_role` checks what the state *means*.
- `time_role` checks whether the state is current, next-step, target, or predicted.
- `persistence` checks whether the state is ephemeral, persistent, buffered, parameterized, observed, or predicted.

Identical shape is never enough to justify mixing states.

## Required Output Order

1. Architecture decomposition
2. Typed state inventory
3. Operator-state matrix
4. Supervision and gradient reachability
5. Shortcut and path dominance
6. Invariants and singularities
7. Train/infer congruence
8. Formalization candidates
9. Empirical-only claims
10. Risks and redesign guidance

## Allowed Finding Labels

Use one of these exact labels:

- `Structural finding`
- `Type violation risk`
- `Invariant risk`
- `Gradient reachability finding`
- `Shortcut risk`
- `Train/infer mismatch risk`
- `Formalization candidate`
- `Empirical-only claim`

## Forbidden Formal Labels and Keys

Do **not** use any of the following inside the tomography bundle:

- `Formal support`
- `Partial formal support`
- `No direct formal support found in mathlib`
- `verified_in_lean`
- `verification_method`
- `claim_label`

Those belong to the formal verification contract, not the structural one.

## Bundle Format

For nontrivial requests, produce:

- `report.md`
- `tomography.json`
- `session_log.json` when ambiguity, missing equations, or source limitations materially affect the result

Validate the bundle explicitly with:

`python scripts/validate_tomography_bundle.py --bundle-dir <dir>`

## `tomography.json` Required Top-Level Fields

- `architecture_name`
- `architecture_summary`
- `assumptions`
- `typed_states`
- `operators`
- `operator_state_matrix`
- `supervision_matrix`
- `shortcut_paths`
- `invariants`
- `train_infer_congruence`
- `findings`
- `formalization_candidates`
- `empirical_only_claims`

## Required `typed_states` Fields

Each typed state record must include:

- `state_id`
- `symbol`
- `semantic_role`
- `shape`
- `space`
- `geometry`
- `time_role`
- `persistence`
- `producer_ops`
- `consumer_ops`

## Required `operators` Fields

Each operator record must include:

- `operator_id`
- `equation_or_rule`
- `purpose`
- `reads`
- `writes`
- `mode`

`mode` must be one of `train`, `infer`, or `both`.

## Required `operator_state_matrix` Fields

The operator-state matrix object must include:

- `states`
- `rows`

Each row must include:

- `operator_id`
- `cells`

`cells` must map state ids to matrix cell codes from `matrix_legend.md`.

## Required `supervision_matrix` Fields

The supervision matrix object must include:

- `rows`

Each row must include:

- `loss_id`
- `cells`
- `notes`

## Required `shortcut_paths` Fields

Each shortcut-path record must include:

- `shortcut_id`
- `claim_or_output`
- `intended_path`
- `shortcut_path`
- `status`
- `risk_summary`

## Required `invariants` Fields

Each invariant record must include:

- `invariant_id`
- `statement`
- `statuses`
- `boundary`

## Required `train_infer_congruence` Fields

The congruence object must include:

- `status`
- `train_path`
- `infer_path`
- `mismatch_points`
- `notes`

## Required `findings` Fields

Each finding record must include:

- `finding_id`
- `finding_label`
- `severity`
- `summary`
- `basis`
- `confidence`
- `evidence_refs`
- `boundary`
- `recommended_action`

`basis` should be one of:

- `explicit_equation`
- `textual_description`
- `naming_inference`
- `assumption_backed`
- `missing_information`

`confidence` should be one of `high`, `medium`, or `low`.

## Required `formalization_candidates` Fields

Each candidate must include:

- `candidate_id`
- `natural_language_claim`
- `reason_it_is_formalizable`
- `target_backend`
- `theorem_family`
- `search_terms`
- `suggested_import_nouns`
- `side_conditions`

## Required `empirical_only_claims` Fields

Each empirical-only record must include:

- `claim_id`
- `claim`
- `why_empirical`
- `required_evidence`

## Unknowns Must Be Explicit

If formulas, code paths, or losses are missing, encode that explicitly in:

- `assumptions`
- `findings[*].basis`
- `findings[*].confidence`
- `train_infer_congruence.status` when appropriate

## Do Not Collapse Categories

- Do not present structural cleanliness as benchmark evidence.
- Do not present a local invariant as proof of end-to-end model quality.
- Do not present a formalization candidate as a verified theorem.
- Do not treat absence of a detected shortcut as proof that none exists.
