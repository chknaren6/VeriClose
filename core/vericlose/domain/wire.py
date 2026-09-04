"""Explicit JSON-safe wire conversion for foundational domain evidence.

This is intentionally narrow. API DTOs may evolve independently, while these helpers make
the audit-critical event identity, paise amount, and source coordinates round-trip exactly.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from core.vericlose.domain.enums import Direction, EventType, SourceType
from core.vericlose.domain.events import CanonicalEvent, RawField, RawRowRef
from core.vericlose.domain.evidence import EvidenceLink
from core.vericlose.domain.money import Money


def canonical_event_to_dict(event: CanonicalEvent) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "run_id": event.run_id,
        "source_type": event.source_type.value,
        "source_record_id": event.source_record_id,
        "legal_entity_id": event.legal_entity_id,
        "event_type": event.event_type.value,
        "amount_minor": event.money.amount_minor,
        "currency": event.money.currency,
        "direction": event.direction.value,
        "event_at": event.event_at.isoformat(),
        "value_date": event.value_date.isoformat() if event.value_date else None,
        "external_reference": event.external_reference,
        "settlement_reference": event.settlement_reference,
        "payment_reference": event.payment_reference,
        "bank_utr": event.bank_utr,
        "account_code": event.account_code,
        "narration": event.narration,
        "lineage": {
            "source_file_id": event.lineage.source_file_id,
            "file_sha256": event.lineage.file_sha256,
            "table_name": event.lineage.table_name,
            "row_number": event.lineage.row_number,
            "raw_row_hash": event.lineage.raw_row_hash,
        },
        "raw_fields": [{"name": field.name, "value": field.value} for field in event.raw_fields],
        "mapping_profile_version": event.mapping_profile_version,
    }


def canonical_event_from_dict(payload: dict[str, Any]) -> CanonicalEvent:
    lineage = payload["lineage"]
    return CanonicalEvent(
        event_id=_require_string(payload["event_id"], "event_id"),
        run_id=_require_string(payload["run_id"], "run_id"),
        source_type=SourceType(payload["source_type"]),
        source_record_id=_require_string(payload["source_record_id"], "source_record_id"),
        legal_entity_id=_require_string(payload["legal_entity_id"], "legal_entity_id"),
        event_type=EventType(payload["event_type"]),
        money=Money(
            _require_int(payload["amount_minor"], "amount_minor"),
            _require_string(payload["currency"], "currency"),
        ),
        direction=Direction(payload["direction"]),
        event_at=datetime.fromisoformat(str(payload["event_at"])),
        value_date=(
            date.fromisoformat(str(payload["value_date"]))
            if payload.get("value_date") is not None
            else None
        ),
        external_reference=_optional_text(payload.get("external_reference")),
        settlement_reference=_optional_text(payload.get("settlement_reference")),
        payment_reference=_optional_text(payload.get("payment_reference")),
        bank_utr=_optional_text(payload.get("bank_utr")),
        account_code=_optional_text(payload.get("account_code")),
        narration=_optional_text(payload.get("narration")),
        lineage=RawRowRef(
            source_file_id=_require_string(lineage["source_file_id"], "source_file_id"),
            file_sha256=_require_string(lineage["file_sha256"], "file_sha256"),
            table_name=_require_string(lineage["table_name"], "table_name"),
            row_number=_require_int(lineage["row_number"], "row_number"),
            raw_row_hash=_require_string(lineage["raw_row_hash"], "raw_row_hash"),
        ),
        raw_fields=tuple(
            RawField(
                name=_require_string(field["name"], "raw field name"),
                value=field.get("value"),
            )
            for field in payload["raw_fields"]
        ),
        mapping_profile_version=_require_string(
            payload["mapping_profile_version"], "mapping_profile_version"
        ),
    )


def evidence_link_to_dict(link: EvidenceLink) -> dict[str, Any]:
    return {
        "event_id": link.event_id,
        "source_file_id": link.source_file_id,
        "table_name": link.table_name,
        "row_number": link.row_number,
        "raw_row_hash": link.raw_row_hash,
        "purpose": link.purpose,
    }


def evidence_link_from_dict(payload: dict[str, Any]) -> EvidenceLink:
    return EvidenceLink(
        event_id=_optional_text(payload.get("event_id")),
        source_file_id=_require_string(payload["source_file_id"], "source_file_id"),
        table_name=_require_string(payload["table_name"], "table_name"),
        row_number=_require_int(payload["row_number"], "row_number"),
        raw_row_hash=_require_string(payload["raw_row_hash"], "raw_row_hash"),
        purpose=_require_string(payload["purpose"], "purpose"),
    )


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    return _require_string(value, "optional text")


def _require_string(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    return value


def _require_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must remain an integer across the wire")
    return value
