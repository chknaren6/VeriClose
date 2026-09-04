"""Load the checked-in synthetic demo inputs without exposing arbitrary paths."""

from pathlib import Path

from core.vericlose.ingestion.contracts import SourceDocument


class LocalDemoSourceProvider:
    _FILES = (
        ("gateway", "gateway.csv"),
        ("bank", "bank.csv"),
        ("erp", "erp_gl.csv"),
    )

    def __init__(self, fixture_directory: Path) -> None:
        self._fixture_directory = fixture_directory.resolve()

    def load(self) -> tuple[SourceDocument, ...]:
        documents = []
        for file_id, filename in self._FILES:
            path = (self._fixture_directory / filename).resolve()
            if not path.is_relative_to(self._fixture_directory) or not path.is_file():
                raise FileNotFoundError(f"demo fixture is unavailable: {filename}")
            documents.append(
                SourceDocument.from_bytes(
                    file_id=file_id,
                    original_name=filename,
                    media_type="text/csv",
                    content=path.read_bytes(),
                )
            )
        return tuple(documents)
