# VeriClose: Framework for Building From Here

This framework separates release-critical work from deliberate post-MVP expansion. The current
controller already owns the core loop: import → deterministic proof → evidence review → approved
action → immutable export/corrected source → re-run. The next work must protect that loop.

## 1. Current foundation

| Layer | Current responsibility | Rule for future work |
|---|---|---|
| `domain` | Money, directions, proof levels, actions and immutable invariants | No web, storage, parsing or model imports. |
| `adapters` / `ingestion` | CSV/XLSX detection, validation, normalization and lineage | A new source passes the shared detect/validate/normalize/control-total contract. |
| `reconciliation` | Deterministic candidate bounds, accounting checks, risk gate and exceptions | Matching changes start with a failing regression and adversarial test. |
| `investigation` | Read-only advisory explanation and grounded Q&A | Models cannot alter proof, source evidence, auto-clear status or posting state. |
| `application` | Reviews, approvals, exports, corrections and re-runs | Side effects must be explicit, approval-gated, idempotent and audited. |
| `infrastructure` | DuckDB, immutable files, artifacts and optional model transport | Concrete dependencies are wired only in API composition. |

## 2. Release path: finish the submission honestly

### Gate A — Practitioner evidence (blocks M5 and M7)

Run the prepared blinded review instead of inventing results.

1. Run `make review-pack` and conduct one uncoached practitioner session on the provided 25 cases.
2. Complete the structured labels and priority forms under `docs/practitioner/review_01/`.
3. Run `make review-analyze`; it deliberately refuses incomplete input.
4. Translate accepted corrections into a failing test, then a policy/rule/UX change.
5. Re-run `make benchmark` and retain the holdout for the later review.

Exit evidence: a proportional `DOMAIN_REVIEW_01.md`, promoted synthetic golden cases, and a
benchmark report that records any trade-off. Do not claim practitioner validation until this exists.

### Gate B — Hosted release (blocks M8)

Deploy the already-tested image; do not create a second serving path.

1. Choose a container host with HTTPS and a writable volume or an explicitly ephemeral runtime.
2. Set `VERICLOSE_ENVIRONMENT=hosted-demo`, `VERICLOSE_DEMO_MODE=true`, and server-side optional
   model credentials only if required.
3. Record the immutable image/build identifier in `VERICLOSE_BUILD_COMMIT`.
4. Use **Restore demo** to create a fresh known-seed run; it never accepts a caller-supplied path.
5. Run `BASE_URL=https://… make smoke` and save the JSON result.
6. Record the five-minute video from that URL, showing a proved case, one unresolved case,
   fallback/advisory behavior, an approval, export and correction re-run.

Exit evidence: URL, smoke result, retention decision, browser checklist and video link. A hosted
URL and video require human account/hosting authority and are intentionally not fabricated here.

## 3. Change framework for any finance behavior

Use this sequence for every new rule, source adapter, action, or workflow pack:

```text
Observed evidence or practitioner finding
  → classify scope (policy, rule, adapter, UI, or workflow)
  → add a failing deterministic/adversarial test
  → implement behind the inward dependency boundary
  → add evidence, approval and idempotency behavior
  → run benchmark and release checks
  → record metric impact and known limitation
```

Decision guide:

| Proposed change | Required artifacts before merge |
|---|---|
| Match or auto-clear behavior | Regression + adversarial tests, benchmark delta, policy version change if configurable. |
| New input layout | Adapter contract suite, control totals, fixtures, mapping version and validation details. |
| New financial action | Evidence requirements, approval state, immutable receipt, retry/idempotency test and export/correction boundary. |
| Model capability | Schema, post-validation, disabled-model fallback and proof-isolation test. |
| Product/UX change | Practitioner observation or task hypothesis, accessible controls, no accounting recalculation in the UI. |
| Architecture change | ADR before moving a dependency boundary. |

## 4. Post-MVP expansion sequence

These are P2 work items and must not be merged into the frozen INR, one-merchant MVP without an
explicit scope decision.

1. **Additional mappings and adapters.** Add a second gateway, bank layout or ERP export through
   the adapter contract. Do not generalize the reconciliation kernel first.
2. **Fee/GST leakage pack.** Add a versioned commercial rate card, deterministic expected-fee
   checks and an evidence-backed recovery pack.
3. **Refund/chargeback lifecycle.** Add explicit state transitions linking reversals to original
   payments and settlements.
4. **Policy drift proposal.** Compare verified historical runs with a proposed policy version;
   require human approval and benchmark it before activation.
5. **Read-only connectors.** Add scoped credentials, checkpoints, rate limits and audit. Keep
   source edits and ERP posting out of the connector.
6. **Multi-entity/currency.** This is a kernel change: first add entity isolation, currency-specific
   minor units, FX evidence and cross-entity/currency abstention tests.

## 5. Non-negotiable release checklist

- `make verify` passes.
- `make benchmark` passes with zero false clears under its published threshold.
- `make image` and `make smoke-container` pass without a model key.
- The UI can restore the synthetic demo, preserve one unresolved case, and complete one approved
  correction loop.
- `docs/examples/manifest.json` traces example artifacts to the known seed and build identifier.
- No runtime module imports hidden truth or evaluation labels.
- No real finance data, credentials, model key, or live ERP write-back is introduced.

## 6. Current external blockers

The repository is ready for the gates below, but they require authority or observation outside this
workspace:

- real practitioner review and holdout review;
- hosted container account, HTTPS URL and external smoke execution;
- five-minute hosted-demo recording;
- final deploy-time trust review against the hosted URL.
