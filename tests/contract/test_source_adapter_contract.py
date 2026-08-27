"""S3.1 proof that the reusable adapter contract catches unsafe behavior."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

import pytest

from core.vericlose.domain.enums import Direction, EventType, SourceType
from core.vericlose.domain.events import CanonicalEvent, RawField, RawRowRef
from core.vericlose.domain.money import Money
from core.vericlose.ingestion.contracts import (
    ControlTotal,
    ControlTotals,
    DetectionReason,
    DetectionResult,
    IssueSeverity,
    MappingProfileRef,
    NormalizationContext,
    NormalizationResult,
    RowDisposition,
    RowDispositionStatus,
    SourceDocument,
    SourceFormat,
    ValidationIssue,
    ValidationReport,
    ValidationStage,
)
from core.vericlose.ports.source_adapter import MappingProfile
from tests.contract.source_adapter_contract import SourceAdapterContract


@dataclass(frozen=True, slots=True)
class FakeMappingProfile:
    """Test double proving column knowledge lives behind MappingProfile."""

    ref: MappingProfileRef
    columns: tuple[tuple[str, str], ...]

    def source_column_for(self, canonical_field: str) -> str | None:
        return dict(self.columns).get(canonical_field)

    def transform_for(self, canonical_field: str) -> str | None:
        del canonical_field
        return None


class FakeGatewayCsvAdapter:
    """Minimal fake used only to exercise the shared adapter contract."""

    adapter_id = "fake-gateway-csv"
    adapter_version = "1.0.0"
    source_type = SourceType.GATEWAY
    supported_formats = frozenset({SourceFormat.CSV})

    def __init__(self, profiles: Sequence[MappingProfile]) -> None:
        self._profiles = tuple(profiles)

    def detect(self, document: SourceDocument) -> DetectionResult:
        is_csv = document.extension == ".csv"
        return DetectionResult(
            adapter_id=self.adapter_id,
            adapter_version=self.adapter_version,
            source_type=self.source_type,
            source_format=SourceFormat.CSV if is_csv else SourceFormat.UNKNOWN,
            confidence_bps=9_000 if is_csv else 0,
            reasons=(DetectionReason("CSV_EXTENSION", "The document has a CSV extension", 9_000),)
            if is_csv
            else (),
            candidate_profiles=tuple(profile.ref for profile in self._profiles) if is_csv else (),
        )

    def validate(
        self,
        document: SourceDocument,
        mapping_profile: MappingProfile,
    ) -> ValidationReport:
        rows, fieldnames = self._read(document)
        issues: list[ValidationIssue] = []
        required_columns = {
            mapping_profile.source_column_for(field)
            for field in ("source_record_id", "amount_minor", "event_at")
        }
        missing = {column for column in required_columns if column and column not in fieldnames}
        if None in required_columns or missing:
            issues.append(
                ValidationIssue(
                    stage=ValidationStage.SCHEMA,
                    severity=IssueSeverity.ERROR,
                    code="REQUIRED_COLUMN_MISSING",
                    message="The selected mapping cannot resolve every required field",
                    file_id=document.file_id,
                    table_name="rows",
                    row_number=None,
                    field_name=None,
                    supplied_value=",".join(sorted(missing)),
                    suggested_fix="Select a compatible mapping profile",
                    blocking=True,
                )
            )
        amount_column = mapping_profile.source_column_for("amount_minor")
        time_column = mapping_profile.source_column_for("event_at")
        if not issues and amount_column and time_column:
            for row_number, row in enumerate(rows, start=2):
                try:
                    int(row[amount_column])
                except (TypeError, ValueError):
                    issues.append(
                        self._row_issue(
                            document,
                            row_number,
                            "AMOUNT_NOT_INTEGER",
                            amount_column,
                            row.get(amount_column),
                            "Supply an integer amount in minor units",
                        )
                    )
                try:
                    parsed = datetime.fromisoformat(row[time_column])
                    if parsed.tzinfo is None or parsed.utcoffset() is None:
                        raise ValueError
                except (TypeError, ValueError):
                    issues.append(
                        self._row_issue(
                            document,
                            row_number,
                            "EVENT_TIME_INVALID",
                            time_column,
                            row.get(time_column),
                            "Supply an ISO-8601 timestamp with timezone",
                        )
                    )
        return ValidationReport(
            adapter_id=self.adapter_id,
            adapter_version=self.adapter_version,
            source_file_id=document.file_id,
            mapping_profile=mapping_profile.ref,
            rows_seen=len(rows),
            issues=tuple(issues),
        )

    def normalize(
        self,
        document: SourceDocument,
        mapping_profile: MappingProfile,
        context: NormalizationContext,
    ) -> NormalizationResult:
        rows, _ = self._read(document)
        report = self.validate(document, mapping_profile)
        if not report.can_normalize_valid_rows:
            raise ValueError("file-level validation errors must be fixed before normalization")

        issues_by_row: dict[int, list[ValidationIssue]] = {}
        for issue in report.issues:
            if issue.blocking and issue.row_number is not None:
                issues_by_row.setdefault(issue.row_number, []).append(issue)

        events: list[CanonicalEvent] = []
        dispositions: list[RowDisposition] = []
        id_column = mapping_profile.source_column_for("source_record_id")
        amount_column = mapping_profile.source_column_for("amount_minor")
        time_column = mapping_profile.source_column_for("event_at")
        assert id_column and amount_column and time_column  # guaranteed by validation above

        for row_number, row in enumerate(rows, start=2):
            row_issues = issues_by_row.get(row_number, [])
            if row_issues:
                dispositions.append(
                    RowDisposition(
                        row_number=row_number,
                        status=RowDispositionStatus.QUARANTINED,
                        event_ids=(),
                        issue_codes=tuple(issue.code for issue in row_issues),
                    )
                )
                continue

            record_id = row[id_column]
            event_id = f"event-{record_id}"
            raw_row = json.dumps(row, sort_keys=True, separators=(",", ":")).encode()
            event = CanonicalEvent(
                event_id=event_id,
                run_id=context.run_id,
                source_type=self.source_type,
                source_record_id=record_id,
                legal_entity_id=context.legal_entity_id,
                event_type=EventType.PAYMENT,
                money=Money(int(row[amount_column]), context.currency),
                direction=Direction.CREDIT,
                event_at=datetime.fromisoformat(row[time_column]),
                value_date=None,
                external_reference=None,
                settlement_reference=None,
                payment_reference=record_id,
                bank_utr=None,
                account_code=None,
                narration=None,
                lineage=RawRowRef(
                    source_file_id=document.file_id,
                    file_sha256=document.sha256,
                    table_name="rows",
                    row_number=row_number,
                    raw_row_hash=hashlib.sha256(raw_row).hexdigest(),
                ),
                raw_fields=tuple(RawField(name, value) for name, value in row.items()),
                mapping_profile_version=mapping_profile.ref.versioned_id,
            )
            events.append(event)
            dispositions.append(
                RowDisposition(
                    row_number=row_number,
                    status=RowDispositionStatus.NORMALIZED,
                    event_ids=(event_id,),
                    issue_codes=(),
                )
            )

        return NormalizationResult(
            adapter_id=self.adapter_id,
            adapter_version=self.adapter_version,
            source_file_id=document.file_id,
            source_file_sha256=document.sha256,
            mapping_profile=mapping_profile.ref,
            rows_seen=report.rows_seen,
            events=tuple(events),
            row_dispositions=tuple(dispositions),
            issues=report.issues,
        )

    def control_totals(self, events: Sequence[CanonicalEvent]) -> ControlTotals:
        if any(event.source_type is not self.source_type for event in events):
            raise ValueError("control totals received an event from another source")
        amount = sum(event.money.amount_minor for event in events)
        currency = events[0].money.currency if events else "INR"
        return ControlTotals(
            source_type=self.source_type,
            event_count=len(events),
            components=(ControlTotal("PAYMENTS", currency, amount, len(events)),),
        )

    @staticmethod
    def _read(document: SourceDocument) -> tuple[list[dict[str, str]], tuple[str, ...]]:
        reader = csv.DictReader(io.StringIO(document.content.decode("utf-8")))
        rows = [dict(row) for row in reader]
        return rows, tuple(reader.fieldnames or ())

    @staticmethod
    def _row_issue(
        document: SourceDocument,
        row_number: int,
        code: str,
        field_name: str,
        value: str | None,
        suggested_fix: str,
    ) -> ValidationIssue:
        return ValidationIssue(
            stage=ValidationStage.SEMANTIC,
            severity=IssueSeverity.ERROR,
            code=code,
            message=f"Invalid {field_name}",
            file_id=document.file_id,
            table_name="rows",
            row_number=row_number,
            field_name=field_name,
            supplied_value=value,
            suggested_fix=suggested_fix,
            blocking=True,
        )


def _profile(
    profile_id: str = "gateway-standard",
    version: str = "1.0.0",
    columns: tuple[tuple[str, str], ...] = (
        ("source_record_id", "record_id"),
        ("amount_minor", "amount_minor"),
        ("event_at", "event_at"),
    ),
) -> FakeMappingProfile:
    return FakeMappingProfile(
        ref=MappingProfileRef(profile_id, version, SourceType.GATEWAY),
        columns=columns,
    )


def _document(file_id: str, content: str) -> SourceDocument:
    return SourceDocument.from_bytes(
        file_id=file_id,
        original_name=f"{file_id}.csv",
        media_type="text/csv",
        content=content.encode(),
    )


class TestFakeGatewayAdapter(SourceAdapterContract):
    @pytest.fixture
    def mapping_profile(self) -> FakeMappingProfile:
        return _profile()

    @pytest.fixture
    def adapter(self, mapping_profile: FakeMappingProfile) -> FakeGatewayCsvAdapter:
        return FakeGatewayCsvAdapter((mapping_profile,))

    @pytest.fixture
    def valid_document(self) -> SourceDocument:
        return _document(
            "gateway-valid",
            "record_id,amount_minor,event_at\n"
            "pay-1,10000,2026-08-01T10:00:00+05:30\n"
            "pay-2,25000,2026-08-01T10:05:00+05:30\n",
        )

    @pytest.fixture
    def mixed_document(self) -> SourceDocument:
        return _document(
            "gateway-mixed",
            "record_id,amount_minor,event_at\n"
            "pay-1,10000,2026-08-01T10:00:00+05:30\n"
            "pay-2,not-money,2026-08-01T10:05:00+05:30\n",
        )

    @pytest.fixture
    def normalization_context(self) -> NormalizationContext:
        return NormalizationContext("run-contract", "merchant-contract")


def test_mapping_profile_changes_layout_without_changing_adapter_code() -> None:
    standard = _profile()
    alternate = _profile(
        profile_id="gateway-alternate",
        version="2.1.0",
        columns=(
            ("source_record_id", "payment_key"),
            ("amount_minor", "value_in_paise"),
            ("event_at", "captured_timestamp"),
        ),
    )
    adapter = FakeGatewayCsvAdapter((standard, alternate))
    context = NormalizationContext("run-layout", "merchant-layout")
    standard_result = adapter.normalize(
        _document(
            "standard",
            "record_id,amount_minor,event_at\npay-1,10000,2026-08-01T10:00:00+05:30\n",
        ),
        standard,
        context,
    )
    alternate_result = adapter.normalize(
        _document(
            "alternate",
            "payment_key,value_in_paise,captured_timestamp\n"
            "pay-1,10000,2026-08-01T10:00:00+05:30\n",
        ),
        alternate,
        context,
    )

    standard_event = standard_result.events[0]
    alternate_event = alternate_result.events[0]
    assert standard_event.source_record_id == alternate_event.source_record_id
    assert standard_event.money == alternate_event.money
    assert standard_event.event_at == alternate_event.event_at
    assert standard_event.mapping_profile_version == "gateway-standard@1.0.0"
    assert alternate_event.mapping_profile_version == "gateway-alternate@2.1.0"
