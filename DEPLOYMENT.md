# VeriClose Deployment Runbook

This runbook defines the reproducible, model-optional deployment path a judge can use.
The same container will remain the delivery shape as reconciliation capability is added.

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
reports `model_enabled: false`, and all future deterministic finance functionality must
remain available.

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
| `VERICLOSE_DATA_DIR` | `/app/data` | Writable uploads, artifacts, and future local data. |
| `VERICLOSE_DATABASE_PATH` | `/app/data/vericlose.duckdb` | Future local database path. |
| `VERICLOSE_DEMO_MODE` | `true` | Allows only safe synthetic demo behavior. |
| `VERICLOSE_UPLOAD_MAX_BYTES` | `10485760` | Per-file upload ceiling. |
| `VERICLOSE_DETERMINISTIC_SEED` | `42` | Default reproducibility seed. |
| `VERICLOSE_POLICY_VERSION` | `razorpay_inr_v1` | Versioned accounting policy selection. |
| `VERICLOSE_MODEL_API_KEY` | unset | Optional investigation provider credential. |

Do not put secrets in the image, source tree, Compose file, frontend bundle, or demo data.

## Container contract

- The process listens on container port `8000`.
- FastAPI serves `/api/*`, health endpoints, docs, and compiled React assets on one origin.
- The process runs as a non-root user.
- `/app/data` is the only required writable application directory.
- Liveness means the process responds.
- Readiness means settings loaded and the configured data path is writable; later milestones
  will also check policy, mapping, storage schema, and production assets.
- SIGTERM/SIGINT must allow Uvicorn to shut down cleanly.

## External smoke check

For an already-running deployment:

```bash
BASE_URL=http://localhost:8000 make smoke
```

This checks readiness and metadata from outside the application process. `make
smoke-container` additionally builds a short-lived container, waits for readiness,
checks the production HTML shell, and then removes the container.

## Hosted demo profile

The future hosted demo will use the same image with environment configuration changed:

```text
VERICLOSE_ENVIRONMENT=hosted-demo
VERICLOSE_DEMO_MODE=true
VERICLOSE_DATA_DIR=/app/data
VERICLOSE_DATABASE_PATH=/app/data/vericlose.duckdb
```

The hosting platform must provide persistent writable storage if runs must survive a
restart. Without it, deployment is still valid for an ephemeral judge demo, but run data
will be lost when the container is replaced.

## Release gate

Before handing a build to judges:

1. Run `make verify`.
2. Run `make image`.
3. Run `make smoke-container` with no model credential.
4. Start `make judge` and complete the documented demo flow in a private/incognito browser.
5. Confirm all inputs are synthetic and no `.env`, client files, or generated truth artifacts
   are present in the image or Git history.
6. Record the commit SHA and benchmark configuration shown in the demo.

## Current M0 limitation

The current image is a verified walking skeleton. It does not yet ingest finance files or
claim reconciliation results. That capability is added inside the existing API, web app,
and image as subsequent task gates pass.
