from pathlib import Path

import pytest

from core.vericlose.adapters.gateway import GatewayAdapter
from core.vericlose.ingestion.contracts import SourceDocument, ValidationStage
from core.vericlose.ingestion.mappings import MappingCatalog

PROFILE = MappingCatalog.from_directory(Path("config/mappings")).get("gateway_standard@1.0.0")
ADAPTER = GatewayAdapter((PROFILE,))


@pytest.mark.parametrize(
    ("content", "expected_code"),
    [
        (b"", "EMPTY_FILE"),
        (b"id,amount\n1\n", "CSV_COLUMN_COUNT_MISMATCH"),
        (b'id,amount\n1,"unterminated\n', "CSV_MALFORMED"),
    ],
)
def test_file_validation_returns_typed_diagnostics(content: bytes, expected_code: str) -> None:
    document = SourceDocument.from_bytes(
        file_id=f"bad-{expected_code.lower()}",
        original_name="gateway.csv",
        media_type="text/csv",
        content=content,
    )
    report = ADAPTER.validate(document, PROFILE)
    assert not report.can_normalize_valid_rows
    assert report.issues[0].stage is ValidationStage.FILE
    assert report.issues[0].code == expected_code
    assert report.issues[0].suggested_fix


def test_schema_validation_lists_unresolved_required_fields() -> None:
    document = SourceDocument.from_bytes(
        file_id="wrong-schema",
        original_name="gateway.csv",
        media_type="text/csv",
        content=b"id,amount\n1,100\n",
    )
    report = ADAPTER.validate(document, PROFILE)
    issue = report.issues[0]
    assert issue.stage is ValidationStage.SCHEMA
    assert issue.code == "REQUIRED_MAPPING_MISSING"
    assert "source_record_id" in issue.message
