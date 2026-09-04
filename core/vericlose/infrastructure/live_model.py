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
                "max_output_tokens": 1200,
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
        try:
            output_text = next(
                part["text"]
                for item in payload["output"]
                if item.get("type") == "message"
                for part in item.get("content", [])
                if part.get("type") == "output_text"
            )
            parsed = json.loads(output_text)
        except (KeyError, StopIteration, TypeError, json.JSONDecodeError) as error:
            raise ModelUnavailableError(
                "structured model response contained no valid output"
            ) from error
        if not isinstance(parsed, dict):
            raise ModelUnavailableError("structured model output must be an object")
        return ModelResponse(parsed, str(payload.get("model") or self._model), latency_ms)
