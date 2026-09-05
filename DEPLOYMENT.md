# VeriClose Deployment Runbook

This runbook defines the reproducible, model-optional deployment path a judge can use.
The production image contains the complete local controller loop, including synthetic reset,
evidence review, approval-gated export, mock correction and re-run.

## Supported judge path

Prerequisites:

- Docker Engine with BuildKit support
- one available local port (default `8000`)
- approximately 1 GB of free disk space for build layers and dependencies

Build and verify the image:

```bash
make image
make smoke-container
```

Run it interactively:

```bash
make judge
```

Open:

- product: <http://localhost:8000>
- API documentation: <http://localhost:8000/docs>
- liveness: <http://localhost:8000/health/live>
- readiness: <http://localhost:8000/health/ready>
- build/runtime metadata: <http://localhost:8000/api/meta>

The application must start without an AI provider credential. In that case `/api/meta`
reports `model_enabled: false`, and all deterministic finance functionality must
remain available.

In the product, use **Restore demo** to start a new known seed-42 run. It contains one proved
case, one `MISSING_ERP_POSTING` correction path, and one independent `MISSING_BANK_RECEIPT` that
remains open after the correction. Reset never uses a caller-provided filesystem path.

## Docker Compose convenience path

If the Docker Compose plugin is installed:

```bash
docker compose up --build
```

The Compose service and `make judge` use the same Dockerfile and runtime command. Compose
adds a named volume for `/app/data`; the Make target binds local `.data/` there instead.

## Native development path

With Python 3.11, `uv`, Node.js 22+, `pnpm`, and Make installed:

```bash
make setup
make dev
```

This starts Vite on <http://localhost:5173> and FastAPI on
<http://localhost:8000>. The Vite development proxy forwards health and API requests
to FastAPI. Native mode is for development; the judge path above is the reproducible
release artifact.

## Configuration

All application settings use the `VERICLOSE_` prefix. Copy `.env.example` for local
development; never commit the populated `.env` file.

Important variables:

| Variable | Judge default | Purpose |
|---|---:|---|
| `VERICLOSE_ENVIRONMENT` | `judge-local` | Selects runtime behavior/profile. |
| `VERICLOSE_DATA_DIR` | `/app/data` | Writable immutable uploads and generated artifacts. |
| `VERICLOSE_DATABASE_PATH` | `/app/data/vericlose.duckdb` | DuckDB persistence path. |
| `VERICLOSE_POLICY_PATH` | `/app/config/policies/razorpay_inr_v1.yaml` | Validated policy pack. |
| `VERICLOSE_DEMO_FIXTURE_DIR` | `/app/demo/seed-42/inputs` | Checked-in synthetic reset source only. |
| `VERICLOSE_DEMO_MODE` | `true` | Allows only safe synthetic demo behavior. |
| `VERICLOSE_UPLOAD_MAX_BYTES` | `10485760` | Per-file upload ceiling. |
| `VERICLOSE_DETERMINISTIC_SEED` | `42` | Default reproducibility seed. |
| `VERICLOSE_RULE_VERSION` | `segment4-v1` | Deterministic rule-set version. |
| `VERICLOSE_POLICY_VERSION` | `razorpay_inr_v1@1.0.0` | Accounting policy version. |
| `VERICLOSE_MODEL_API_KEY` | unset | Optional investigation provider credential. |
| `VERICLOSE_MODEL_NAME` | `gpt-5-nano` | Optional bounded investigator model. |
| `VERICLOSE_MODEL_TIMEOUT_SECONDS` | `30` | Model request timeout before deterministic fallback. |
| `VERICLOSE_RETENTION_HOURS` | `24` | Hosted-demo operator retention policy window. |

Do not put secrets in the image, source tree, Compose file, frontend bundle, or demo data.

## Container contract

- The process listens on container port `8000`.
- FastAPI serves `/api/*`, health endpoints, docs, and compiled React assets on one origin.
- In `hosted-demo` mode, API docs/OpenAPI are disabled and workflow conflict messages do not expose
  raw internal error text.
- The process runs as a non-root user.
- `/app/data` is the only required writable application directory.
- Liveness means the process responds.
- Readiness means settings loaded and the configured data path is writable. Mapping profiles are
  validated when the application composition root starts; versioned DuckDB migrations are applied
  transactionally on the first persistence operation.
- SIGTERM/SIGINT must allow Uvicorn to shut down cleanly.

## External smoke check

For an already-running deployment:

```bash
BASE_URL=http://localhost:8000 make smoke
```

This starts a fresh known-seed run from outside the application process, asserts a proved case and
an honest exception, opens evidence through the API and downloads a checksummed exception pack.
`make smoke-container` additionally checks the production HTML shell and removes its short-lived
container. Save a result with:

```bash
make smoke-container SMOKE_OUTPUT=docs/examples/deployment-smoke-container.json
```

## Hosted demo profile

Use the same image with environment configuration changed:

```text
VERICLOSE_ENVIRONMENT=hosted-demo
VERICLOSE_DEMO_MODE=true
VERICLOSE_DATA_DIR=/app/data
VERICLOSE_DATABASE_PATH=/app/data/vericlose.duckdb
```

The current repository does not claim a hosted URL. Choose a host with HTTPS and either:

- **ephemeral demo storage:** reset after restart; this is the recommended judging profile; or
- **persistent volume:** retain synthetic run history temporarily, then purge the whole demo data
  volume at or before the documented `VERICLOSE_RETENTION_HOURS` window.

The application never purges accounting evidence inside a run. Retention is an operator-level,
whole-demo-data lifecycle decision for synthetic hosted sessions. Do not use this build for real
financial data.

## Release gate

Before handing a build to judges:

1. Run `make verify`.
2. Run `make image`.
3. Run `make smoke-container` with no model credential.
4. Start `make judge` and complete the documented demo flow in a private/incognito browser.
5. Confirm all inputs are synthetic and no `.env`, client files, or generated truth artifacts
   are present in the image or Git history.
6. Record the commit SHA and benchmark configuration shown in the demo.

## Current capability and limits

The image validates three sources, preserves immutable lineage, applies bounded deterministic
proof, exposes case evidence, provides bounded advisory fallback, requires approval before action
export, imports an approved mock journal as a new source version, and re-runs deterministically.
It does not perform live ERP posting, process real client data, or claim a practitioner review,
hosted deployment or certification that has not occurred.

Native end-to-end proof:

```bash
make generate
make reconcile CLOSE_RUN_ID=judge-seed-42-v1
```

Expected properties of the default seed-42 batch:

- 315 source rows become 315 traceable canonical events and 25 case decisions.
- The run reaches `COMPLETED` with 15 proved auto-clears and 10 honest exceptions.
- Every decision contains persisted proof checks and exact source-row evidence.
- Fuzzy support and ambiguous groups cannot auto-clear.
- A repeated upload in the same run is rejected by content hash; re-import uses a new run ID.

The generator and import CLI are also included in the production image, so the same proof can run
without development dependencies when input and data directories are mounted into the container.

To remove host bind-mount permissions from the proof entirely, run the synthetic generator and
close loop inside an anonymous writable container volume:

```bash
docker run --rm -v /app/data vericlose:dev \
  python -m scripts.reconcile --generate-demo \
  --run-id judge-seed-42 --data-dir /app/data \
  --database /app/data/vericlose.duckdb \
  --exceptions-output /app/data/exceptions.json
```
