"""Immutable source-file storage port."""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from core.vericlose.ingestion.contracts import SourceDocument


@dataclass(frozen=True, slots=True)
class StoredFile:
    run_id: str
    file_id: str
    relative_path: str
    sha256: str
    size_bytes: int


@runtime_checkable
class FileStore(Protocol):
    def put(self, run_id: str, document: SourceDocument) -> StoredFile:
        """Store original bytes once without overwriting an existing object."""
        ...

    def get(self, stored_file: StoredFile) -> bytes:
        """Return the exact original bytes after verifying their hash."""
        ...

    def hash(self, stored_file: StoredFile) -> str:
        """Recalculate and return the current content hash."""
        ...
