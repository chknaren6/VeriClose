from __future__ import annotations

import argparse
import json
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test a running VeriClose skeleton")
    parser.add_argument("--base-url", default="http://localhost:8000")
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

    print(
        json.dumps(
            {
                "status": "passed",
                "base_url": base_url,
                "environment": meta.get("environment"),
                "model_enabled": meta.get("model_enabled"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (HTTPError, URLError, TimeoutError, AssertionError, RuntimeError, TypeError) as error:
        print(f"Smoke test failed: {error}")
        raise SystemExit(1) from error
