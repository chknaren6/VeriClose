"""Unit tests for source-neutral S3.1 ingestion invariants."""

import hashlib
from datetime import UTC, datetime

import pytest

from core.vericlose.domain.enums import Direction, EventType, SourceType
from core.vericlose.domain.events import CanonicalEvent, RawField, RawRowRef
from core.vericlose.domain.money import Money
from core.vericlose.ingestion.contracts import (
    DetectionReason,
    DetectionResult,
    IssueSeverity,
    MappingProfileRef,
    NormalizationResult,
    RowDisposition,
    RowDispositionStatus,
    SourceDocument,
    SourceFormat,
    ValidationIssue,
    ValidationReport,
    ValidationStage,
)


def _document() -> SourceDocument:
    return SourceDocument.from_bytes(
        file_id="file-1",
        original_name="gateway.csv",
        media_type="text/csv",
        content=b"id,amount\npay-1,100\n",
    )


def _profile(version: str = "1.0.0") -> MappingProfileRef:
    return MappingProfileRef("gateway-standard", version, SourceType.GATEWAY)


def _issue(row_number: int = 2, code: str = "INVALID_AMOUNT") -> ValidationIssue:
    return ValidationIssue(
        stage=ValidationStage.SEMANTIC,
        severity=IssueSeverity.ERROR,
        code=code,
        message="Amount is invalid",
        file_id="file-1",
        table_name="payments",
        row_number=row_number,
        field_name="amount",
        supplied_value="bad",
        suggested_fix="Supply an integer amount in minor units",
        blocking=True,
    )


def _event(
    document: SourceDocument, mapping_version: str = "gateway-standard@1.0.0"
) -> CanonicalEvent:
    return CanonicalEvent(
        event_id="event-1",
        run_id="run-1",
        source_type=SourceType.GATEWAY,
        source_record_id="pay-1",
        legal_entity_id="merchant-1",
        event_type=EventType.PAYMENT,
        money=Money(100),
        direction=Direction.CREDIT,
        event_at=datetime(2026, 8, 1, tzinfo=UTC),
        value_date=None,
        external_reference=None,
        settlement_reference=None,
        payment_reference="pay-1",
        bank_utr=None,
        account_code=None,
        narration=None,
        lineage=RawRowRef(
            source_file_id=document.file_id,
            file_sha256=document.sha256,
            table_name="payments",
            row_number=2,
            raw_row_hash=hashlib.sha256(b"pay-1,100").hexdigest(),
        ),
        raw_fields=(RawField("amount", "100"),),
        mapping_profile_version=mapping_version,
    )


def test_source_document_verifies_content_hash() -> None:
    document = _document()
    assert document.extension == ".csv"

    with pytest.raises(ValueError, match="does not match"):
        SourceDocument(
            file_id="file-1",
            original_name="gateway.csv",
            media_type="text/csv",
            sha256="0" * 64,
            content=document.content,
        )


def test_positive_detection_requires_evidence() -> None:
    with pytest.raises(ValueError, match="must include reasons"):
        DetectionResult(
            adapter_id="gateway-csv",
            adapter_version="1.0.0",
            source_type=SourceType.GATEWAY,
            source_format=SourceFormat.CSV,
            confidence_bps=8_000,
            reasons=(),
            candidate_profiles=(_profile(),),
        )

    result = DetectionResult(
        adapter_id="gateway-csv",
        adapter_version="1.0.0",
        source_type=SourceType.GATEWAY,
        source_format=SourceFormat.CSV,
        confidence_bps=8_000,
        reasons=(DetectionReason("HEADER_MATCH", "Required headers were found", 8_000),),
        candidate_profiles=(_profile(),),
    )
    assert result.confidence_bps == 8_000


def test_mapping_profile_identity_includes_version() -> None:
    assert _profile("2.3.1").versioned_id == "gateway-standard@2.3.1"


def test_validation_report_distinguishes_row_and_file_blockers() -> None:
    row_report = ValidationReport(
        "adapter",
        "1.0.0",
        "file-1",
        _profile(),
        1,
        (_issue(),),
    )
    file_issue = ValidationIssue(
        stage=ValidationStage.SCHEMA,
        severity=IssueSeverity.ERROR,
        code="COLUMN_MISSING",
        message="Required column is missing",
        file_id="file-1",
        table_name="payments",
        row_number=None,
        field_name="amount",
        supplied_value=None,
        suggested_fix="Select the correct mapping",
        blocking=True,
    )
    file_report = ValidationReport(
        "adapter",
        "1.0.0",
        "file-1",
        _profile(),
        0,
        (file_issue,),
    )

    assert not row_report.is_valid
    assert row_report.can_normalize_valid_rows
    assert row_report.quarantined_row_numbers == (2,)
    assert not file_report.can_normalize_valid_rows


def test_row_disposition_has_no_implicit_skipped_state() -> None:
    with pytest.raises(ValueError, match="require event IDs"):
        RowDisposition(2, RowDispositionStatus.NORMALIZED, (), ())
    with pytest.raises(ValueError, match="require issue codes"):
        RowDisposition(2, RowDispositionStatus.QUARANTINED, (), ())


def test_normalization_rejects_silently_dropped_rows() -> None:
    document = _document()
    event = _event(document)

    with pytest.raises(ValueError, match="every input row"):
        NormalizationResult(
            adapter_id="gateway-csv",
            adapter_version="1.0.0",
            source_file_id=document.file_id,
            source_file_sha256=document.sha256,
            mapping_profile=_profile(),
            rows_seen=2,
            events=(event,),
            row_dispositions=(
                RowDisposition(2, RowDispositionStatus.NORMALIZED, (event.event_id,), ()),
            ),
            issues=(),
        )


def test_quarantine_must_cite_a_blocking_issue_for_the_same_row() -> None:
    document = _document()
    with pytest.raises(ValueError, match="every row blocker"):
        NormalizationResult(
            adapter_id="gateway-csv",
            adapter_version="1.0.0",
            source_file_id=document.file_id,
            source_file_sha256=document.sha256,
            mapping_profile=_profile(),
            rows_seen=1,
            events=(),
            row_dispositions=(
                RowDisposition(3, RowDispositionStatus.QUARANTINED, (), ("INVALID_AMOUNT",)),
            ),
            issues=(_issue(row_number=2),),
        )


def test_blocking_row_cannot_be_reported_as_normalized() -> None:
    document = _document()
    event = _event(document)

    with pytest.raises(ValueError, match="every row blocker"):
        NormalizationResult(
            adapter_id="gateway-csv",
            adapter_version="1.0.0",
            source_file_id=document.file_id,
            source_file_sha256=document.sha256,
            mapping_profile=_profile(),
            rows_seen=1,
            events=(event,),
            row_dispositions=(
                RowDisposition(2, RowDispositionStatus.NORMALIZED, (event.event_id,), ()),
            ),
            issues=(_issue(row_number=2),),
        )


def test_normalization_propagates_mapping_version_and_lineage() -> None:
    document = _document()
    event = _event(document, mapping_version="gateway-standard@old")
    disposition = RowDisposition(2, RowDispositionStatus.NORMALIZED, (event.event_id,), ())

    with pytest.raises(ValueError, match="mapping version"):
        NormalizationResult(
            adapter_id="gateway-csv",
            adapter_version="1.0.0",
            source_file_id=document.file_id,
            source_file_sha256=document.sha256,
            mapping_profile=_profile(),
            rows_seen=1,
            events=(event,),
            row_dispositions=(disposition,),
            issues=(),
        )
