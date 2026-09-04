# Assumptions and current policy

These values are provisional and must be challenged during review.

- One legal entity and INR per run.
- Money is exact integer paise with explicit debit/credit direction.
- Gateway settlement → bank receipt window: 0–3 calendar days.
- Bank receipt → ERP posting window: no more than 3 days.
- Settlement component, bank receipt and ERP posting amount tolerances: ₹0.00.
- Bank account: `110000` debit; clearing: `120000` credit.
- Fee account: `510000` debit; tax account: `140000` debit.
- Auto-clear requires gateway uniqueness, component arithmetic, bank presence/amount/direction/
  reference/date/uniqueness, ERP presence/uniqueness/balance, and every configured posting role.
- Narration similarity is advisory and cannot create proof.
- Duplicate, ambiguous, bounded-out, contradicted and invalid-input cases abstain.
- Preliminary review never mutates canonical evidence or the prior decision.

The authoritative machine-readable policy is `config/policies/razorpay_inr_v1.yaml`. Any accepted
change must first receive a failing regression test and must publish before/after benchmark impact.

