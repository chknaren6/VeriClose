# VeriClose demo and application guide

## The one-sentence story

VeriClose proves settlement money across **Gateway → Bank → ERP**, auto-clears only cases that
pass every deterministic control, and sends the rest through an evidence-backed human correction
loop without rewriting history.

## Why this is different

Keep this explanation to four points:

1. **It proves instead of predicts.** Deterministic rules own amounts, accounting invariants,
   uniqueness, proof levels, and auto-clear.
2. **It accounts for the full batch.** Every source row is either connected to a proved case,
   routed with evidence, or left open with an explicit reason.
3. **AI is bounded.** The model can explain an exception and recommend one next action, but it
   cannot change proof, edit a source, or post a journal.
4. **It closes the loop.** Approval, export, corrected import, and re-run create new history rather
   than replacing the old decision.

## Explain the architecture in 45 seconds

Use this sequence rather than listing technologies:

```text
CSV / XLSX sources
  → source adapters validate and normalize rows
  → canonical INR events preserve raw-row lineage
  → deterministic reconciliation kernel runs hard checks
  → risk gate assigns proof level and auto-clear eligibility
  → workbench shows evidence and human-controlled actions
  → optional model explains exceptions through a validated schema
  → approved correction creates a new version and re-runs proof
```

Then say:

> The important boundary is that the model sits beside the verification kernel, not inside it.
> FastAPI coordinates the workflow, DuckDB preserves the local audit state, and React presents the
> result. Dependencies point inward to pure finance types, so presentation and model availability
> cannot change accounting truth.

## Before recording or presenting

1. Start from the repository root with `make demo`.
2. Open <http://localhost:5173>.
3. Select **Restore seed-42** and wait for the run-complete notice.
4. Confirm the cockpit shows **315 source records, 25 cases, 15 proved, and 10 exceptions**.
5. Keep one `PROVED`, one `MISSING_ERP_POSTING`, and one `MISSING_BANK_RECEIPT` case easy to find.
6. Close notifications, hide bookmarks, use 100% browser zoom, and never show an API key.

If a clean reset is needed mid-demo, select **Restore seed-42** again. It creates a fresh immutable
run rather than editing the earlier run.

## Five-minute pitch script

### 0:00–0:35 — Problem and promise

Say:

> Finance teams do not need another AI matcher. They need proof that every gateway settlement
> reached the bank and was posted correctly in ERP. VeriClose either proves that movement,
> routes it with evidence, or states why it cannot decide.

Show the top-level **Gateway → Bank → ERP** product story.

### 0:35–1:10 — Whole-batch control

Select **Restore seed-42**. In the cockpit point to:

- 315 source records processed, not a hand-picked transaction;
- 25 accountable cases;
- 15 proved auto-clears and 10 honest exceptions;
- the five proof levels and amount at risk;
- the separate benchmark boundary.

Say: “Confidence never creates PROVED. Only hard checks, accounting invariants, and uniqueness do.”

### 1:10–2:00 — Proved case

Open a `PROVED` case. Point left-to-right through:

1. Gateway net settlement.
2. Bank receipt and UTR.
3. Balanced ERP journal.
4. Expected minus observed equals zero variance.
5. Every mandatory proof check passes.

Open one evidence row briefly to show original row lineage and the preserved raw values.

### 2:00–3:00 — Bounded investigation

Open a `MISSING_ERP_POSTING` or `CONTRADICTED` case and select **Investigate exception**.

Point out that deterministic facts appear first. Then show the separately styled advisory
hypothesis, linked evidence IDs, recommended action, confidence, and the banner:

> ADVISORY ONLY — This cannot change the proof level or auto-clear status.

Say: “The model explains and proposes. It cannot edit sources, clear a case, or post a journal.”

### 3:00–4:15 — Human-controlled correction loop

For a missing ERP posting:

1. Select **Propose controlled action**.
2. Show equal total debits and credits.
3. Select **Approve action**.
4. Select **Export approved journal**.
5. Show the checksum-backed artifact receipt.
6. Select **Import correction & re-run**.
7. Show the before/after status change, such as `SUPPORTED → PROVED`.

Say: “The correction creates a new run and decision. Original evidence and decisions remain
available, so the control is auditable.”

### 4:15–4:40 — Integrity demonstration

Open a missing-bank-receipt case. Explain that an ERP proposal cannot manufacture missing bank
evidence, so the case remains unresolved until outside evidence arrives.

Say: “Abstention is a feature. VeriClose would rather leave a case open than create a false clear.”

### 4:40–5:00 — Close

Show the close report, exception pack, and audit log links.

End with:

> VeriClose is an AI finance controller because it completes the operational loop—verify,
> investigate, approve, correct, and prove again—while deterministic code remains in charge of
> accounting truth.

## Optional manufacturing demo packs

Use [the manufacturing dataset guide](../demo/manufacturing/README.md) when a judge wants another
industry story. Aether emphasizes fee/GST controls, Nexus emphasizes settlement timing and missing
cash evidence, and Vanguard emphasizes refunds and ERP integrity failures.

## Enable the OpenAI investigation

The model is optional. VeriClose remains fully operational without it and displays
`deterministic fallback active`.

Create a local `.env` file from the safe template:

```bash
cp .env.example .env
chmod 600 .env
```

Add these values to `.env` using your own key; never paste the real key into source code, the
browser, a screenshot, the pitch video, or Git:

```dotenv
VERICLOSE_MODEL_API_KEY=your_key_here
VERICLOSE_MODEL_NAME=gpt-5-nano
VERICLOSE_MODEL_BASE_URL=https://api.openai.com/v1
VERICLOSE_MODEL_TIMEOUT_SECONDS=30
```

Restart with `make demo`. The footer should change to `AI helper: on`. Investigation
requests are sent server-side through the Responses API with a strict JSON schema,
minimal reasoning effort, and short evidence refs (E01…) so the small model copies
IDs exactly. The model has
no source-edit, auto-clear, journal-posting, filesystem, or messaging tools.

To demonstrate the model well:

1. Choose a non-proved case with several evidence rows.
2. Read the deterministic failure first; do not describe the model as finding that fact.
3. Select **Investigate** once and wait for the structured result.
4. Show the one-sentence hypothesis, short explanation, linked evidence IDs, confidence, and one
   recommended action.
5. Emphasize that accepting the explanation records a human review event but leaves proof intact.

If the panel reports a checks-based note instead of an AI suggestion, first confirm the footer says `AI helper: on`, then
restart after checking the four `VERICLOSE_MODEL_*` values. A timeout, unavailable model, invalid
schema, invented evidence ref, or invented amount deliberately falls back to a plain-language
checks note instead of breaking the
reconciliation run.

For the judge container, set the environment variable only for the command:

```bash
VERICLOSE_MODEL_API_KEY=your_key_here make judge
```

The repository ignores `.env`. OpenAI's official guidance likewise recommends keeping API keys
secret and loading them from server-side environment variables: [OpenAI API documentation](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.2).

## The 12 application answers

Fill the three personal placeholders yourself; do not guess them.

1. **Full name:** `[YOUR FULL LEGAL NAME]`
2. **College:** `[YOUR COLLEGE]`
3. **Graduation year:** `[YYYY]`
4. **In-person from September:** `[YES or NO — answer truthfully]`
5. **Availability:** `12 months`
6. **Resume:** `[UPLOAD PDF — use a simple filename such as Firstname_Lastname_Resume.pdf]`
7. **Track:** `Track 04 — AI Finance Controller`
8. **Project name:** `VeriClose`
9. **What it solves:**

   > VeriClose reconciles payment-gateway settlements to bank receipts and ERP journals. It
   > processes the full batch, auto-clears only deterministically proved cases, routes exceptions
   > with source-row evidence, and supports approval-gated correction, export, and re-verification.

10. **Public GitHub repository:** <https://github.com/chknaren6/VeriClose>
11. **Five-minute pitch video:** `[PASTE YOUR UNLISTED VIDEO URL]`
12. **What broke, and how you got out:**

   > The reconciliation kernel was correct, but the first product presentation looked like a
   > generic matching dashboard and the reset path loaded a tiny fixture instead of the full
   > judge-scale batch. The local demo also assumed a globally installed frontend package manager,
   > and model credentials could be absent. I kept accounting truth deterministic, rebuilt the UI
   > around Gateway → Bank → ERP proof, restored the reproducible 315-record seed, added a safe
   > launcher fallback, and made AI strictly optional with a deterministic investigation fallback.
   > The result is more trustworthy because every failure led to a control, not a hidden workaround.

## Video and submission checklist

- Repository is public and opens in an incognito window.
- README starts with the product promise and fastest judge path.
- No `.env`, key, local database, uploads, or hidden truth report is committed.
- Video is unlisted, plays without requesting access, and is at most five minutes.
- Browser shows “Synthetic data only.”
- Restore demo works immediately before recording.
- One proved case, one corrected case, and one honestly unresolved case are shown.
- The final application answer is specific and consistent with the repository history.
