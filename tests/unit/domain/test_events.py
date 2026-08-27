from datetime import UTC, date, datetime

import pytest

from core.vericlose.domain.enums import Direction, EventType, SourceType
from core.vericlose.domain.events import CanonicalEvent, RawField, RawRowRef
from core.vericlose.domain.money import Money


def _lineage() -> RawRowRef:
    return RawRowRef("file-1", "a" * 64, "payments", 2, "b" * 64)


def _event(**overrides: object) -> CanonicalEvent:
    fields: dict[str, object] = {
        "event_id": "evt-1",
        "run_id": "run-1",
        "source_type": SourceType.GATEWAY,
        "source_record_id": "pay-1",
        "legal_entity_id": "merchant-1",
        "event_type": EventType.PAYMENT,
        "money": Money(10_000),
        "direction": Direction.CREDIT,
        "event_at": datetime(2026, 4, 1, 10, tzinfo=UTC),
        "value_date": date(2026, 4, 1),
        "external_reference": "order-1",
        "settlement_reference": "set-1",
        "payment_reference": "pay-1",
        "bank_utr": None,
        "account_code": None,
        "narration": "Synthetic payment",
        "lineage": _lineage(),
        "raw_fields": (RawField("amount", "100.00"),),
        "mapping_profile_version": "gateway-v1",
    }
    fields.update(overrides)
    return CanonicalEvent(**fields)  # type: ignore[arg-type]


def test_event_preserves_lineage_and_raw_values() -> None:
    event = _event()
    assert event.lineage.row_number == 2
    assert event.raw_fields == (RawField("amount", "100.00"),)


def test_event_requires_timezone_aware_event_time() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        _event(event_at=datetime(2026, 4, 1, 10))


def test_value_date_is_an_accounting_date_not_timestamp() -> None:
    with pytest.raises(TypeError, match="date, not a datetime"):
        _event(value_date=datetime(2026, 4, 1, tzinfo=UTC))


def test_lineage_rejects_bad_hash_or_row() -> None:
    with pytest.raises(ValueError, match="64-character"):
        RawRowRef("file", "bad", "sheet", 1, "b" * 64)
    with pytest.raises(ValueError, match=">= 1"):
        RawRowRef("file", "a" * 64, "sheet", 0, "b" * 64)


def test_raw_float_is_not_preserved_implicitly() -> None:
    with pytest.raises(TypeError, match="strings"):
        RawField("amount", 10.5)  # type: ignore[arg-type]
