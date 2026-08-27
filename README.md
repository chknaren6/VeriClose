# VeriClose

**Evidence-first settlement-to-ERP reconciliation.**

VeriClose is being built for Razorpay Hackathon Track 04. It will process complete batches of gateway, bank and ERP records; automatically clear only provable matches; expose honest exceptions; and measure performance against hidden synthetic ground truth.

The current implementation includes the deployable M0 walking skeleton plus the Segment 2
finance foundation: immutable canonical types, source contracts, deterministic synthetic
gateway/bank/ERP batches, hidden ground truth and controlled exception scenarios. Upload,
normalization and reconciliation are not implemented yet.

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

## Judge-local container

Docker Compose is optional. The baseline command uses plain Docker:

```bash
make image
make judge
```

Then open <http://localhost:8000>. The deterministic fallback works without an AI model key.

If Docker Compose is available:

```bash
docker compose up --build
```

## Current architecture

```text
React/Vite shell
    → FastAPI routes
    → application composition root
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
