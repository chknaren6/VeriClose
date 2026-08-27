import json
from datetime import UTC, date, datetime

from core.vericlose.domain.enums import Direction, EventType, SourceType
from core.vericlose.domain.events import CanonicalEvent, RawField, RawRowRef
from core.vericlose.domain.evidence import EvidenceLink
from core.vericlose.domain.money import Money
from core.vericlose.domain.wire import (
    canonical_event_from_dict,
    canonical_event_to_dict,
    evidence_link_from_dict,
    evidence_link_to_dict,
)


def test_event_and_evidence_round_trip_preserves_audit_fields() -> None:
    event = CanonicalEvent(
        event_id="evt-stable",
        run_id="run-1",
        source_type=SourceType.BANK,
        source_record_id="bank-1",
        legal_entity_id="merchant-1",
        event_type=EventType.BANK_CREDIT,
        money=Money(12_345, "INR"),
        direction=Direction.CREDIT,
        event_at=datetime(2026, 4, 1, 10, tzinfo=UTC),
        value_date=date(2026, 4, 2),
        external_reference=None,
        settlement_reference="set-1",
        payment_reference=None,
        bank_utr="UTR1",
        account_code=None,
        narration="Synthetic bank row",
        lineage=RawRowRef("file-1", "a" * 64, "bank", 17, "b" * 64),
        raw_fields=(RawField("credit_amount", "123.45"),),
        mapping_profile_version="bank-v1",
    )
    link = EvidenceLink("evt-stable", "file-1", "bank", 17, "b" * 64, "amount")

    event_payload = json.loads(json.dumps(canonical_event_to_dict(event)))
    link_payload = json.loads(json.dumps(evidence_link_to_dict(link)))
    restored_event = canonical_event_from_dict(event_payload)
    restored_link = evidence_link_from_dict(link_payload)

    assert restored_event == event
    assert restored_event.money.amount_minor == 12_345
    assert restored_event.lineage.row_number == 17
    assert restored_link == link
