# MVP Boundary

## Product promise

For every source record, VeriClose will either prove where the money went, route the case for review with supporting evidence, or state exactly why it cannot decide.

## Supported in the MVP

- One merchant and one legal entity
- INR with integer paise amounts
- CSV and XLSX upload paths
- One Razorpay-style settlement export
- One generic bank statement
- One generic ERP general-ledger export
- Exact, invariant, grouped and bounded candidate matching
- `PROVED`, `SUPPORTED`, `AMBIGUOUS`, `CONTRADICTED` and `INVALID_INPUT` proof outcomes
- Evidence-first review
- Balanced journal proposal/export
- Corrected mock ERP import and re-run
- Generated, golden and adversarial synthetic evaluation
- Hosted and local judge execution

## Explicit non-goals

- Production ERP write-back
- Multi-entity consolidation
- Foreign-currency reconciliation or revaluation
- Tax filing or statutory advice
- General ERP migration in the MVP
- Unbounded autonomous actions
- Chat-first product navigation
- Production handling of real confidential finance data

## Classification rule

A proposed feature is:

- **MVP** when it is required to close or verify the three-source settlement loop.
- **Adapter expansion** when it changes an input/output integration without changing proof semantics.
- **Workflow expansion** when it reuses canonical events, proof, evidence, review and evaluation for another finance loop.
- **Rejected for now** when it weakens evidence, introduces unsafe write authority or delays the complete MVP.
