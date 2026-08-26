#!/usr/bin/env bash
set -euo pipefail

uv run uvicorn apps.api.app.main:app --host 0.0.0.0 --port 8000 --reload &
api_pid=$!

cleanup() {
  kill "$api_pid" 2>/dev/null || true
}

trap cleanup EXIT INT TERM

pnpm --filter @vericlose/web dev --host 0.0.0.0
