"""Narrow model boundary for advisory exception investigation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


class ModelUnavailableError(RuntimeError):
    """Raised when the optional advisory provider cannot return a response."""


@dataclass(frozen=True, slots=True)
class ModelRequest:
    prompt_version: str
    instructions: str
    context: dict[str, Any]
    output_schema: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ModelResponse:
    payload: dict[str, Any]
    model_version: str
    latency_ms: int


@runtime_checkable
class ModelGateway(Protocol):
    def generate(self, request: ModelRequest) -> ModelResponse: ...
