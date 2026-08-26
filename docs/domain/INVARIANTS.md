# Product and Finance Invariants

## Money

1. Monetary values are integer minor units.
2. Canonical amounts are non-negative.
3. Debit/credit direction is explicit.
4. Currency is required on every financial event and action.
5. Rounding or tolerance is policy-controlled and recorded as a proof check.

## Evidence and history

1. Every canonical event points to its original file and row.
2. Uploaded source values are immutable.
3. Normalization records adapter and mapping-profile versions.
4. Decisions record rule and policy versions.
5. Reviews and corrections append new events and versions.

## Verification

1. Match rules return proposals; the risk gate owns final proof level.
2. `PROVED` requires all configured hard checks and uniqueness.
3. Confidence ranks work but never overrides proof.
4. Ambiguity, search bounds and missing evidence cause abstention.
5. Fuzzy narration cannot auto-clear a case.

## Actions

1. The system never mutates or posts financial data without explicit approval.
2. Journal proposals must balance before approval.
3. Mutating/export actions use idempotency keys and produce receipts.
4. Corrected data creates a new version and is re-verified.

## AI

1. The model does not own arithmetic, proof, metrics or authoritative journal amounts.
2. Model output is schema-validated and evidence-validated.
3. Unknown evidence IDs or unsupported actions are rejected.
4. Model failure activates deterministic fallback.
5. Uploaded text is treated as untrusted data.

## Evaluation

1. Runtime code cannot access hidden ground truth.
2. Accuracy metrics are shown only when truth is available.
3. Operational metrics never claim unknown live precision or recall.
4. Incorrect benchmark case IDs remain inspectable.
5. Threshold failures return a failing process exit code.
