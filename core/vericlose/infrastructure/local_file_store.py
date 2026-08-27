"""Run-scoped immutable file store constrained beneath one configured root."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from core.vericlose.ingestion.contracts import SourceDocument
from core.vericlose.ports.file_store import StoredFile

_SAFE_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class LocalFileStore:
    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def put(self, run_id: str, document: SourceDocument) -> StoredFile:
        safe_run = _validate_component(run_id, "run_id")
        safe_file = _validate_component(document.file_id, "file_id")
        extension = document.extension if document.extension in {".csv", ".xlsx"} else ".bin"
        relative = (
            Path("runs") / safe_run / "uploads" / (f"{safe_file}-{document.sha256[:12]}{extension}")
        )
        target = self._resolve(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            with target.open("xb") as handle:
                handle.write(document.content)
                handle.flush()
        except FileExistsError:
            if target.read_bytes() != document.content:
                raise ValueError(
                    "immutable stored-file path already contains different bytes"
                ) from None
        return StoredFile(
            run_id=run_id,
            file_id=document.file_id,
            relative_path=relative.as_posix(),
            sha256=document.sha256,
            size_bytes=len(document.content),
        )

    def get(self, stored_file: StoredFile) -> bytes:
        content = self._resolve(Path(stored_file.relative_path)).read_bytes()
        if hashlib.sha256(content).hexdigest() != stored_file.sha256:
            raise ValueError("stored source file failed its integrity check")
        return content

    def hash(self, stored_file: StoredFile) -> str:
        return hashlib.sha256(self.get(stored_file)).hexdigest()

    def _resolve(self, relative: Path) -> Path:
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("stored file path must be safe and relative")
        candidate = (self._root / relative).resolve()
        if not candidate.is_relative_to(self._root):
            raise ValueError("stored file path escapes configured data directory")
        return candidate


def _validate_component(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not _SAFE_COMPONENT.fullmatch(value):
        raise ValueError(f"{field_name} contains unsafe path characters")
    if value in {".", ".."}:
        raise ValueError(f"{field_name} cannot be a path traversal component")
    return value
