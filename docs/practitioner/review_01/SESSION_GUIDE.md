# Practitioner session guide

## Roles

- Practitioner: independently inspects and labels cases.
- Observer: records behavior without coaching or defending the product.

Use a neutral practitioner code such as `practitioner-01`. Do not record company or client names.

## Phase 1 — Observe five cases

Ask: “Please investigate this as you normally would. Think aloud, but I will not explain the
system yet.” Record evidence-open order, time, confusing terms and missing fields in
`OBSERVATION_NOTES.md`.

Do not ask leading questions during these five cases.

## Phase 2 — Blind-label all 25 cases

Complete `labels.csv` using these vocabularies:

- `expected_status`: `CLEAR`, `REVIEW`, `UNRESOLVED`
- `expected_proof_level`: `PROVED`, `SUPPORTED`, `AMBIGUOUS`, `CONTRADICTED`, `INVALID_INPUT`
- `reason_category`: domain exception category or `NONE`
- `severity`: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`, or `NONE`
- `requires_company_input`: `true` or `false`
- `required_evidence_ids`: pipe-separated `PR-...-E..` identifiers
- `journal_behavior`: the exact entry/wait/correction behavior, or `NONE`

Every label needs an evidence-based rationale. Do not open the private answer key yet.

## Phase 3 — Reveal and resolve

Open the private answer key and `LEAST_CERTAIN.md`. For each full-label disagreement, complete
`resolutions.csv` with `ACCEPT_SYSTEM`, `ACCEPT_PRACTITIONER`, or `DEFER`, plus a concrete reason.
An accepted practitioner correction requires a task ID before it can enter the golden suite.

## Phase 4 — Prioritize workflow feedback

Record one row per observation/request in `feature_priorities.csv`:

- priority: `MUST_HAVE`, `SHOULD_HAVE`, `LATER`, `REJECT`
- decision: `ACCEPT`, `DEFER`, `REJECT`
- trust impact, review-time impact, build cost and scope risk: integers 1–5

A must-have requires trust impact of at least 4. Accepted work requires a task ID. Novelty alone is
not a reason to expand the frozen MVP.

## Phase 5 — Publish

Run `make review-analyze`. The command computes agreement/disagreement counts, publishes the
proportional domain-review report and promotes resolved, sanitized cases into the evaluation-only
golden suite. Deferred disagreements and the reserved 90% holdout are excluded.

