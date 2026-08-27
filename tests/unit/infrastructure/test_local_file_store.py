from pathlib import Path

import pytest

from core.vericlose.infrastructure.local_file_store import LocalFileStore
from core.vericlose.ingestion.contracts import SourceDocument


def _document(file_id: str = "gateway") -> SourceDocument:
    return SourceDocument.from_bytes(
        file_id=file_id,
        original_name="gateway.csv",
        media_type="text/csv",
        content=b"id,amount\n1,100\n",
    )


def test_file_store_writes_once_and_verifies_hash(tmp_path: Path) -> None:
    store = LocalFileStore(tmp_path)
    stored = store.put("run-1", _document())
    repeated = store.put("run-1", _document())

    assert repeated == stored
    assert store.get(stored) == b"id,amount\n1,100\n"
    assert store.hash(stored) == _document().sha256
    assert (tmp_path / stored.relative_path).is_file()


@pytest.mark.parametrize("unsafe", ["../run", "run/child", "/absolute", ".."])
def test_file_store_rejects_unsafe_run_or_file_components(
    tmp_path: Path,
    unsafe: str,
) -> None:
    store = LocalFileStore(tmp_path)
    with pytest.raises(ValueError, match="unsafe|traversal"):
        store.put(unsafe, _document())
    with pytest.raises(ValueError, match="unsafe|traversal"):
        store.put("run-safe", _document(unsafe))
