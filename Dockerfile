FROM node:22-alpine AS web-build

WORKDIR /build
RUN npm install --global pnpm@11.19.0
COPY pnpm-workspace.yaml pnpm-lock.yaml ./
COPY apps/web/package.json apps/web/package.json
RUN pnpm install --frozen-lockfile
COPY apps/web/ apps/web/
RUN pnpm --filter @vericlose/web build

FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS python-build

ENV UV_PROJECT_ENVIRONMENT=/opt/venv
WORKDIR /build
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

FROM python:3.11-slim AS runtime

ARG VERICLOSE_BUILD_COMMIT=unknown
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VERICLOSE_ENVIRONMENT=judge-local \
    VERICLOSE_HOST=0.0.0.0 \
    VERICLOSE_PORT=8000 \
    VERICLOSE_DATA_DIR=/app/data \
    VERICLOSE_DATABASE_PATH=/app/data/vericlose.duckdb \
    VERICLOSE_STATIC_DIR=/app/apps/api/app/static \
    VERICLOSE_POLICY_PATH=/app/config/policies/razorpay_inr_v1.yaml \
    VERICLOSE_DEMO_MODE=true \
    VERICLOSE_RULE_VERSION=segment4-v1 \
    VERICLOSE_POLICY_VERSION=razorpay_inr_v1@1.0.0 \
    VERICLOSE_BUILD_COMMIT=${VERICLOSE_BUILD_COMMIT}

WORKDIR /app

RUN groupadd --system vericlose && useradd --system --gid vericlose --home-dir /app vericlose

COPY --from=python-build /opt/venv /opt/venv
COPY apps /app/apps
COPY core /app/core
COPY config /app/config
COPY scripts /app/scripts
COPY synthetic /app/synthetic
COPY --from=web-build /build/apps/web/dist /app/apps/api/app/static

RUN mkdir -p /app/data && chown -R vericlose:vericlose /app

USER vericlose
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/ready', timeout=2)"

CMD ["uvicorn", "apps.api.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
