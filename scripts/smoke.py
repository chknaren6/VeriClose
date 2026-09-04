from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def fetch_json(url: str) -> dict[str, Any]:
    request = Request(url, headers={"Accept": "application/json"})
    with urlopen(request, timeout=10) as response:  # noqa: S310 - caller supplies judge URL
        if response.status != 200:
            raise RuntimeError(f"{url} returned HTTP {response.status}")
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise TypeError(f"{url} returned a non-object JSON payload")
    return payload


def request_json(url: str, *, method: str = "GET") -> dict[str, Any] | list[Any]:
    request = Request(
        url,
        data=b"{}" if method == "POST" else None,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        method=method,
    )
    with urlopen(request, timeout=30) as response:  # noqa: S310 - caller supplies judge URL
        if response.status != 200:
            raise RuntimeError(f"{url} returned HTTP {response.status}")
        return json.load(response)


def fetch_artifact(url: str) -> tuple[bytes, str | None]:
    request = Request(url, headers={"Accept": "*/*"})
    with urlopen(request, timeout=30) as response:  # noqa: S310 - caller supplies judge URL
        return response.read(), response.headers.get("X-VeriClose-SHA256")


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test a running VeriClose skeleton")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")

    live = fetch_json(f"{base_url}/health/live")
    ready = fetch_json(f"{base_url}/health/ready")
    meta = fetch_json(f"{base_url}/api/meta")

    if live.get("status") != "alive":
        raise AssertionError("Liveness response is not alive")
    if ready.get("status") != "ready":
        raise AssertionError("Readiness response is not ready")
    if meta.get("app") != "VeriClose":
        raise AssertionError("Metadata does not identify VeriClose")

    reset = request_json(f"{base_url}/api/v1/demo/reset", method="POST")
    if not isinstance(reset, dict) or reset.get("state") != "COMPLETED":
        raise AssertionError("Known synthetic demo did not complete")
    run_id = reset.get("run_id")
    cases = request_json(f"{base_url}/api/v1/runs/{run_id}/cases")
    if not isinstance(cases, list) or not cases:
        raise AssertionError("Smoke run has no cases")
    if not any(item.get("proof_level") == "PROVED" for item in cases):
        raise AssertionError("Smoke run has no proved case")
    exception = next((item for item in cases if item.get("proof_level") != "PROVED"), None)
    if exception is None:
        raise AssertionError("Smoke run has no honest exception")
    detail = request_json(f"{base_url}/api/v1/cases/{exception['case_id']}")
    if not isinstance(detail, dict) or not detail.get("evidence"):
        raise AssertionError("Exception evidence links are missing")
    artifact, checksum = fetch_artifact(
        f"{base_url}/api/v1/runs/{run_id}/artifacts/exception-pack"
    )
    if not artifact or checksum is None or len(checksum) != 64:
        raise AssertionError("Exception artifact or checksum is missing")

    result = {
        "status": "passed",
        "checked_at": datetime.now(UTC).isoformat(),
        "base_url": base_url,
        "environment": meta.get("environment"),
        "build_commit": meta.get("build_commit"),
        "model_enabled": meta.get("model_enabled"),
        "run_id": run_id,
        "case_count": len(cases),
        "exception_case_id": exception["case_id"],
        "artifact_sha256": checksum,
    }
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (HTTPError, URLError, TimeoutError, AssertionError, RuntimeError, TypeError) as error:
        print(f"Smoke test failed: {error}")
        raise SystemExit(1) from error
