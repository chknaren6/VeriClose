from __future__ import annotations

import argparse
import time
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


def main() -> int:
    parser = argparse.ArgumentParser(description="Wait for a VeriClose readiness endpoint")
    parser.add_argument("--url", default="http://127.0.0.1:8000/health/ready")
    parser.add_argument("--timeout", type=float, default=20.0)
    args = parser.parse_args()
    deadline = time.monotonic() + args.timeout
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        try:
            with urlopen(args.url, timeout=1) as response:  # noqa: S310 - local/deployed health URL
                if response.status == 200:
                    return 0
        except (HTTPError, URLError, TimeoutError, ConnectionError) as error:
            last_error = error
        time.sleep(0.2)

    print(f"VeriClose did not become ready within {args.timeout:.1f}s: {last_error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
