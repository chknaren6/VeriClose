#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
port="${1:-8000}"
base_url="http://127.0.0.1:${port}"

cd "$project_root"
export UV_CACHE_DIR="${UV_CACHE_DIR:-$project_root/.uv-cache}"

uv run uvicorn apps.api.app.main:app --host 127.0.0.1 --port "$port" >/tmp/vericlose-smoke-api.log 2>&1 &
api_pid=$!

cleanup() {
  kill "$api_pid" 2>/dev/null || true
  wait "$api_pid" 2>/dev/null || true
}

trap cleanup EXIT INT TERM

uv run python scripts/wait_for_ready.py --url "$base_url/health/ready"
uv run python scripts/smoke.py --base-url "$base_url"
