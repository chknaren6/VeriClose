"""Immutable lookup indexes used to keep candidate search bounded."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from types import MappingProxyType

from core.vericlose.domain.events import CanonicalEvent


@dataclass(frozen=True, slots=True)
class CandidateIndexes:
    by_settlement_reference: Mapping[str, tuple[CanonicalEvent, ...]]
    by_utr: Mapping[str, tuple[CanonicalEvent, ...]]
    by_external_reference: Mapping[str, tuple[CanonicalEvent, ...]]
    by_amount_minor: Mapping[int, tuple[CanonicalEvent, ...]]
    by_date: Mapping[date, tuple[CanonicalEvent, ...]]

    @classmethod
    def build(cls, events: tuple[CanonicalEvent, ...]) -> CandidateIndexes:
        settlement: dict[str, list[CanonicalEvent]] = defaultdict(list)
        utr: dict[str, list[CanonicalEvent]] = defaultdict(list)
        external: dict[str, list[CanonicalEvent]] = defaultdict(list)
        amount: dict[int, list[CanonicalEvent]] = defaultdict(list)
        dates: dict[date, list[CanonicalEvent]] = defaultdict(list)
        for event in sorted(events, key=lambda item: item.event_id):
            if event.settlement_reference:
                settlement[event.settlement_reference].append(event)
            if event.bank_utr:
                utr[event.bank_utr].append(event)
            if event.external_reference:
                external[event.external_reference].append(event)
            amount[event.money.amount_minor].append(event)
            dates[event.value_date or event.event_at.date()].append(event)
        return cls(
            _freeze(settlement),
            _freeze(utr),
            _freeze(external),
            _freeze(amount),
            _freeze(dates),
        )


def _freeze(mapping: dict[object, list[CanonicalEvent]]) -> Mapping:
    return MappingProxyType({key: tuple(value) for key, value in mapping.items()})
