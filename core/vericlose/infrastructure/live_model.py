"""Provider-isolated structured Responses API adapter with no financial tools."""

from __future__ import annotations

import json
from time import monotonic
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from core.vericlose.ports.model_gateway import (
    ModelRequest,
    ModelResponse,
    ModelUnavailableError,
)


class OpenAIModelGateway:
    def __init__(self, api_key: str, model: str, base_url: str, timeout_seconds: float) -> None:
        if not api_key:
            raise ValueError("api_key cannot be blank")
        self._api_key = api_key
        self._model = model
        self._url = f"{base_url.rstrip('/')}/responses"
        self._timeout_seconds = timeout_seconds

    def generate(self, request: ModelRequest) -> ModelResponse:
        # gpt-5-nano is a reasoning model: default (medium) effort spends ~2500
        # reasoning tokens before writing any output, so a small max_output_tokens
        # budget returns status=incomplete with no message. Minimal effort keeps
        # the advisory fast and leaves budget for the actual JSON answer.
        body = json.dumps(
            {
                "model": self._model,
                "instructions": request.instructions,
                "input": json.dumps(request.context, sort_keys=True, separators=(",", ":")),
                "text": {
                    "format": {
                        "type": "json_schema",
                        "name": "vericlose_exception_investigation",
                        "strict": True,
                        "schema": request.output_schema,
                    }
                },
                "store": False,
                "reasoning": {"effort": "minimal"},
                "max_output_tokens": 5000,
            },
            separators=(",", ":"),
        ).encode()
        http_request = Request(
            self._url,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
        )
        started = monotonic()
        try:
            with urlopen(http_request, timeout=self._timeout_seconds) as response:  # noqa: S310
                payload = json.load(response)
        except (HTTPError, URLError, TimeoutError, OSError) as error:
            raise ModelUnavailableError(
                f"structured model request failed: {type(error).__name__}"
            ) from error
        latency_ms = max(0, round((monotonic() - started) * 1000))
        status = payload.get("status")
        if status is not None and status != "completed":
            incomplete = payload.get("incomplete_details") or {}
            reason = incomplete.get("reason") if isinstance(incomplete, dict) else None
            raise ModelUnavailableError(
                f"model response was {status}"
                + (f" ({reason})" if reason else "")
                + ": no advisory text was returned"
            )
        try:
            texts: list[str] = []
            for item in payload.get("output", []):
                if not isinstance(item, dict) or item.get("type") != "message":
                    continue
                for part in item.get("content", []):
                    if isinstance(part, dict) and part.get("type") == "output_text":
                        text = part.get("text")
                        if isinstance(text, str) and text.strip():
                            texts.append(text)
            if not texts:
                raise StopIteration("no output_text part")
            output_text = "".join(texts)
            parsed = json.loads(output_text)
        except (KeyError, StopIteration, TypeError, json.JSONDecodeError) as error:
            raise ModelUnavailableError(
                "structured model response contained no valid output"
            ) from error
        if not isinstance(parsed, dict):
            raise ModelUnavailableError("structured model output must be an object")
        return ModelResponse(parsed, str(payload.get("model") or self._model), latency_ms)
