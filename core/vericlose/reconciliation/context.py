"""Read-only reconciliation context; rules never scan repositories directly."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from core.vericlose.domain.enums import Direction, EventType, SourceType
from core.vericlose.domain.events import CanonicalEvent
from core.vericlose.reconciliation.indexes import CandidateIndexes
from core.vericlose.reconciliation.policy import ReconciliationPolicy


@dataclass(frozen=True, slots=True)
class ReconciliationContext:
    run_id: str
    legal_entity_id: str
    events: tuple[CanonicalEvent, ...]
    indexes: CandidateIndexes
    policy: ReconciliationPolicy

    @classmethod
    def build(
        cls,
        events: tuple[CanonicalEvent, ...],
        policy: ReconciliationPolicy,
    ) -> ReconciliationContext:
        if not events:
            raise ValueError("reconciliation requires canonical events")
        run_ids = {event.run_id for event in events}
        entities = {event.legal_entity_id for event in events}
        if len(run_ids) != 1 or len(entities) != 1:
            raise ValueError("events must belong to one run and one legal entity")
        currencies = {event.money.currency for event in events}
        if currencies != {policy.currency}:
            raise ValueError(
                f"policy currency {policy.currency} does not match events {sorted(currencies)}"
            )
        ordered = tuple(sorted(events, key=lambda event: event.event_id))
        return cls(
            next(iter(run_ids)),
            next(iter(entities)),
            ordered,
            CandidateIndexes.build(ordered),
            policy,
        )

    @property
    def settlement_references(self) -> tuple[str, ...]:
        references = {
            event.settlement_reference
            for event in self.events
            if event.source_type is SourceType.GATEWAY and event.settlement_reference
        }
        return tuple(sorted(references))

    def gateway_settlement(self, reference: str) -> tuple[CanonicalEvent, ...]:
        return tuple(
            event
            for event in self.indexes.by_settlement_reference.get(reference, ())
            if event.source_type is SourceType.GATEWAY and self._same_scope(event)
        )

    def erp_journals(self, reference: str) -> tuple[tuple[CanonicalEvent, ...], ...]:
        candidates = (
            event
            for event in self.indexes.by_external_reference.get(reference, ())
            if event.source_type is SourceType.ERP and self._same_scope(event)
        )
        grouped: dict[str, list[CanonicalEvent]] = {}
        for event in candidates:
            journal_id = event.source_record_id.rsplit(":", 1)[0]
            grouped.setdefault(journal_id, []).append(event)
        return tuple(
            tuple(sorted(lines, key=lambda event: event.event_id))
            for _, lines in sorted(grouped.items())
        )

    def bank_candidates(
        self,
        *,
        settlement_date: date,
        consumed_event_ids: frozenset[str] = frozenset(),
    ) -> tuple[CanonicalEvent, ...]:
        first = settlement_date + timedelta(days=self.policy.dates.settlement_to_bank_min_days)
        last = settlement_date + timedelta(days=self.policy.dates.settlement_to_bank_max_days)
        candidates = (
            event
            for event in self.events
            if event.source_type is SourceType.BANK
            and event.event_type is EventType.BANK_CREDIT
            and event.direction is Direction.CREDIT
            and self._same_scope(event)
            and event.event_id not in consumed_event_ids
            and event.value_date is not None
            and first <= event.value_date <= last
        )
        return tuple(sorted(candidates, key=lambda event: (event.value_date, event.event_id)))

    def _same_scope(self, event: CanonicalEvent) -> bool:
        return (
            event.legal_entity_id == self.legal_entity_id
            and event.money.currency == self.policy.currency
        )
