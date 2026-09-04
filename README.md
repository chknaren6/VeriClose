# VeriClose

**Evidence-first settlement-to-ERP reconciliation.**

VeriClose processes complete gateway, bank and ERP batches; auto-clears only policy-proved
matches; routes the rest with evidence; and supports an approval-gated correction and re-run.
It is synthetic-data-only and no model credential is required.

The executable controller now includes bounded AI-style investigation with deterministic fallback,
grounded case Q&A, journal/clarification action exports, corrected mock-ERP imports, immutable
re-runs, artifact packs, demo reset, and a production container smoke path. Practitioner review,
hosted deployment and video recording remain explicit external gates.

## Fastest judge path

```bash
make image
make smoke-container
make judge
```

Open <http://localhost:8000>, select **Restore demo**, inspect a `MISSING_ERP_POSTING` case,
approve its balanced journal, export it, apply the mock correction and observe the new immutable
run. A separate `MISSING_BANK_RECEIPT` case remains unresolved by design.

## Start locally

Prerequisites:

- Python 3.11
- `uv`
- Node.js 22+
- `pnpm`
- GNU Make

Install dependencies:

```bash
make setup
```

Start the API and Vite development servers:

```bash
make dev
```

Open:

- Web: <http://localhost:5173>
- API docs: <http://localhost:8000/docs>
- Readiness: <http://localhost:8000/health/ready>

## Run checks

```bash
make verify
```

This runs Python linting, backend tests, frontend type checking and the production frontend build.

## Product loop and safety boundary

```text
gateway + bank + ERP
  → validate and preserve lineage
  → deterministic proof / abstention
  → evidence workbench + optional bounded advisory
  → human approval
  → checksummed export or clarification
  → corrected source version + re-run
```

- Deterministic code owns money, matching, proof level, journal balance and auto-clear.
- Model output is advisory only and is schema-validated against supplied evidence.
- Every export requires explicit human approval and has an idempotency receipt.
- Corrections make a new source/run version; they never overwrite old evidence or decisions.
- Operational dashboards do not show benchmark accuracy.

## Reproducible evidence

```bash
make benchmark
make examples
```

The latest five-seed benchmark evaluates 1,574 events and 125 cases: 100% auto-clear precision,
100% exception recall and zero false clears under this synthetic benchmark. Runtime varies by host;
run `make benchmark` to reproduce current p50/p95 timings.

Fresh artifact examples are in [docs/examples](/home/daredevil/Downloads/VeriClose/docs/examples):
close report, exception pack, audit log, approved journal, benchmark report, production smoke
result and browser-path checklist. Their hashes and seed/build provenance are in
[manifest.json](/home/daredevil/Downloads/VeriClose/docs/examples/manifest.json).

## Generate the synthetic company

```bash
make generate
```

This writes reproducible source files beneath `.data/synthetic/seed-42/`:

```text
inputs/gateway.csv
inputs/bank.csv
inputs/erp_gl.csv
manifest.json
private/ground_truth.json
```

Only evaluation code may read `private/ground_truth.json`.

## Import and validate the complete batch

After generating the files, run:

```bash
make import-batch RUN_ID=demo-seed-42-v1
```

The command prints a machine-readable summary containing the detected source/profile, rows seen,
normalized and quarantined row counts, validation codes, total canonical event count, and final
run state. Use a new `RUN_ID` for a re-import; previous source and canonical layers are immutable.

To import your own synthetic CSV/XLSX files directly:

```bash
uv run python -m scripts.import_batch \
  --gateway path/to/gateway.xlsx \
  --bank path/to/bank.csv \
  --erp path/to/erp_gl.xlsx
```

## Reconcile the complete batch

Generate, import, prove, risk-gate, persist, and export the exception queue:

```bash
make generate
make reconcile CLOSE_RUN_ID=demo-close-v1
```

The CLI reports operational verification throughput, proof-level counts, amount at risk, stage
timings, and the exception-file path. This is operational run output—not an accuracy benchmark.
Synthetic ground-truth accuracy and multi-seed safety gates are deliberately isolated in Segment 5.

## Judge-local container

Docker Compose is optional. The baseline command uses plain Docker:

```bash
make image
make judge
```

Then open <http://localhost:8000>. The deterministic fallback works without an AI model key.

The same image contains both the M1 import CLI and M2 close CLI. With generated inputs mounted
under `/app/data`, invoke `python -m scripts.import_batch` or `python -m scripts.reconcile`; no
development dependencies are needed.

For a mount-free proof entirely inside an ephemeral container volume:

```bash
docker run --rm -v /app/data vericlose:dev \
  python -m scripts.reconcile --generate-demo \
  --run-id judge-seed-42 --data-dir /app/data \
  --database /app/data/vericlose.duckdb \
  --exceptions-output /app/data/exceptions.json
```

If Docker Compose is available:

```bash
docker compose up --build
```

## Current architecture

```text
React/Vite review workspace
    → stable FastAPI workflow contracts
    → application import/run/query/review/action/correction services
    → adapter registry and versioned mappings
    → immutable file store + DuckDB
    → read-only candidate context + deterministic proof rules
    → policy-owned risk gate + evidence-backed exceptions
    → optional bounded investigator + append-only audit/artifacts
```

- `apps/api`: HTTP delivery and production static-asset serving
- `apps/web`: React user interface
- `core/vericlose`: domain, ports, rules and workflows
- `synthetic`: generated source data
- `evaluation`: hidden-truth comparison and benchmarks
- `config`: versioned source mappings and policy packs
- `tests`: unit, integration, contract, adversarial and deployment checks

Run `make benchmark` for the five-seed development safety gate or
`make benchmark-submission` for the ten-seed submission gate. Results are written to
`evaluation/reports/benchmark-latest.{json,md}` and include event/case accuracy, scenario
diagnostics, p50/p95 performance, exception recall and false-clear enforcement.

Prepare the blinded 25-case practitioner review with `make review-pack`. After the real session,
complete the forms under `docs/practitioner/review_01/` and run `make review-analyze`. Analysis
intentionally fails while labels or disagreement resolutions are incomplete.

Read [PROJECT_PLAN.md](PROJECT_PLAN.md) for the product design, [TASKS.md](TASKS.md) for
delivery gates, [BUILD_STEPS.md](BUILD_STEPS.md) for the implementation sequence, and
[DEPLOYMENT.md](DEPLOYMENT.md) for the judge runbook.

For the next release and expansion framework, read
[NEXT_BUILD_FRAMEWORK.md](/home/daredevil/Downloads/VeriClose/docs/NEXT_BUILD_FRAMEWORK.md).

The implementation report contains the historical architecture narrative; its current release
addendum records the post-M4 controller capabilities and remaining external gates.

For a plain-language description of the inputs, outputs and user journey, read
[docs/PRODUCT_WORKFLOW.md](docs/PRODUCT_WORKFLOW.md). Ideas that deliberately remain outside
the frozen MVP are tracked separately in
[docs/FUTURE_OPPORTUNITIES.md](docs/FUTURE_OPPORTUNITIES.md).

## Data safety

The hackathon build is for synthetic data only. Do not upload or commit real client data, credentials or proprietary ERP mappings. In hosted-demo mode, API docs are disabled, verbose workflow conflicts are sanitized, uploads are limited to CSV/XLSX and the configured per-file size, and **Restore demo** reads only the checked-in synthetic fixture.
