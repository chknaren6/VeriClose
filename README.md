# VeriClose

**Evidence-first settlement-to-ERP reconciliation.**

VeriClose is being built for Razorpay Hackathon Track 04. It will process complete batches of gateway, bank and ERP records; automatically clear only provable matches; expose honest exceptions; and measure performance against hidden synthetic ground truth.

The current implementation includes the deployable shell and complete M1 ingestion pipeline:
immutable canonical types, deterministic synthetic gateway/bank/ERP batches, CSV/XLSX source
adapters, safe versioned mappings, staged validation, honest row quarantine, immutable source
storage, and transactional DuckDB persistence. Reconciliation deliberately starts in Segment 4.

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

## Judge-local container

Docker Compose is optional. The baseline command uses plain Docker:

```bash
make image
make judge
```

Then open <http://localhost:8000>. The deterministic fallback works without an AI model key.

The same image also contains the M1 import CLI. With generated inputs mounted under `/app/data`,
it can be invoked with `python -m scripts.import_batch`; no development dependencies are needed.

If Docker Compose is available:

```bash
docker compose up --build
```

## Current architecture

```text
React/Vite shell
    → FastAPI routes
    → application composition root/import service
    → adapter registry and versioned mappings
    → immutable file store + DuckDB
    → future deterministic verification kernel
```

- `apps/api`: HTTP delivery and production static-asset serving
- `apps/web`: React user interface
- `core/vericlose`: domain, ports, rules and workflows
- `synthetic`: generated source data
- `evaluation`: hidden-truth comparison and benchmarks
- `config`: versioned source mappings and policy packs
- `tests`: unit, integration, contract, adversarial and deployment checks

Read [PROJECT_PLAN.md](PROJECT_PLAN.md) for the product design, [TASKS.md](TASKS.md) for
delivery gates, [BUILD_STEPS.md](BUILD_STEPS.md) for the implementation sequence, and
[DEPLOYMENT.md](DEPLOYMENT.md) for the judge runbook.

For a plain-language description of the inputs, outputs and user journey, read
[docs/PRODUCT_WORKFLOW.md](docs/PRODUCT_WORKFLOW.md). Ideas that deliberately remain outside
the frozen MVP are tracked separately in
[docs/FUTURE_OPPORTUNITIES.md](docs/FUTURE_OPPORTUNITIES.md).

## Data safety

The hackathon build is for synthetic data only. Do not upload or commit real client data, credentials or proprietary ERP mappings.
