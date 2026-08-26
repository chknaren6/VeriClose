# Domain Glossary

## Source record

One immutable row from an uploaded gateway, bank or ERP file, identified by file, sheet and row number.

## Canonical event

A typed representation of a source record with normalized amount, direction, currency, dates and references while retaining raw lineage.

## Settlement

A gateway-defined transfer of net transaction value to a merchant bank account after relevant components such as refunds, fees, tax and adjustments.

## Match group

The set of gateway, bank and ERP events proposed to describe the same movement of money.

## Proof check

A deterministic assertion with expected value, observed value, tolerance, result and supporting evidence.

## Evidence link

A link from a proof check, decision, exception or action to the exact source rows that support it.

## Match proposal

A rule’s side-effect-free candidate grouping and proof checks. It is not yet a final decision.

## Proof level

- `PROVED`: required identifiers, accounting checks and uniqueness pass.
- `SUPPORTED`: strong evidence exists but at least one hard proof is absent.
- `AMBIGUOUS`: multiple viable candidates or insufficient evidence remain.
- `CONTRADICTED`: sources disagree on a required fact or accounting behavior.
- `INVALID_INPUT`: validation prevents reliable reconciliation.

## Verified

A system status backed by a `PROVED` decision. It is stronger than “likely matched.”

## Auto-clear

A policy-permitted transition for a unique `PROVED` case. Confidence alone cannot auto-clear.

## Exception

A case that is unsupported, ambiguous, contradicted or blocked by invalid input and requires review, external information or correction.

## Review

An append-only human decision to approve, reject, edit, defer or request information. Review does not mutate source evidence.

## Proposed action

A typed, evidence-linked next step such as journal export, clarification request, mapping correction, wait or accepted difference.

## Resolved

A prior exception whose required action/evidence has been applied in a new version and whose result has been re-evaluated. Resolved is not synonymous with matched.

## Event-level evaluation

Measurement of whether each source event received the correct group and disposition.

## Case-level evaluation

Measurement of whether the complete multi-source money movement received the correct proof level, exception class and action.

## False-clear

An incorrect or anomalous case marked auto-cleared. This is the highest-severity evaluation failure.
