# VeriClose Execution Tasks

## How to use this file

This is the implementation control document for VeriClose. Work in task-ID order unless a dependency explicitly permits parallel work. Completion percentages represent demonstrated product capability, not the percentage of checkboxes completed.

Priority labels:

- **P0:** required for a credible hackathon submission
- **P1:** strong differentiator; build after P0 dependencies are stable
- **P2:** post-hackathon or only if the submission is already complete

Rules:

1. Do not mark a segment complete until its exit gate passes.
2. Do not replace failed acceptance criteria with screenshots or hardcoded demo data.
3. If schedule slips, cut P2 and visual polish before cutting evidence, evaluation, or failure recovery.
4. Record architecture changes in an ADR and domain changes in the relevant domain document.
5. New matching behavior requires a failing test before implementation and a passing regression test afterward.
6. Never add real client data, credentials, or confidential mappings to the repository.

## Milestone map

| Milestone | Capability | Completion point |
|---|---|---:|
| M0 | Scope, contracts and repository skeleton | 10% |
| M1 | Synthetic truth, adapters and validated canonical data | 25% |
| M2 | Deterministic verification kernel | 45% |
| M3 | Honest evaluation harness — complete | 55% |
| M4 | Thin end-to-end review product — complete | 65% |
| M5 | First practitioner review incorporated | 75% |
| M6 | Bounded AI and correction loop | 88% |
| M7 | Hardening, production image and holdout practitioner review | 95% |
| M8 | Submission-ready repository and video | 100% |

## Critical-path commands

These commands should exist by the indicated milestone:

```text
make setup       # M0
make test        # M0, progressively expanded
make generate    # M1
make reconcile   # M2
make benchmark   # M3
make dev         # M4
make demo        # M6
make smoke       # M7: exercise a running deployment from outside
make judge       # M7: build and start the judge-local container profile
make verify      # M8: lint + tests + benchmark + production build
```

## Current implementation checkpoint — 2026-08-29

The **M0–M4 milestones through Segment 6 are complete**.
The repository now has pure immutable finance types, explicit source contracts, hidden
event/case truth, deterministic source generation, controlled scenario injectors, and a
reproducible 50+ record batch in addition to the deployable shell. The adapter boundary now
returns typed detection, validation, normalization, quarantine, and control-total results;
CSV/XLSX gateway, bank, and ERP data can be imported into immutable files and DuckDB records.

Verified at this checkpoint:

- `uv sync --dev` and `pnpm install --frozen-lockfile` install from lockfiles.
- `make verify` passes lint, the full backend/architecture test suite, frontend type checking,
  and the production web build.
- `make smoke-local PORT=8011` starts the API and exercises readiness and metadata.
- `make image` and `make smoke-container PORT=8012` build and exercise the exact
  judge-facing container without a model key.
- The production page was opened in a browser; it reached `/health/ready` and
  `/api/meta`, displayed the deterministic fallback, and produced no console errors.
- `make generate` produces 315 source rows for the default seed across gateway, bank,
  and ERP, plus a manifest and private truth labels.
- `make import-batch` takes the three generated inputs through detect, map, staged validation,
  normalization, control totals, immutable file storage, and transactional DuckDB persistence.
- The default 315-row seed imports as `VALIDATED`; its intentionally unbalanced journal remains
  canonical evidence and is persisted as a non-blocking `JOURNAL_UNBALANCED` accounting issue.
- `make reconcile` imports and closes the default 315-row batch into 25 decisions: 15 strictly
  proved auto-clears and 10 evidence-backed exceptions across all five proof levels.
- 168 tests cover domain and policy invariants, adapters, exact parsing, staged diagnostics,
  immutable persistence, every synthetic scenario, false-clear prevention, deterministic row
  ordering, bounded grouping, safe failure states, and truth isolation.

What this checkpoint intentionally **does not** claim:

- production action execution, journal export, and corrected-data re-runs remain later segments;
- operational screens never display benchmark-only accuracy claims;
- no AI judgment exists;
- dashboard numbers are not mocked.

The next executable task is **S7.1, practitioner review preparation**. Segment 6 satisfies the M4
exit gate; hidden truth remains isolated from operational API and UI code.

---

# Segment 0 — Product contracts and safety rules (0–5%)

## S0.1 Freeze the MVP boundary — P0

- [x] Write the supported entity, currency, source, format and workflow boundary.
- [x] Write the explicit non-goals.
- [x] Define the one-sentence product promise.

Depends on: none.

Acceptance criteria:

- The boundary matches `PROJECT_PLAN.md`.
- A feature can be classified as MVP, later adapter, later workflow pack, or rejected.
- Multi-currency, live ERP posting and general migration are not accidentally in the MVP.

## S0.2 Define domain terminology — P0

- [x] Create `docs/domain/GLOSSARY.md`.
- [x] Define event, settlement, match group, proof check, exception, review and action.
- [x] Define record-level versus case-level evaluation.

Depends on: S0.1.

Acceptance criteria:

- Terms are used consistently across schemas, APIs, UI and metrics.
- “Match,” “verified,” “supported” and “resolved” are not used interchangeably.

## S0.3 Write product invariants — P0

- [x] Record money representation and direction rules.
- [x] Record proof-level and auto-clear rules.
- [x] Record evidence and lineage requirements.
- [x] Record LLM authority boundaries.
- [x] Record ground-truth isolation requirements.

Depends on: S0.1, S0.2.

Acceptance criteria:

- Every invariant can later be covered by a test or static check.
- Confidence alone cannot auto-clear a case.
- Runtime modules are forbidden from importing benchmark truth.

## S0.4 Create the root `AGENTS.md` — P0

- [x] Add project objective and MVP boundary.
- [x] Add architecture dependency rules.
- [x] Add finance-safety and data-safety constraints.
- [x] Add required commands and change-validation expectations.
- [x] Add AI and benchmark constraints.

Depends on: S0.1–S0.3.

Acceptance criteria:

- The file is concise enough for coding agents to follow.
- It links to deeper documents rather than duplicating the entire project plan.
- It forbids real client data, floating-point money, ground-truth leakage and unverified auto-clears.

## S0.5 Create initial ADRs — P0

- [x] ADR-001: deterministic verification before LLM investigation.
- [x] ADR-002: canonical model and immutable lineage.
- [x] ADR-003: strict proof levels and risk gate.
- [x] ADR-004: hidden-truth evaluation design.
- [x] ADR-005: modular monolith.

Depends on: S0.3.

Acceptance criteria:

- Each ADR contains context, decision, alternatives and consequences.
- The decision can be understood without reading source code.

### Segment 0 exit gate

- [x] Scope, terminology, invariants, `AGENTS.md` and ADRs agree.
- [x] No implementation dependency points inward from `core/domain` to adapters, UI or model code.

---

# Segment 1 — Repository and engineering foundation (5–10%)

## S1.1 Scaffold the modular monolith — P0

- [x] Create backend, frontend, core, config, synthetic, evaluation, tests and docs directories.
- [x] Add package metadata and dependency management.
- [x] Add environment-example file without secrets.

Depends on: Segment 0.

Acceptance criteria:

- Backend and frontend start independently.
- Runtime, synthetic and evaluation packages have explicit boundaries.
- A clean environment can install dependencies from documented commands.

## S1.2 Add developer commands — P0

- [x] Implement `make setup`.
- [x] Implement `make test`.
- [x] Add lint and formatting commands.
- [x] Add a basic health check.

Depends on: S1.1.

Acceptance criteria:

- Commands return non-zero on failure.
- Setup does not require undocumented global software beyond listed prerequisites.

## S1.3 Establish configuration loading — P0

- [x] Define typed application settings.
- [x] Separate local defaults from secrets.
- [x] Add model-disabled mode.
- [x] Add deterministic seed and policy-version configuration.

Depends on: S1.1.

Acceptance criteria:

- Missing optional model credentials do not prevent deterministic reconciliation.
- Secrets are ignored by version control.

## S1.4 Reserve persistence boundaries — P0

- [x] Reserve `ports` and `infrastructure` packages without importing infrastructure into domain code.
- [x] Document that original files/events are immutable and review/action state is append-only.
- [x] Defer protocols and DuckDB tables until canonical types exist; track their implementation in S3.7.

Depends on: S1.1, S0.3.

Acceptance criteria:

- The skeleton makes the eventual dependency direction explicit.
- No database choice leaks into domain or application code.
- Concrete storage work is not falsely represented as complete.

## S1.5 Add automated checks — P1

- [x] Add a local `make verify` placeholder that grows with milestones.
- [x] Add CI for lint and tests.
- [ ] Add dependency and secret scanning if time permits.

Depends on: S1.2.

Acceptance criteria:

- A broken test blocks the check.
- No demo result is required for the initial skeleton.

## S1.6 Define judge-runtime configuration — P0

- [x] Define `development`, `judge-local`, `hosted-demo` and `benchmark` profiles.
- [x] Make host, port, data directory, database path, upload limit and demo mode configurable.
- [x] Define model-optional behavior and safe startup defaults.
- [x] Create ADR-009 for the single-image deployment decision.

Depends on: S1.1, S1.3.

Acceptance criteria:

- No runtime path assumes the developer’s home directory.
- Missing model credentials do not fail startup.
- Hosted-demo behavior can be enabled without editing source code.

## S1.7 Prove the deployment skeleton early — P0

- [x] Add an initial multi-stage Dockerfile for the API health endpoint and frontend shell.
- [x] Serve compiled frontend assets and `/api/*` on one origin.
- [x] Add an initial Compose service and `judge-local` configuration.
- [x] Start the container without a model key.

Depends on: S1.1, S1.2, S1.6.

Acceptance criteria:

- `make image && make smoke-container` serves and checks the UI shell and health endpoint by M0.
- `docker compose up --build` is the equivalent convenience path when the host has the Compose plugin.
- The implementation may be skeletal, but the final deployment path is already exercised.
- Later product code replaces behavior inside the same image rather than inventing a second deployment architecture.

### Segment 1 exit gate — M0 (10%)

- [x] Fresh setup succeeds.
- [x] Backend health endpoint and frontend shell run.
- [x] Test skeleton and repository boundaries are documented.
- [x] Judge runtime profiles and writable-path rules are documented.
- [x] The walking-skeleton production container starts successfully.

---

# Segment 2 — Canonical domain and synthetic truth (10–18%)

## S2.1 Implement canonical domain types — P0

- [x] In `domain/enums.py`, define source, event, direction, proof-level, decision-state,
  exception-category, severity, review-state, and action-state enums using stable wire values.
- [x] In `domain/money.py`, implement an immutable money value object that accepts integer
  minor units only, requires an ISO currency code, and performs same-currency arithmetic.
- [x] In `domain/events.py`, implement immutable `RawRowRef` and `CanonicalEvent` types with
  source file hash, sheet/table name, 1-based row number, canonical event ID, entity,
  amount, direction, dates, source references, and preserved raw metadata.
- [x] In `domain/runs.py`, implement `RunManifest` and `SourceFile` with seed, policy version,
  mapping versions, input hashes, build ID, creation time, and run-state transitions.
- [x] In `domain/evidence.py`, implement `MatchGroup`, `ProofCheck`, and `EvidenceLink` so
  expected/observed/tolerance values and precise source rows are serializable.
- [x] In `domain/decisions.py`, keep `MatchProposal` separate from the final
  `ReconciliationDecision`; a proposal is rule output, while a decision is risk-gate output.
- [x] In `domain/exceptions.py` and `domain/actions.py`, implement `ExceptionCase`,
  `ProposedAction`, `ReviewDecision`, and `ActionReceipt` with typed state transitions.
- [x] Add focused tests under `tests/unit/domain/` for paise boundaries, lineage requirements,
  invalid enum/state transitions, proof-versus-support separation, and balanced journals.

Depends on: S0.2, S0.3, S1.1.

Acceptance criteria:

- Monetary values accept integer minor units only.
- Currency and direction are required.
- Events cannot exist without source lineage.
- Proof level is distinct from support/confidence score.
- Domain modules import no FastAPI, database, dataframe, provider-SDK, or synthetic-truth code.
- Round-trip serialization preserves stable IDs, integer amounts, and evidence coordinates.

## S2.2 Specify source schemas — P0

- [x] Create `docs/domain/SOURCE_SCHEMAS.md` with one canonical-field mapping table per source.
- [x] Specify gateway payment/refund/fee/tax/adjustment/settlement fields, sign semantics,
  references, and event dates.
- [x] Specify both bank layouts: signed amount and separate debit/credit columns; define value
  date, booking date, UTR, narration, and bank-account identity behavior.
- [x] Specify ERP journal header/line fields, debit/credit rules, external references, account
  role mapping, and journal grouping keys.
- [x] Mark every field required, optional, derived, preserved-only, or rejected, including its
  accepted types and null behavior.
- [x] Add minimal CSV fixtures under `tests/fixtures/schema/` representing one valid row/layout
  and one intentionally invalid row/layout for each source.

Depends on: S2.1.

Acceptance criteria:

- Each source field maps unambiguously to canonical data or preserved raw metadata.
- Sign, date and reference behavior is explicit.

## S2.3 Design truth labels — P0

- [x] Define expected match-group labels.
- [x] Define expected proof disposition.
- [x] Define exception type, severity and expected next action.
- [x] Define valid timing differences separately from anomalies.

Depends on: S2.1, S2.2.

Acceptance criteria:

- Labels support event-level and case-level scoring.
- Truth does not contain hints embedded in runtime source fields.

## S2.4 Build deterministic synthetic generator — P0

- [x] Generate clean payments, settlements, bank credits and ERP journals.
- [x] Support seed, record count and exception-rate arguments.
- [x] Generate source files independently from truth labels.
- [x] Generate a manifest containing scenario counts and control totals.

Depends on: S2.2, S2.3.

Acceptance criteria:

- The same seed produces byte-for-byte or semantically identical data.
- Different seeds meaningfully alter identities, amounts, dates and scenario placement.
- A default batch comfortably exceeds 50 records.

## S2.5 Implement scenario injectors — P0

- [x] Clean exact match.
- [x] Many payments to one settlement.
- [x] Partial settlement.
- [x] Refund applied in a later settlement.
- [x] Legitimate working-day date shift.
- [x] Missing or mistyped reference.
- [x] Duplicate source or ERP posting.
- [x] Missing bank credit.
- [x] Missing ERP posting.
- [x] Incorrect fee or tax.
- [x] Amount mismatch.
- [x] Orphan bank credit.
- [x] Unbalanced ERP journal.
- [x] Equal-amount ambiguous candidates.

Depends on: S2.4.

Acceptance criteria:

- Each injector has a focused test.
- Each scenario records its expected disposition.
- Valid partial/timing behavior is not labelled as an error.

## S2.6 Enforce truth isolation — P0

- [x] Place truth in an evaluation-only path/package.
- [x] Add an import-boundary test preventing runtime access.
- [x] Ensure API responses never expose hidden labels during reconciliation.

Depends on: S2.3, S2.4.

Acceptance criteria:

- Runtime tests fail if reconciliation imports truth modules.
- The UI cannot fetch truth except through an explicitly benchmark-only endpoint/mode.

### Segment 2 exit gate

- [x] `make generate` creates three valid source files, truth and a manifest.
- [x] Scenario counts and control totals are reproducible.
- [x] Truth-isolation test passes.

---

# Segment 3 — Adapter, mapping and validation pipeline (18–25%)

## S3.1 Define source-adapter contract — P0

- [x] Define detect, validate, normalize and control-total methods.
- [x] Define typed detection and validation reports.
- [x] Define mapping-profile version behavior.

Depends on: S2.1, S2.2.

Acceptance criteria:

- Matching code has no dependency on source-specific column names.
- An adapter cannot silently drop invalid rows.

## S3.2 Implement Razorpay-style gateway adapter — P0

- [x] Support CSV and XLSX.
- [x] Parse payments, refunds, fees, taxes, adjustments and settlement references.
- [x] Preserve raw sign and map canonical direction.
- [x] Produce component control totals.

Depends on: S3.1.

Acceptance criteria:

- Generated gateway fixtures normalize correctly.
- Unknown event types are rejected or explicitly quarantined.

## S3.3 Implement generic bank adapter — P0

- [x] Parse debit/credit or signed-amount layouts.
- [x] Extract value date, narration and UTR/reference.
- [x] Preserve unmatched narration as untrusted text.

Depends on: S3.1.

Acceptance criteria:

- Both debit/credit-column and signed-amount fixtures normalize consistently.
- Direction and amount never depend on floating-point values.

## S3.4 Implement generic ERP GL adapter — P0

- [x] Parse journal, line, account, debit, credit, date and external reference.
- [x] Group journal lines.
- [x] Verify journal balance before reconciliation.

Depends on: S3.1.

Acceptance criteria:

- Unbalanced journals are visible validation/accounting exceptions.
- Clearing, bank, fee and tax account roles come from policy, not hardcoded names.

## S3.5 Implement mapping profiles — P0

- [x] Define versioned profile schema.
- [x] Support column aliases and safe transforms.
- [x] Add auto-detection scoring with explicit user confirmation.
- [x] Save selected mapping to the run manifest.

Depends on: S3.2–S3.4.

Acceptance criteria:

- At least two alternate layouts per source normalize to equivalent canonical events.
- Required mappings cannot be accepted ambiguously.

## S3.6 Implement staged validation — P0

- [x] File validation.
- [x] Schema validation.
- [x] Semantic validation.
- [x] Accounting validation.
- [x] Cross-source readiness validation.

Depends on: S3.2–S3.5.

Acceptance criteria:

- Errors contain file, sheet, row, field, supplied value, code and suggested fix.
- Duplicate upload is detected by hash.
- Date-range, entity and currency conflicts are visible before matching.

## S3.7 Persist raw and canonical layers — P0

- [x] Define `RunRepository`, `SourceFileRepository`, `EventRepository`,
  `DecisionRepository`, `ReviewRepository`, and `AuditRepository` protocols in
  `core/vericlose/ports/repositories.py`; use domain types in signatures and expose no SQL.
- [x] Define `FileStore` in `core/vericlose/ports/file_store.py` with immutable put/get/hash
  operations and run-scoped paths.
- [x] Create versioned DuckDB migrations for runs, files, canonical events, proof checks,
  evidence links, decisions, exceptions, reviews, actions, receipts, and audit events.
- [x] Implement DuckDB repositories under `core/vericlose/infrastructure/duckdb/` with explicit
  unit-of-work/transaction boundaries for import, decision persistence, and review/action writes.
- [x] Implement `LocalFileStore` that validates paths, uses content hashes, never overwrites an
  original upload, and stores only beneath the configured data directory.
- [x] Save adapter version, mapping-profile version, policy version, file SHA-256, source row,
  and canonical event ID so every value is reconstructable.
- [x] Add fake-repository contract tests plus a temporary-directory DuckDB integration test.
- [x] Prove that a review or proposed correction appends new state and cannot update the raw or
  canonical source layers.

Depends on: S1.4, S3.2–S3.6.

Acceptance criteria:

- Every canonical event can be traced back to a precise source row.
- Re-import creates a new run/version rather than mutating history.

### Segment 3 exit gate — M1 (25%)

- [x] Three source files pass through upload/detect/map/validate/normalize.
- [x] Alternate layouts produce equivalent canonical results.
- [x] Malformed inputs fail with precise diagnostics.

---

# Segment 4 — Deterministic verification kernel (25–45%)

## S4.1 Define policy-pack schema — P0

- [x] Define currency and date policy.
- [x] Define component and account roles.
- [x] Define amount tolerances.
- [x] Define auto-clear eligibility.
- [x] Define allowed actions and severity behavior.

Depends on: S2.1, S3.1.

Acceptance criteria:

- `razorpay_inr_v1` is versioned and validated at startup.
- Rules read policies through a stable interface.

## S4.2 Implement candidate blocking — P0

- [x] Block by legal entity and currency.
- [x] Block by compatible event type.
- [x] Apply bounded date windows.
- [x] Exclude already-consumed candidates where policy requires uniqueness.

Depends on: S4.1, Segment 3.

Acceptance criteria:

- Candidate sets remain bounded on the default dataset.
- Impossible cross-currency and cross-entity candidates never proceed.

## S4.3 Implement exact-identifier rules — P0

- [x] Settlement-reference matching.
- [x] UTR matching.
- [x] ERP external-reference matching.
- [x] Duplicate/conflicting identifier detection.

Depends on: S4.2.

Acceptance criteria:

- Exact identity alone does not auto-clear until amount and uniqueness checks pass.
- Conflicting exact IDs become contradictions, not arbitrary wins.

## S4.4 Implement settlement component invariant — P0

- [x] Sum payment, refund, fee, tax and adjustment components using policy signs.
- [x] Compare expected settlement with source settlement total.
- [x] Record expected, observed, variance and tolerance as proof checks.

Depends on: S4.1, S4.3.

Acceptance criteria:

- Calculations use integer minor units.
- Incorrect fee/tax and partial settlement cases behave as labelled.

## S4.5 Implement bank receipt proof — P0

- [x] Verify amount and direction.
- [x] Verify UTR/reference when available.
- [x] Verify allowed value-date behavior.
- [x] Detect missing and duplicate bank receipts.

Depends on: S4.3, S4.4.

Acceptance criteria:

- Legitimate timing shifts are not false exceptions.
- Amount-equal but ambiguous receipts do not auto-clear.

## S4.6 Implement ERP posting proof — P0

- [x] Verify bank and clearing postings.
- [x] Verify fee and tax account behavior.
- [x] Verify journal balance.
- [x] Detect wrong direction, wrong account, missing and duplicate postings.

Depends on: S4.4, S4.5.

Acceptance criteria:

- Account roles come from the policy pack.
- A settlement cannot be fully proved when required ERP evidence is absent.

## S4.7 Implement bounded grouping — P0

- [x] One-to-many membership matching.
- [x] Many-to-one aggregation where policy permits.
- [x] Enforce maximum candidate/group size and date window.
- [x] Reject non-unique valid groupings as ambiguous.

Depends on: S4.2, S4.4–S4.6.

Acceptance criteria:

- Group search has deterministic ordering and explicit bounds.
- Multiple valid subsets never produce an auto-clear.

## S4.8 Implement candidate support scoring — P1

- [x] Score amount, date, reference-token and narration similarity.
- [x] Preserve a feature breakdown for review.
- [x] Use scoring only after proof rules fail.

Depends on: S4.2.

Acceptance criteria:

- Support score can rank but cannot create `PROVED`.
- Fuzzy text never bypasses accounting invariants.

## S4.9 Implement proof-level risk gate — P0

- [x] Map proposal checks to `PROVED`, `SUPPORTED`, `AMBIGUOUS`, `CONTRADICTED` or `INVALID_INPUT`.
- [x] Apply policy-level auto-clear permission.
- [x] Record decision and reason codes.

Depends on: S4.3–S4.8.

Acceptance criteria:

- Only unique proposals with all required hard checks can auto-clear.
- Unit tests cover every proof-level transition.

## S4.10 Implement exception creation and prioritization — P0

- [x] Assign stable reason code and severity.
- [x] Calculate amount at risk deterministically.
- [x] Attach rules attempted and evidence rows.
- [x] Set recommended workflow state and company-input flag.

Depends on: S4.9.

Acceptance criteria:

- No unresolved case lacks a reason, evidence or next-action category.
- Unknown remains a valid honest classification.

## S4.11 Implement deterministic run orchestration — P0

- [x] Execute validation, normalization, matching, risk gating and persistence.
- [x] Store stage timings and counts.
- [x] Add run-state transitions and safe failure states.
- [x] Implement `make reconcile`.

Depends on: Segment 3, S4.1–S4.10.

Acceptance criteria:

- Same inputs and versions reproduce deterministic decisions.
- Failed runs do not appear completed.
- CLI outputs a close summary and exception file.

### Segment 4 exit gate — M2 (45%)

- [x] Complete synthetic batch reconciles without UI or LLM.
- [x] Every decision has proof checks and source-row evidence.
- [x] Fuzzy or ambiguous cases never auto-clear.

---

# Segment 5 — Evaluation and regression system (45–55%)

## S5.1 Implement event-level evaluator — P0

- [x] Compare predicted group and disposition with truth.
- [x] Report per-scenario correctness.
- [x] List incorrect event IDs.

Depends on: S2.6, S4.11.

Acceptance criteria:

- Metrics are derived from stored outputs and isolated truth.
- Incorrect IDs can be reopened in a diagnostic report.

## S5.2 Implement case-level evaluator — P0

- [x] Score proved, review and exception decisions.
- [x] Calculate auto-match precision, exception recall and false-clear rate.
- [x] Produce confusion matrix.

Depends on: S5.1.

Acceptance criteria:

- Metric denominators are documented and tested.
- A false-clear is distinguishable from a wrong exception classification.

## S5.3 Add multi-seed benchmark — P0

- [x] Run at least five seeds during normal development and ten for submission.
- [x] Record dataset size, scenario mix and exception rate.
- [x] Report p50/p95 runtime and throughput.
- [x] Implement `make benchmark`.

Depends on: S5.1, S5.2.

Acceptance criteria:

- Results are not copied into source code.
- A single favorable seed cannot hide failures in others.

## S5.4 Add safety thresholds — P0

- [x] Configure target auto-clear precision.
- [x] Configure target exception recall.
- [x] Configure allowed false-clear count/rate.
- [x] Fail the command when thresholds are missed.

Depends on: S5.3.

Acceptance criteria:

- Lowering a metric through an injected bug fails the benchmark.
- Threshold changes require documentation.

## S5.5 Create adversarial suite — P0

- [x] Equal amount and equal date candidates.
- [x] Duplicate IDs with conflicting amounts.
- [x] Boundary and invalid dates.
- [x] Very large paise amounts.
- [x] Prompt-like text in narration.
- [x] Missing columns and malformed workbook sheets.
- [x] Unbalanced and reversed journals.

Depends on: S5.2.

Acceptance criteria:

- Each case has an explicit expected safe outcome.
- Prompt-like narration cannot affect deterministic status.

## S5.6 Add property-based accounting tests — P1

- [x] Amount normalization never loses paise.
- [x] Balanced journals remain balanced after normalization.
- [x] Permuting source-row order does not change results.
- [x] Record the duplicate-action idempotency invariant; executable action application begins in S8.

Depends on: S4.11.

Acceptance criteria:

- Tests explore generated boundary values rather than only fixed examples.

### Segment 5 exit gate — M3 (55%)

- [x] Benchmark reports event and case results over multiple seeds.
- [x] False-clear failures block the benchmark.
- [x] Incorrect cases are inspectable, not hidden behind aggregate metrics.

---

# Segment 6 — Thin end-to-end review product (55–65%)

## S6.1 Define API contracts — P0

- [x] Liveness, readiness and build-metadata endpoints.
- [x] Upload/detect/map/validate endpoints.
- [x] Start/get run endpoints.
- [x] List/get case endpoints.
- [x] Evidence and proof-check endpoints.
- [x] Operational and benchmark metric endpoints.
- [x] Review-state endpoint without financial mutation.

Depends on: S4.11, Segment 5.

Acceptance criteria:

- API schemas use domain terminology.
- Benchmark truth is available only in explicit synthetic benchmark mode.
- Readiness checks policies, database, writable storage and production assets where applicable.

## S6.2 Build import and mapping screen — P0

- [x] Add gateway, bank and ERP upload slots.
- [x] Show detected adapter/profile.
- [x] Show field mapping and sample rows.
- [x] Show exact validation errors and control totals.
- [x] Require confirmation for inferred required mappings.

Depends on: S3.5–S3.7, S6.1.

Acceptance criteria:

- A user can correct a mapping problem without opening the terminal.
- Invalid batches cannot start reconciliation.

## S6.3 Build run cockpit — P0

- [x] Show verified/review/unresolved counts and amounts.
- [x] Show amount at risk and reason distribution.
- [x] Show pipeline state and runtime.
- [x] Separate benchmark accuracy from operational status.

Depends on: S6.1.

Acceptance criteria:

- Live-mode screens do not claim precision or recall without truth.
- Summary totals reconcile with stored cases.

## S6.4 Build exception queue — P0

- [x] List case ID, reason, severity, amount at risk, proof level and next action.
- [x] Sort by severity and amount exposure.
- [x] Filter by state and reason.
- [x] Make unresolved external-information cases visible.

Depends on: S6.1, S6.3.

Acceptance criteria:

- Every non-proved case can be opened from the queue.
- Sorting does not hide unknown/ambiguous cases.

## S6.5 Build evidence-first case workbench — P0

- [x] Align gateway, bank and ERP source rows.
- [x] Show original and canonical values.
- [x] Show settlement equation and variance.
- [x] Show proof checks and rules attempted.
- [x] Visually separate verified facts from future AI/advisory space.

Depends on: S6.1, S6.4.

Acceptance criteria:

- A reviewer can explain the decision using only visible source evidence.
- Source file and row numbers are available.

## S6.6 Persist preliminary review state — P0

- [x] Allow reviewer classification, note and defer state.
- [x] Preserve previous decisions.
- [x] Add reviewer/time audit event.

Depends on: S1.4, S6.5.

Acceptance criteria:

- Review does not alter canonical source events.
- Refreshing the page preserves the review state.

## S6.7 Design all essential UI states — P1

- [x] Empty and first-run state.
- [x] Uploading, validating and processing state.
- [x] Validation failure state.
- [x] No-match and ambiguous states.
- [x] Model-unavailable placeholder.
- [x] No-exceptions success state.

Depends on: S6.2–S6.6.

Acceptance criteria:

- No expected state exposes a blank or misleading screen.
- Status is understandable without color alone.

### Segment 6 exit gate — M4 (65%)

- [x] A non-developer can upload, reconcile, inspect evidence and classify cases through the UI.
- [x] The product is functional but intentionally not final-polished.
- [x] Practitioner review pack can be prepared without inventing results.

---

# Segment 7 — First practitioner review and domain correction (65–75%)

## S7.1 Prepare practitioner review materials — P0

- [ ] Create five-minute walkthrough.
- [ ] Document current assumptions and policy values.
- [ ] Select 20–30 blinded cases across proof levels and exception types.
- [ ] Create structured label and feature-priority forms.
- [ ] List the five least-certain system decisions.

Depends on: M4.

Acceptance criteria:

- System decisions are hidden during initial blind labelling.
- Selected cases are not all easy or all from one seed.

## S7.2 Conduct observation session — P0

- [ ] Observe five cases without coaching.
- [ ] Record evidence inspection order.
- [ ] Record confusing terms and missing information.
- [ ] Avoid exposing client names or data.

Depends on: S7.1.

Acceptance criteria:

- Notes distinguish observed behavior from requested features.
- No real client artifact enters the repository.

## S7.3 Conduct blind case review — P0

- [ ] Capture expected status and proof level.
- [ ] Capture reason, evidence and severity.
- [ ] Capture next action and required journal behavior.
- [ ] Reveal and classify disagreements after independent labelling.

Depends on: S7.1.

Acceptance criteria:

- Agreement and disagreement counts are computable.
- Each disagreement has a reason, not only a changed label.

## S7.4 Prioritize feature and workflow feedback — P0

- [ ] Classify must-have, should-have, later and reject.
- [ ] Score trust impact, review-time impact, build cost and scope risk.
- [ ] Convert accepted items into task IDs.

Depends on: S7.2, S7.3.

Acceptance criteria:

- Feature novelty alone cannot make an item must-have.
- Scope expansion that does not improve the core loop is deferred.

## S7.5 Publish `DOMAIN_REVIEW_01.md` — P0

- [ ] Document methodology and sample size.
- [ ] Document findings and disagreements.
- [ ] Document accepted/deferred/rejected changes.
- [ ] Document privacy constraints.

Depends on: S7.2–S7.4.

Acceptance criteria:

- Claims are proportional to one practitioner’s review.
- The document does not imply formal certification.

## S7.6 Build practitioner golden suite — P0

- [ ] Convert accepted labelled cases into sanitized synthetic fixtures.
- [ ] Add expected proof, exception and action labels.
- [ ] Keep a different holdout set for the 90% review.

Depends on: S7.3, S7.5.

Acceptance criteria:

- Golden fixtures contain no client-identifying content.
- Runtime code cannot access their labels.

## S7.7 Incorporate domain-rule changes — P0

- [ ] Update policy pack.
- [ ] Update exception taxonomy.
- [ ] Update validation or matching rules.
- [ ] Add regression tests before changing behavior.
- [ ] Re-run all seeds and publish before/after metrics.

Depends on: S7.4, S7.6.

Acceptance criteria:

- No accepted rule exists only as prose.
- Any coverage/precision trade-off is documented.

## S7.8 Incorporate evidence-UX changes — P0

- [ ] Reorder evidence based on observed workflow.
- [ ] Add missing controller-relevant fields.
- [ ] Remove or defer distracting information.
- [ ] Re-test five cases without coaching.

Depends on: S7.2, S7.4.

Acceptance criteria:

- Changes improve task completion, not only appearance.
- Verified facts and hypotheses remain visibly separated.

### Segment 7 exit gate — M5 (75%)

- [ ] Structured practitioner feedback is documented.
- [ ] Accepted finance logic is encoded in tests and policies.
- [ ] A holdout practitioner set remains unused.
- [ ] Updated benchmark has no hidden regression.

---

# Segment 8 — Bounded AI exception investigator (75–82%)

## S8.1 Define investigator schemas — P0

- [ ] Define hypothesis, evidence IDs, confidence, action type and approval requirement.
- [ ] Define optional journal and clarification structures.
- [ ] Define refusal/fallback output.

Depends on: S4.10, M5.

Acceptance criteria:

- Free-form text cannot directly drive workflow state.
- Schema validation rejects unknown evidence and action types.

## S8.2 Implement investigator tool boundary — P0

- [ ] Implement read-only case, evidence, proof, policy and candidate tools.
- [ ] Implement attach-explanation and queue-proposal outputs.
- [ ] Exclude posting, source editing and auto-clear tools.

Depends on: S8.1.

Acceptance criteria:

- Model credentials grant no filesystem, network or financial mutation authority.
- Tool calls are scoped to the active run/case.

## S8.3 Implement structured model call — P0

- [ ] Build minimum-evidence prompt context.
- [ ] Delimit uploaded text as untrusted data.
- [ ] Validate structured response.
- [ ] Record model and prompt versions, latency and failure state.

Depends on: S8.1, S8.2.

Acceptance criteria:

- Invalid response cannot enter the review queue as valid advice.
- Explanation cites only supplied evidence IDs.

## S8.4 Implement deterministic post-validation — P0

- [ ] Recalculate all mentioned amounts.
- [ ] Validate evidence ownership.
- [ ] Validate debit/credit balance for proposed journals.
- [ ] Downgrade unsupported certainty language/state.

Depends on: S8.3.

Acceptance criteria:

- Model arithmetic is never authoritative.
- Unsupported outputs become fallback/review errors, not silent decisions.

## S8.5 Implement model-unavailable fallback — P0

- [ ] Generate rule-based explanation template.
- [ ] Generate deterministic next-action category.
- [ ] Mark run/case as model-fallback without blocking reconciliation.

Depends on: S8.1.

Acceptance criteria:

- With credentials absent or timeout forced, the core demo remains usable.
- Fallback output does not pretend to be model-generated.

## S8.6 Add agent explanation to workbench — P0

- [ ] Show hypothesis separately from verified facts.
- [ ] Link every cited evidence ID to its row.
- [ ] Show confidence as advisory, not proof.
- [ ] Allow reviewer rejection and notes.

Depends on: S6.5, S8.3–S8.5.

Acceptance criteria:

- Reviewers can inspect evidence without reading the narrative.
- Agent explanation never overwrites deterministic reason codes.

## S8.7 Add grounded unresolved-case Q&A — P1

- [ ] Limit questions to a selected completed run.
- [ ] Answer only from stored evidence, checks and reviews.
- [ ] Link cited cases/rows.
- [ ] Refuse requests requiring absent source data.

Depends on: S8.6.

Acceptance criteria:

- Q&A is secondary to the run and case interfaces.
- Unsupported answers abstain clearly.

### Segment 8 exit gate

- [ ] Structured investigator handles supported exception categories.
- [ ] Invalid or unavailable model output safely falls back.
- [ ] AI cannot change proof level or auto-clear status.

---

# Segment 9 — Review, action and re-verification loop (82–88%)

## S9.1 Define proposed-action types — P0

- [ ] Journal proposal.
- [ ] Clarification request.
- [ ] Mapping correction.
- [ ] Wait for expected timing event.
- [ ] No action/accepted difference.

Depends on: S7.7, S8.1.

Acceptance criteria:

- Every action type has required evidence and approval policy.
- “Unknown” cannot silently become a journal action.

## S9.2 Implement journal proposal engine — P0

- [ ] Generate lines from policy and deterministic variance.
- [ ] Require account, direction, amount, currency and reference.
- [ ] Verify total debits equal total credits.
- [ ] Link every line to case evidence.

Depends on: S9.1.

Acceptance criteria:

- The model may draft rationale but not authoritative line amounts.
- Unbalanced proposals are impossible to approve.

## S9.3 Build action review UI — P0

- [ ] Preview before approval.
- [ ] Approve, reject or edit allowed fields.
- [ ] Require reviewer identity/name in demo form.
- [ ] Show effect scope and idempotency key.

Depends on: S9.1, S9.2, S6.6.

Acceptance criteria:

- No action-like export occurs before explicit approval.
- Original proposal and edited version remain in audit history.

## S9.4 Implement journal CSV export — P0

- [ ] Export approved balanced journal lines.
- [ ] Include case, evidence and policy references.
- [ ] Produce checksum and action receipt.

Depends on: S9.3.

Acceptance criteria:

- Export totals balance.
- Repeated export with same idempotency key is recognized.

## S9.5 Implement corrected-data import and affected re-run — P0

- [ ] Import a corrected mock ERP file or approved mock entry.
- [ ] Create a new source/run version.
- [ ] Re-run only affected match groups when safe.
- [ ] Preserve before/after decisions.

Depends on: S9.3, S9.4.

Acceptance criteria:

- A demo exception can move to resolved after valid correction.
- Re-running does not erase original evidence or review history.

## S9.6 Build clarification-request export — P1

- [ ] Draft evidence-backed question.
- [ ] Include missing/contradictory fields without unnecessary data.
- [ ] Export as text/Markdown, not real email delivery.

Depends on: S9.1, S8.6.

Acceptance criteria:

- Draft does not invent an explanation from the company.
- Company input requirement remains open until new evidence arrives.

### Segment 9 exit gate — M6 (88%)

- [ ] One correction completes the entire closed loop.
- [ ] One case is intentionally left unresolved.
- [ ] All actions require approval and produce audit receipts.

---

# Segment 10 — Failure recovery, security and product polish (88–95%)

## S10.1 Test malformed and partial input recovery — P0

- [ ] Corrupt CSV encoding/rows.
- [ ] Remove required columns.
- [ ] Upload incompatible date ranges/currency.
- [ ] Verify user can correct and retry without losing previous attempt.

Depends on: M6.

Acceptance criteria:

- Errors are actionable and no partial successful state is claimed.

## S10.2 Test duplicate and idempotency behavior — P0

- [ ] Duplicate file upload.
- [ ] Duplicate source records.
- [ ] Repeated review action.
- [ ] Repeated journal export/import.

Depends on: M6.

Acceptance criteria:

- No duplicated financial effect occurs.
- Duplicate evidence is still visible and classified.

## S10.3 Test AI failure and hostile text — P0

- [ ] Timeout and malformed output.
- [ ] Missing credentials.
- [ ] Prompt-like bank narration.
- [ ] Invented evidence IDs and amounts.

Depends on: Segment 8.

Acceptance criteria:

- Deterministic workflow continues.
- Hostile text is treated as data.

## S10.4 Improve accessibility and financial presentation — P1

- [ ] Keyboard-accessible review controls.
- [ ] Status labels/icons in addition to color.
- [ ] Exact locale-aware rupee and paise formatting.
- [ ] Responsive evidence layout.
- [ ] Accessible validation summaries.

Depends on: S6.7, M6.

Acceptance criteria:

- Core demo is usable at common laptop widths.
- No amount is rounded in a decision-critical view.

## S10.5 Improve performance and observability — P1

- [ ] Measure pipeline stage latency.
- [ ] Add structured run/case logs without sensitive raw values.
- [ ] Profile default and larger benchmark batches.
- [ ] Prevent accidental N-squared candidate explosions through blocking limits.

Depends on: S5.3, M6.

Acceptance criteria:

- Benchmark reports p50/p95 runtime.
- Slow stages and failed rules can be diagnosed by run ID.

## S10.6 Conduct holdout practitioner review — P0

- [ ] Use cases not shown at the 65% review.
- [ ] Measure agreement by proof and exception category.
- [ ] Record false-clears, correct abstentions and review time.
- [ ] Capture final critical fixes only.

Depends on: S7.6, S10.1–S10.3.

Acceptance criteria:

- Methodology and sample size are documented.
- Results are reported honestly and do not imply certification.

## S10.7 Apply final critical domain fixes — P0

- [ ] Add failing regression tests.
- [ ] Update rules/policies.
- [ ] Re-run all benchmark suites.
- [ ] Document any remaining known limitation.

Depends on: S10.6.

Acceptance criteria:

- No known critical false-clear remains.
- Non-critical feature requests are deferred rather than destabilizing the build.

## S10.8 Build and test the production image — P0

- [x] Add a multi-stage build that compiles React and packages the FastAPI runtime.
- [x] Serve compiled UI and `/api/*` from the same origin.
- [x] Run as a non-root container user.
- [x] Add `.dockerignore` exclusions for secrets, caches, local databases and benchmark truth outputs.
- [x] Add `judge-local` Compose profile with a named writable volume.
- [x] Implement `/health/live`, `/health/ready` and `/api/meta` checks.
- [x] Implement the external API smoke-test skeleton and `make smoke`; extend its assertions as product endpoints arrive.
- [x] Implement `make judge`.

Depends on: S1.6, S6.1, M6.

Acceptance criteria:

- A clean container build succeeds without local frontend/backend artifacts.
- Container startup requires no model key.
- The browser UI and API work on one documented port.
- `make smoke` verifies a non-empty run, one proved case, one exception, evidence links and artifact export.
- Restart behavior is documented for both ephemeral and named-volume data.

### Segment 10 exit gate — M7 (95%)

- [ ] Failure behavior is visible and recoverable.
- [ ] Holdout practitioner results are documented.
- [ ] Known limitations and unresolved cases are explicit.
- [ ] The production image passes the deployed smoke test locally.

---

# Segment 11 — Judge deployment and submission package (95–100%)

## S11.1 Finish one-command developer experience — P0

- [ ] Implement `make demo`.
- [ ] Implement final `make verify`.
- [ ] Add `.env.example`, prerequisites and troubleshooting.
- [ ] Verify native setup from a fresh clone/environment.
- [ ] Verify `docker compose up --build` from a clean Docker cache where practical.

Depends on: M7, S10.8.

Acceptance criteria:

- A reviewer can start the demo without hidden terminal repair steps.
- Missing model credentials activate documented fallback.
- Commands fail loudly rather than displaying stale generated results.

## S11.2 Add hosted-demo reset and safety behavior — P0

- [x] Add a visible synthetic-data-only notice.
- [ ] Restrict file type and upload size.
- [ ] Store uploads under generated IDs rather than supplied paths.
- [ ] Add known-seed demo reset or automatic startup seed.
- [ ] Define and document retention/purge behavior.
- [ ] Disable debug endpoints and verbose error leakage in hosted mode.

Depends on: S1.6, S10.8.

Acceptance criteria:

- A judge can always restore the hosted app to a known working batch.
- The UI does not invite real confidential data.
- Reset cannot escape the configured demo data directory.

## S11.3 Deploy the hosted demo — P0

- [ ] Select a container host supporting the required port and writable-data strategy.
- [ ] Configure server-side environment values without committing secrets.
- [ ] Deploy the exact production image used by `make judge`.
- [ ] Record the deployed build commit through `/api/meta`.
- [ ] Configure a stable judging URL and HTTPS.
- [ ] Document whether storage is ephemeral or persistent.

Depends on: S11.1, S11.2.

Acceptance criteria:

- Hosted liveness and readiness pass.
- A fresh browser session can complete the primary demo loop.
- The model key, if present, never reaches browser assets or API responses.
- Restart/reset behavior matches documentation.

## S11.4 Run deployment smoke and browser-path tests — P0

- [ ] Run `make smoke` against judge-local.
- [ ] Run `make smoke` against the hosted URL.
- [ ] Verify model-optional fallback against judge-local.
- [ ] Test sample upload, run completion, case evidence and artifact export.
- [ ] Perform one browser-level principal-path test or documented manual checklist.
- [ ] Save smoke results with build commit and timestamp.

Depends on: S11.3.

Acceptance criteria:

- Smoke test runs from outside the application process.
- Hosted and local results agree on deterministic cases.
- A deployment that serves only the landing page cannot pass.

## S11.5 Write `DEPLOYMENT.md` — P0

- [ ] Document hosted URL and demo reset.
- [x] Document container and native paths.
- [x] Document runtime profiles and environment variables.
- [x] Document health endpoints and smoke command.
- [x] Document persistence, model fallback and resource assumptions.
- [x] Document demo-only security limitations.

Depends on: S11.3, S11.4.

Acceptance criteria:

- A judge can choose a path without contacting the author.
- No secret value appears in documentation.

## S11.6 Write the README — P0

- [x] Problem and one-sentence solution.
- [ ] Hosted demo and local judge command above the fold.
- [ ] Demo flow and screenshots/GIF if useful.
- [ ] Architecture diagram.
- [x] Setup and foundation commands; extend with demo/benchmark commands when implemented.
- [ ] Dataset and benchmark methodology.
- [ ] Measured results and incorrect-case links.
- [ ] AI-versus-deterministic decision boundaries.
- [ ] Failure recovery and known limitations.
- [ ] Practitioner review methodology.
- [ ] Adjacent product directions and expansion path.

Depends on: S11.1–S11.5.

Acceptance criteria:

- Every metric is reproducible through a command.
- No planned feature is described as already implemented.
- Judge execution requires no searching through the document.

## S11.7 Produce example artifacts — P0

- [ ] Close report.
- [ ] Exception pack.
- [ ] Audit log.
- [ ] Journal proposal/export.
- [ ] Benchmark report.
- [ ] Practitioner review summary.
- [ ] Deployment smoke report.

Depends on: M7, S11.4.

Acceptance criteria:

- Artifacts come from an actual fresh run.
- Each can be traced to the documented dataset seed, build commit and versions.

## S11.8 Rehearse and record five-minute video — P0

- [ ] Open the hosted URL rather than a private development server.
- [ ] Explain the problem and product promise.
- [ ] Run a fresh batch.
- [ ] Show operational and benchmark results.
- [ ] Show proved match evidence.
- [ ] Show an unresolved exception and AI hypothesis.
- [ ] Approve a correction and re-run.
- [ ] Demonstrate one failure and recovery.
- [ ] Close with architecture, AI boundaries and expansion path.

Depends on: S11.3–S11.7.

Acceptance criteria:

- Video is at or below five minutes.
- No result shown requires a hidden manual edit.
- At least one honest unresolved exception remains visible.
- The deployed build shown matches `/api/meta` and the documented commit.

## S11.9 Perform final trust review — P0

- [ ] Search repository and built frontend assets for secrets and real data.
- [ ] Verify all tests and benchmark thresholds.
- [ ] Verify local and hosted links, commands and screenshots.
- [ ] Verify clean status or document intended generated artifacts.
- [ ] Verify claims match measured results.
- [ ] Re-run the hosted smoke test immediately before submission.

Depends on: S11.8.

Acceptance criteria:

- `make verify` passes.
- Hosted smoke passes.
- No unsupported accuracy, security, product or practitioner claim remains.

### Segment 11 exit gate — M8 (100%)

- [ ] Hosted demo, local container, repository, architecture, five-minute video and measured results are submission-ready.
- [ ] A reviewer can reproduce the central claim without contacting the author.

---

# Segment 12 — Post-hackathon T-shaped expansion (P2)

These tasks do not block submission.

## S12.1 Saved organization mapping profiles

- [ ] Version mapping profiles by entity and source.
- [ ] Add change preview and backward compatibility.
- [ ] Add mapping confidence and approval history.

## S12.2 Additional source adapters

- [ ] Add a second gateway fixture/adapter.
- [ ] Add bank-specific layouts.
- [ ] Add ERP-specific journal export packs.
- [ ] Prove adapter conformance with shared contract tests.

## S12.3 Multi-entity and multi-currency policies

- [ ] Add entity isolation.
- [ ] Add currency-specific minor units.
- [ ] Add explicit FX source and revaluation policy.
- [ ] Prevent cross-entity/currency matching.

## S12.4 Production connector foundation

- [ ] Read-only connector authentication.
- [ ] Incremental ingestion and checkpoints.
- [ ] Tenant-scoped secrets and audit.
- [ ] Rate-limit and retry behavior.

## S12.5 Controlled ERP write-back

- [ ] ERP staging adapter.
- [ ] Dry-run and approval policy.
- [ ] Idempotency and action receipts.
- [ ] Reversal/compensating action path.
- [ ] Pilot-specific security review.

## S12.6 New workflow packs

- [ ] Create a workflow-pack contract for required event types, proof rules, exception types, actions and metrics.
- [ ] Require a synthetic generator and evaluator for every workflow pack.
- [ ] Keep workflow-specific rules outside the settlement kernel.

## S12.7 Fee and GST leakage auditor

- [ ] Add versioned commercial-rate-card input.
- [ ] Compare expected fee/tax with gateway deductions and ERP postings.
- [ ] Quantify recoverable leakage separately from timing differences.
- [ ] Draft a claim pack or balanced posting proposal.

## S12.8 Refund and chargeback lifecycle controller

- [ ] Link reversal to original payment.
- [ ] Track gateway, settlement, customer-ledger and ERP effects.
- [ ] Classify pending, stuck, duplicated and incorrectly posted reversals.
- [ ] Measure unresolved amount and lifecycle age.

## S12.9 Marketplace split-settlement verifier

- [ ] Model customer payment, seller transfer, platform fee and linked-account settlement.
- [ ] Add one-to-many split invariants and seller-level control totals.
- [ ] Detect missing, duplicated and incorrectly allocated transfers.
- [ ] Produce seller/platform exception packs.

## S12.10 Vendor statement/AP reconciliation

- [ ] Add vendor statement and AP-subledger adapters.
- [ ] Match invoices, credit notes and payments.
- [ ] Detect missing invoices, unapplied credits and duplicate payments.
- [ ] Generate a vendor clarification pack.

## S12.11 ERP migration proof pack

- [ ] Compare source and target trial-balance control totals.
- [ ] Verify opening balances and journal balance.
- [ ] Detect missing or remapped masters.
- [ ] Produce migration exception and sign-off packs.

## S12.12 Intercompany reconciliation controller

- [ ] Model reciprocal entity entries and policies.
- [ ] Match invoice, settlement and timing differences.
- [ ] Add explicit currency/FX evidence requirements.
- [ ] Generate bilateral exception actions.

## S12.13 Policy drift detector

- [ ] Compare new verified runs with approved fee, timing and account policies.
- [ ] Propose policy changes without activating them.
- [ ] Run old and proposed policies against historical golden cases.
- [ ] Require approval and versioned rollout.

## S12.14 Verified cash position and forecast

- [ ] Derive current cash only from reconciled balances and explicitly pending items.
- [ ] Add approved payables, payroll and scheduled cash movements.
- [ ] Forecast with scenario ranges and source lineage.
- [ ] Keep forecast uncertainty distinct from reconciliation proof.

Acceptance rule for all post-hackathon work:

> A new source or workflow must reuse the canonical event, proof, evidence, review, audit and evaluation contracts. If it cannot, write an ADR explaining why before changing the kernel.

---

# Scope-cut order if time runs short

Cut or defer in this order:

1. Post-hackathon Segment 12
2. Natural-language Q&A
3. Advanced animations and visual polish
4. Additional deployment profiles beyond the required judge-local and hosted-demo paths
5. Property-based tests beyond the critical money invariants
6. Clarification-request export
7. Support for alternate layouts beyond the contract demonstration

Do not cut:

- Ground-truth isolation
- Deterministic proof checks
- Strict risk gate
- False-clear reporting
- Evidence workbench
- Practitioner review at 65%
- Model fallback
- One approve/correct/re-run path
- Failure recovery demonstration
- Honest exception list
- Judge-local production image and deployed smoke test
