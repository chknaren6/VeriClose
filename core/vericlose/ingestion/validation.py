"""Cross-source readiness checks run after source-level staged validation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from core.vericlose.domain.enums import SourceType
from core.vericlose.domain.events import CanonicalEvent
from core.vericlose.ingestion.contracts import IssueSeverity, ValidationIssue, ValidationStage


@dataclass(frozen=True, slots=True)
class CrossSourceValidationReport:
    issues: tuple[ValidationIssue, ...]

    @property
    def is_ready(self) -> bool:
        return not any(issue.blocking for issue in self.issues)


def validate_cross_source_readiness(
    events: tuple[CanonicalEvent, ...],
    *,
    expected_sources: frozenset[SourceType] = frozenset(
        {SourceType.GATEWAY, SourceType.BANK, SourceType.ERP}
    ),
    maximum_date_span_days: int = 45,
) -> CrossSourceValidationReport:
    issues: list[ValidationIssue] = []
    present_sources = {event.source_type for event in events}
    for missing in sorted(expected_sources - present_sources, key=lambda source: source.value):
        issues.append(
            _batch_issue(
                "SOURCE_MISSING",
                f"Required source is missing: {missing.value}",
                "Upload and validate the missing source before reconciliation",
            )
        )
    entities = {event.legal_entity_id for event in events}
    if len(entities) > 1:
        issues.append(
            _batch_issue(
                "LEGAL_ENTITY_CONFLICT",
                f"Events span multiple legal entities: {', '.join(sorted(entities))}",
                "Import one legal entity per reconciliation run",
            )
        )
    currencies = {event.money.currency for event in events}
    if len(currencies) > 1:
        issues.append(
            _batch_issue(
                "CURRENCY_CONFLICT",
                f"Events span multiple currencies: {', '.join(sorted(currencies))}",
                "Import one currency per MVP reconciliation run",
            )
        )
    dates = tuple(_event_date(event) for event in events)
    if dates and (max(dates) - min(dates)).days > maximum_date_span_days:
        issues.append(
            _batch_issue(
                "DATE_RANGE_CONFLICT",
                f"Event date span exceeds {maximum_date_span_days} days",
                "Confirm the accounting period or split the import into separate runs",
            )
        )
    return CrossSourceValidationReport(tuple(issues))


def _event_date(event: CanonicalEvent) -> date:
    return event.value_date or event.event_at.date()


def _batch_issue(code: str, message: str, suggested_fix: str) -> ValidationIssue:
    return ValidationIssue(
        stage=ValidationStage.CROSS_SOURCE,
        severity=IssueSeverity.ERROR,
        code=code,
        message=message,
        file_id="batch",
        table_name=None,
        row_number=None,
        field_name=None,
        supplied_value=None,
        suggested_fix=suggested_fix,
        blocking=True,
    )
