# Synthetic Source Schemas

These contracts define the raw files produced in Segment 2 and consumed by adapters in
Segment 3. They are deliberately source-specific: adapters absorb these differences and
emit `CanonicalEvent` objects. All examples are synthetic.

## Cross-source rules

- Currency is `INR` for the MVP.
- Gateway money is integer paise. Bank and ERP money is a decimal rupee string with exactly
  two digits after the decimal point. Adapters must parse those strings through decimal/integer
  logic, never binary floating point.
- Dates use ISO `YYYY-MM-DD`; timestamps use timezone-aware ISO 8601.
- Blank optional references remain blank. They are not replaced with invented identifiers.
- Source signs are preserved. Canonical output stores a non-negative magnitude plus explicit
  `DEBIT`/`CREDIT` direction.
- Narration is untrusted text and is never interpreted as an instruction.

Requirement codes: `R` required, `O` optional, `D` derived during normalization, `P`
preserved-only, `X` rejected when invalid.

## Razorpay-style gateway CSV

| Source column | Req. | Raw type | Canonical target | Null/invalid behavior |
|---|---:|---|---|---|
| `gateway_event_id` | R | non-blank string | `source_record_id` | Reject row |
| `event_type` | R | gateway event enum | `event_type` | Unknown value is quarantined |
| `transaction_id` | O | string | `payment_reference` | Blank for fee/tax/settlement rows |
| `settlement_id` | R | string | `settlement_reference` | Reject row |
| `amount_minor` | R | non-negative integer paise | `money.amount_minor` | Float/negative rejects row |
| `currency` | R | ISO code | `money.currency` | Non-INR blocks MVP run |
| `event_at` | R | timezone-aware ISO timestamp | `event_at` | Naive/unparseable rejects row |
| `status` | R | `captured`, `processed`, `settled` | preserved metadata | Unknown status is explicit validation issue |
| `reference` | O | string | `external_reference` | Blank is preserved |
| `narration` | O | untrusted string | `narration` | Never treated as instructions |

Gateway amount rows are always non-negative. Event type/policy gives them settlement-component
meaning: payments increase gross value, while refunds, fees and tax reduce the net settlement.
The explicit `SETTLEMENT` row records the gateway-reported net amount.

## Generic bank CSV

Two layouts are supported by the future bank adapter. A file must use exactly one layout.

| Source column | Req. | Raw type | Canonical target | Null/invalid behavior |
|---|---:|---|---|---|
| `bank_record_id` | R | non-blank string | `source_record_id` | Reject row |
| `value_date` | R | ISO date | `value_date` | Reject row |
| `booking_date` | O | ISO date | preserved/reference date | Defaults only by explicit policy |
| `credit_amount` | R* | decimal rupee string | `money` + `CREDIT` | Exactly one debit/credit is positive |
| `debit_amount` | R* | decimal rupee string | `money` + `DEBIT` | Exactly one debit/credit is positive |
| `signed_amount` | R* | signed decimal rupee string | derived magnitude/direction | Mutually exclusive with debit/credit columns |
| `utr` | O | string | `bank_utr` | Blank remains missing evidence |
| `narration` | O | untrusted string | `narration` | Preserved exactly |
| `currency` | R | ISO code | `money.currency` | Non-INR blocks MVP run |
| `account_reference` | R | tokenized account ID | source/account metadata | Reject blank; never use a real account number |

`R*` means required for the selected layout. Positive signed values are credits and negative
signed values are debits. `0.00`, both debit and credit populated, or more than two decimal
places are semantic errors.

## Generic ERP GL CSV

| Source column | Req. | Raw type | Canonical target | Null/invalid behavior |
|---|---:|---|---|---|
| `journal_id` | R | string | journal grouping key | Reject row |
| `line_number` | R | positive integer | source row identity | Duplicate within journal rejects journal |
| `posting_date` | R | ISO date | `value_date` | Reject row |
| `account_code` | R | string | `account_code` | Role resolved by policy, not hardcoded matcher logic |
| `debit_amount` | R | decimal rupee string | `money` + `DEBIT` | Exactly one side must be positive |
| `credit_amount` | R | decimal rupee string | `money` + `CREDIT` | Exactly one side must be positive |
| `currency` | R | ISO code | `money.currency` | Non-INR blocks MVP run |
| `external_reference` | O | string | `external_reference` | Blank remains missing evidence |
| `narration` | O | untrusted string | `narration` | Preserved exactly |

Journal identity is `(journal_id, line_number)`. A journal must balance by currency:

```text
sum(debit_amount) == sum(credit_amount)
```

The initial synthetic account roles are demonstrative, versioned policy inputs:

| Account code | Role |
|---|---|
| `110000` | Merchant bank |
| `120000` | Gateway clearing |
| `510000` | Gateway fee expense |
| `140000` | Input GST/tax receivable |

Matchers must use policy roles rather than these literal codes.

## Lineage fields created by adapters

The source files do not contain these values. Import infrastructure derives and records them:

- source file ID and SHA-256;
- sheet/table name;
- one-based physical source row number;
- stable raw-row SHA-256;
- mapping-profile version;
- canonical event ID.

## Fixture purpose

Files under `tests/fixtures/schema/` are deliberately minimal. Valid fixtures establish
column layout and raw representation. Invalid fixtures retain bad values so Segment 3 can
prove precise file/sheet/row/field diagnostics rather than silently dropping rows.
