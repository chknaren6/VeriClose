# Initial Assumptions

These assumptions are intentionally provisional until the 65% practitioner review.

- The default entity uses INR and paise.
- Gateway, bank and ERP source ranges overlap sufficiently for one reconciliation run.
- Gateway settlement identifiers and bank UTRs are preferred identity evidence when present.
- Settlement composition signs and required ERP accounts come from a versioned policy pack.
- Exact reference equality is insufficient when amount, direction, accounting balance or uniqueness fails.
- Small synthetic batches can run synchronously in one process.
- Judge and hosted-demo data is synthetic and short-lived.
- Production ERP writes are represented through export/corrected-import during the hackathon.

Each accepted practitioner correction should update this file, a policy, or an ADR and add a regression test.
