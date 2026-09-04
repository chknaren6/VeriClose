"""Read-only source for a known synthetic demonstration batch."""

from typing import Protocol, runtime_checkable

from core.vericlose.ingestion.contracts import SourceDocument


@runtime_checkable
class DemoSourceProvider(Protocol):
    def load(self) -> tuple[SourceDocument, ...]:
        """Return the complete, immutable synthetic demo input set."""
        ...
