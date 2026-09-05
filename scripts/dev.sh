#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"
export UV_CACHE_DIR="${UV_CACHE_DIR:-$project_root/.uv-cache}"

uv run uvicorn apps.api.app.main:app --host 0.0.0.0 --port 8000 --reload &
api_pid=$!

cleanup() {
  kill "$api_pid" 2>/dev/null || true
}

trap cleanup EXIT INT TERM

if command -v pnpm >/dev/null 2>&1; then
  pnpm --filter @vericlose/web dev --host 0.0.0.0
elif [[ -x "$project_root/apps/web/node_modules/.bin/vite" ]]; then
  cd "$project_root/apps/web"
  ./node_modules/.bin/vite --host 0.0.0.0
else
  echo "Frontend dependencies are missing. Run 'make setup' after installing pnpm." >&2
  exit 1
fi
