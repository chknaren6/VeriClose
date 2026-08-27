# VeriClose Opportunities Beyond the Frozen MVP

## Purpose

This file records valuable additions without silently expanding or redirecting the current
MVP. None of these should be implemented until the three-source settlement workflow is
complete, tested and demonstrable end to end.

## Best next additions

### 1. Fee and GST leakage auditor

Compare gateway deductions with a versioned commercial rate card and the corresponding ERP
expense/tax lines. Quantify possible overcharges or missed input-tax postings, then prepare an
evidence pack and reviewed claim/journal proposal.

Why it is attractive: it turns reconciliation from a control exercise into measurable rupee
recovery while reusing the existing settlement evidence.

### 2. Refund and chargeback lifecycle controller

Trace the original payment through refund/chargeback initiation, gateway processing,
settlement impact and ERP/customer-ledger posting. Flag stuck, duplicated, late or incorrectly
posted reversals.

Why it is attractive: it adds temporal reasoning and state-machine design without weakening
the evidence-first approach.

### 3. Policy drift detector

Compare newly verified runs with approved fee, tax, timing and account-mapping policies.
Surface a new pattern for review instead of silently adapting matching rules.

Why it is attractive: it is a credible AI/data extension—learning helps propose policy
changes, while humans and regression benchmarks control adoption.

### 4. Read-only connectors and saved mapping profiles

After file ingestion is reliable, add saved company mappings, additional banks/gateways/ERPs,
and read-only API or SFTP ingestion. Keep the same adapter contract and proof semantics.

Why it is attractive: it demonstrates platform design and integration engineering. Direct ERP
write-back should remain later and require approval, idempotency, dry-run preview and receipts.

### 5. Verified cash-position forecast

Use reconciled cash as the trusted opening balance, then combine pending settlements and
approved outflows to forecast near-term liquidity with explicit uncertainty.

Why it is attractive: it connects the project to the broader “run the books and cash
position” challenge, but only after the underlying cash has been proved.

## Additional workflow packs, later

- Marketplace split-settlement verification for seller transfers and platform fees.
- Vendor statement/AP reconciliation for invoices, credits and duplicate payments.
- ERP migration proof packs for opening balances, control totals and missing masters.
- Intercompany reconciliation with bilateral evidence and dispute ownership.

Each new workflow pack must define its required canonical events, deterministic proof rules,
exception taxonomy, allowed actions, synthetic generator and hidden-truth evaluator. If it
cannot reuse the existing evidence, review, audit and evaluation contracts, it needs an ADR
before changing the verification kernel.

## Portfolio enhancements that do not broaden finance scope

These improve the internship signal while keeping the MVP focused:

- a reproducible adversarial benchmark with a published methodology;
- property-based tests for money signs, journal balance and grouping invariants;
- a concise architecture diagram and two-minute technical walkthrough;
- a case-study page explaining a detected issue and the avoided false clear;
- performance profiling on increasing batch sizes;
- typed API documentation and a clean deployment/smoke-test story;
- an anonymized practitioner review showing what feedback changed and why.

These are more valuable than adding a generic chatbot, unsupported “AI accuracy,” production
write access or many shallow integrations.

## Recommended sequencing

1. Finish the frozen settlement-to-bank-to-ERP MVP and its correction/re-run loop.
2. Validate it with a finance practitioner and convert accepted feedback into tests.
3. Harden the benchmark, adversarial cases and deployment story.
4. Add the fee/GST leakage auditor as the first adjacent module.
5. Add policy-drift proposals or refund lifecycle tracking as the AI/data differentiator.
6. Add connectors only when the source-adapter contract is proven across file layouts.

