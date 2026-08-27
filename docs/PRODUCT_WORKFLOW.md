# VeriClose Product Scope and End-to-End Workflow

## The project in one sentence

VeriClose accepts a payment-gateway export, a bank statement and an ERP general-ledger
export for the same period, preserves every source row, and produces evidence-backed
reconciliation cases showing what is proved, what needs review and what is unresolved.

It is a finance-control workflow, not merely a three-file join and not a chatbot.

## Inputs in the current MVP

The user supplies three synthetic files. Each input may be CSV or XLSX.

| Upload slot | Typical contents | What it proves |
|---|---|---|
| Gateway report | payments, refunds, fees, GST/tax, adjustments, settlement IDs, UTRs and timestamps | how customer transactions became a net settlement |
| Bank statement | credits/debits, dates, UTR/reference and narration | whether the settlement actually reached the bank |
| ERP general ledger | bank, gateway-clearing, fee and tax journal lines | whether the receipt and deductions were recorded correctly in the books |

The frozen MVP supports one merchant/legal entity, INR only, and one known layout per
source with controlled mapping aliases. Development and judging use synthetic data only.

In a realistic demo, the three files represent the same date range or settlement batch.
They do not need to have the same number of rows: many gateway transactions may form one
settlement, while one ERP journal may contain several accounting lines.

## What the system creates

VeriClose never overwrites or collapses the three sources into a new authoritative
financial transaction. It retains:

1. the original uploaded file and a file fingerprint;
2. each original row and its exact file, sheet and row lineage;
3. a normalized canonical event used for comparison; and
4. a separate reconciliation case containing linked evidence, checks, status, reasons and
   any proposed next action.

A reconciliation case may therefore link many gateway rows to one bank row and several ERP
lines. This is safer and more useful than creating one opaque merged row.

## Expected user workflow

### 1. Create a reconciliation run

The user chooses a period or batch and uploads the gateway, bank and ERP files into three
clearly labelled slots.

### 2. Detect, map and validate

The system identifies each layout, maps source columns to canonical fields and reports
actionable file/sheet/row/field errors. It checks file integrity, required fields, currency,
dates, amount formats, duplicate uploads, control totals and balanced ERP journals.

The run must not claim success when an input is incomplete or invalid.

### 3. Normalize without losing evidence

Amounts become integer paise with an explicit debit or credit direction. References and
dates are standardized for matching while original values remain available for inspection.

### 4. Reconcile the gateway settlement internally

For each settlement, deterministic rules verify the component equation, conceptually:

`payments - refunds - fees - taxes +/- adjustments = net settlement`

The engine also verifies settlement membership and detects missing, duplicated or
contradictory gateway components.

### 5. Prove the bank receipt

The engine attempts an exact UTR/reference match, then checks amount, direction, date policy
and uniqueness. Bounded one-to-many or many-to-one matching is allowed when the accounting
relationship justifies it. Similarity alone is not enough to auto-clear.

### 6. Prove the ERP accounting

The engine checks that the bank receipt, gateway-clearing movement, fee expense and input-tax
lines have the expected amounts, directions and account roles, and that the journal balances.

### 7. Apply the risk gate

Every case receives one of these evidence outcomes:

| Outcome | Meaning | Result |
|---|---|---|
| `PROVED` | all required hard checks pass and the match is unique | safe to auto-clear |
| `SUPPORTED` | evidence suggests a candidate but is insufficient for proof | human review |
| `AMBIGUOUS` | multiple plausible candidates exist | abstain and request review |
| `CONTRADICTED` | sources disagree on identity, amount, direction or accounting | high-priority exception |
| `INVALID_INPUT` | the source data cannot be safely evaluated | correct the input first |

### 8. Review exceptions with evidence

The workbench shows the relevant source rows side by side, the checks that passed and failed,
the amount at risk, a reason code and the recommended next step. An optional AI investigator
may explain the deterministic facts or draft a clarification, but cannot decide proof,
change source data or post a journal.

### 9. Correct and close the loop

For a resolvable accounting issue, the system proposes a balanced journal for human review.
After approval it exports a posting-ready CSV. The user then imports corrected mock ERP data,
and VeriClose re-runs only affected cases. Prior evidence and decisions remain in history.

### 10. Export the close pack

The final output includes the run summary, proved cases, unresolved exception list, evidence
links, review decisions, audit history and any approved journal proposal.

## Problems the MVP should demonstrate

The synthetic benchmark should include both genuine errors and legitimate differences:

- a clean exact three-source reconciliation;
- many gateway transactions grouped into one net settlement;
- missing or duplicate bank receipts;
- missing, duplicate, reversed or wrong-account ERP postings;
- incorrect fee or GST/tax deductions/postings;
- refunds and adjustments affecting a later settlement;
- valid weekend or working-day timing differences;
- partial settlements and bounded group matches;
- missing/corrupted references and equal-amount ambiguous candidates;
- malformed files, invalid amounts, duplicate uploads and unbalanced journals.

The system's value is partly in detecting errors and partly in avoiding false alarms for
valid timing, refund and grouping behavior.

## What the main screens should communicate

1. **Import and mapping:** three upload slots, detected layout, validation issues and control
   totals.
2. **Run cockpit:** counts and values proved, under review, unresolved and invalid; no invented
   live “accuracy” number.
3. **Case workbench:** side-by-side source evidence, calculation, proof checks, reason and
   amount at risk.
4. **Exception queue:** filters by category, severity, owner and required action.
5. **Action and re-run:** balanced journal preview, approval/rejection, export, corrected
   import and before/after status.
6. **Benchmark view:** precision, exception recall, false-clear rate and throughput measured
   only against hidden synthetic truth.

Operational run status and benchmark accuracy must remain visibly separate. A real uploaded
batch has no hidden labels, so its true precision or recall is not known at runtime.

## Why this is a strong SWE/AI internship project

The strongest story is not “I used an LLM to match spreadsheets.” It is:

> I designed and built a safety-sensitive, testable reconciliation controller that ingests
> inconsistent financial data, preserves audit lineage, applies deterministic accounting
> invariants, abstains under ambiguity, measures itself on hidden synthetic truth, and uses
> AI only for bounded explanations and proposals.

That demonstrates:

- backend and frontend product engineering;
- data modeling, parsing and normalization;
- algorithms for exact, grouped and bounded matching;
- accounting-domain reasoning and invariant design;
- evaluation discipline, adversarial testing and honest metrics;
- explainable AI, schema validation and safe human-in-the-loop design;
- deployment, reproducibility and clear technical communication.

For interviews, be ready to explain one false-positive risk you prevented, one accounting
invariant, one ambiguous case where the engine abstains, and one measured benchmark tradeoff.
Those decisions show more analytical maturity than maximizing a cosmetic match percentage.

## Definition of a convincing demo

A reviewer can load a synthetic batch of at least 50 records, run all three inputs, inspect a
proved case, inspect an honest ambiguous case, diagnose a fee/tax or missing-posting exception,
approve a balanced correction, import the corrected mock ERP result, re-run the affected case
and download the close pack. The benchmark separately reports reproducible precision,
exception recall, false clears and throughput.

