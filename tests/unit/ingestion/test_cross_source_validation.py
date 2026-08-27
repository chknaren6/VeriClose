from dataclasses import replace
from datetime import UTC, datetime, timedelta

from core.vericlose.domain.enums import Direction, EventType, SourceType
from core.vericlose.domain.events import CanonicalEvent, RawRowRef
from core.vericlose.domain.money import Money
from core.vericlose.ingestion.validation import validate_cross_source_readiness


def _event(source_type: SourceType, *, currency: str = "INR", days: int = 0) -> CanonicalEvent:
    return CanonicalEvent(
        event_id=f"event-{source_type.value}",
        run_id="run-cross",
        source_type=source_type,
        source_record_id=f"record-{source_type.value}",
        legal_entity_id="merchant-in",
        event_type={
            SourceType.GATEWAY: EventType.SETTLEMENT,
            SourceType.BANK: EventType.BANK_CREDIT,
            SourceType.ERP: EventType.ERP_JOURNAL_LINE,
        }[source_type],
        money=Money(100, currency),
        direction=Direction.CREDIT,
        event_at=datetime(2026, 4, 1, tzinfo=UTC) + timedelta(days=days),
        value_date=None,
        external_reference=None,
        settlement_reference=None,
        payment_reference=None,
        bank_utr=None,
        account_code=None,
        narration=None,
        lineage=RawRowRef(f"file-{source_type.value}", "a" * 64, "rows", 2, "b" * 64),
        raw_fields=(),
        mapping_profile_version=f"{source_type.value.lower()}@1",
    )


def test_cross_source_ready_only_when_source_entity_currency_and_dates_agree() -> None:
    events = tuple(_event(source) for source in SourceType)
    assert validate_cross_source_readiness(events).is_ready

    bad = (
        events[0],
        replace(events[1], money=Money(100, "USD")),
        replace(
            events[2],
            event_at=events[2].event_at + timedelta(days=60),
            legal_entity_id="another-entity",
        ),
    )
    codes = {issue.code for issue in validate_cross_source_readiness(bad).issues}
    assert codes == {
        "CURRENCY_CONFLICT",
        "DATE_RANGE_CONFLICT",
        "LEGAL_ENTITY_CONFLICT",
    }


def test_cross_source_reports_missing_source() -> None:
    report = validate_cross_source_readiness((_event(SourceType.GATEWAY),))
    assert {issue.code for issue in report.issues} == {"SOURCE_MISSING"}
