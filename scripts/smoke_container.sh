#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
port="${1:-8012}"
image="${2:-vericlose:dev}"
output="${3:-}"
container_name="vericlose-smoke-${port}"
base_url="http://127.0.0.1:${port}"

cd "$project_root"
export UV_CACHE_DIR="${UV_CACHE_DIR:-$project_root/.uv-cache}"

container_id="$(docker run --rm --detach --name "$container_name" -p "$port:8000" "$image")"

cleanup() {
  docker stop "$container_id" >/dev/null 2>&1 || true
}

trap cleanup EXIT INT TERM

if ! uv run python scripts/wait_for_ready.py --url "$base_url/health/ready" --timeout 30; then
  echo "Container logs:" >&2
  docker logs "$container_id" >&2 || true
  exit 1
fi
smoke_args=(--base-url "$base_url")
if [[ -n "$output" ]]; then
  smoke_args+=(--output "$output")
fi
uv run python scripts/smoke.py "${smoke_args[@]}"

served_title="$(python - "$base_url" <<'PY'
import sys
from urllib.request import urlopen

with urlopen(sys.argv[1], timeout=5) as response:
    html = response.read().decode("utf-8")
print("VeriClose" if "<title>VeriClose</title>" in html else "")
PY
)"

if [[ "$served_title" != "VeriClose" ]]; then
  echo "Production container did not serve the compiled VeriClose UI" >&2
  exit 1
fi

echo "Production UI served successfully by $image"
