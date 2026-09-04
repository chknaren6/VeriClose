"""Port for approved, local-only action artifacts."""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from core.vericlose.domain.actions import ProposedAction


@dataclass(frozen=True, slots=True)
class ExportedArtifact:
    relative_path: str
    media_type: str
    sha256: str
    size_bytes: int


@runtime_checkable
class ActionExporter(Protocol):
    def export(self, run_id: str, action: ProposedAction) -> ExportedArtifact: ...

    def read(self, artifact: ExportedArtifact) -> bytes: ...
