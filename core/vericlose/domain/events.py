"""Canonical finance events and immutable source-row lineage."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from core.vericlose.domain.enums import Direction, EventType, SourceType
from core.vericlose.domain.money import Money

RawScalar = str | int | bool | None
_HEX = frozenset("0123456789abcdef")


def _require_sha256(value: str, field_name: str) -> None:
    if not isinstance(value, str) or len(value) != 64 or any(
        character not in _HEX for character in value.lower()
    ):
        raise ValueError(f"{field_name} must be a 64-character hexadecimal string")


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} cannot be blank")


@dataclass(frozen=True, slots=True)
class RawField:
    """One preserved value from the original row; normalization never overwrites it."""

    name: str
    value: RawScalar

    def __post_init__(self) -> None:
        _require_text(self.name, "RawField.name")
        if isinstance(self.value, float):
            raise TypeError("raw monetary/decimal values must be preserved as strings, not floats")


@dataclass(frozen=True, slots=True)
class RawRowRef:
    source_file_id: str
    file_sha256: str
    table_name: str
    row_number: int
    raw_row_hash: str

    def __post_init__(self) -> None:
        _require_text(self.source_file_id, "source_file_id")
        _require_text(self.table_name, "table_name")
        if isinstance(self.row_number, bool) or not isinstance(self.row_number, int):
            raise TypeError("row_number must be an integer")
        if self.row_number < 1:
            raise ValueError("row_number must be >= 1")
        _require_sha256(self.file_sha256, "file_sha256")
        _require_sha256(self.raw_row_hash, "raw_row_hash")


@dataclass(frozen=True, slots=True)
class CanonicalEvent:
    """Source-independent event consumed by future reconciliation rules."""

    event_id: str
    run_id: str
    source_type: SourceType
    source_record_id: str
    legal_entity_id: str
    event_type: EventType
    money: Money
    direction: Direction
    event_at: datetime
    value_date: date | None
    external_reference: str | None
    settlement_reference: str | None
    payment_reference: str | None
    bank_utr: str | None
    account_code: str | None
    narration: str | None
    lineage: RawRowRef
    raw_fields: tuple[RawField, ...]
    mapping_profile_version: str

    def __post_init__(self) -> None:
        required_text = (
            (self.event_id, "event_id"),
            (self.run_id, "run_id"),
            (self.source_record_id, "source_record_id"),
            (self.legal_entity_id, "legal_entity_id"),
            (self.mapping_profile_version, "mapping_profile_version"),
        )
        for value, field_name in required_text:
            _require_text(value, field_name)

        if not isinstance(self.source_type, SourceType):
            raise TypeError("source_type must be a SourceType")
        if not isinstance(self.event_type, EventType):
            raise TypeError("event_type must be an EventType")
        if not isinstance(self.money, Money):
            raise TypeError("money must be a Money value")
        if not isinstance(self.direction, Direction):
            raise TypeError("direction must be a Direction")
        if not isinstance(self.event_at, datetime):
            raise TypeError("event_at must be a datetime")
        if self.event_at.tzinfo is None or self.event_at.utcoffset() is None:
            raise ValueError("event_at must be timezone-aware")
        if self.value_date is not None and (
            isinstance(self.value_date, datetime) or not isinstance(self.value_date, date)
        ):
            raise TypeError("value_date must be a date, not a datetime")
        if not isinstance(self.lineage, RawRowRef):
            raise TypeError("lineage must be a RawRowRef")
        if not isinstance(self.raw_fields, tuple):
            raise TypeError("raw_fields must be a tuple[RawField, ...]")
        if any(not isinstance(field, RawField) for field in self.raw_fields):
            raise TypeError("raw_fields can contain only RawField values")
