"""Razorpay-style payment and settlement adapter."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from core.vericlose.adapters.base import RowProblem, TabularSourceAdapter
from core.vericlose.domain.enums import Direction, EventType, SourceType
from core.vericlose.domain.events import CanonicalEvent
from core.vericlose.domain.money import Money
from core.vericlose.ingestion.contracts import (
    ControlTotal,
    ControlTotals,
    NormalizationContext,
    SourceDocument,
)
from core.vericlose.ingestion.mappings import FileMappingProfile
from core.vericlose.ingestion.tabular import TabularRow


@dataclass(frozen=True, slots=True)
class GatewayValues:
    source_record_id: str
    event_type: EventType
    payment_reference: str
    settlement_reference: str
    signed_amount_minor: int
    currency: str
    event_at: datetime
    external_reference: str
    narration: str


class GatewayAdapter(TabularSourceAdapter):
    adapter_id = "razorpay-style-gateway"
    source_type = SourceType.GATEWAY

    def _parse_row(self, row: TabularRow, profile: FileMappingProfile) -> GatewayValues:
        source_record_id = str(self._mapped(row, profile, "source_record_id"))
        if not source_record_id:
            raise RowProblem(
                "SOURCE_RECORD_ID_MISSING",
                "Gateway event ID is blank",
                "source_record_id",
                "Supply a stable gateway event ID",
            )
        event_name = str(self._mapped(row, profile, "event_type"))
        try:
            event_type = EventType(event_name)
        except ValueError as error:
            raise RowProblem(
                "GATEWAY_EVENT_TYPE_UNKNOWN",
                f"Unknown gateway event type: {event_name}",
                "event_type",
                "Use PAYMENT, REFUND, FEE, TAX, ADJUSTMENT, or SETTLEMENT",
            ) from error
        allowed = {
            EventType.PAYMENT,
            EventType.REFUND,
            EventType.FEE,
            EventType.TAX,
            EventType.ADJUSTMENT,
            EventType.SETTLEMENT,
        }
        if event_type not in allowed:
            raise RowProblem(
                "GATEWAY_EVENT_TYPE_UNSUPPORTED",
                f"Unsupported gateway event type: {event_name}",
                "event_type",
                "Map this type explicitly before importing",
            )
        amount = self._mapped(row, profile, "amount_minor")
        assert isinstance(amount, int)
        if amount == 0:
            raise RowProblem(
                "AMOUNT_ZERO",
                "Gateway amount cannot be zero",
                "amount_minor",
                "Supply a non-zero amount",
            )
        currency = str(self._mapped(row, profile, "currency"))
        try:
            Money(0, currency)
        except (TypeError, ValueError) as error:
            raise RowProblem(
                "CURRENCY_INVALID",
                str(error),
                "currency",
                "Supply a three-letter ISO currency code",
            ) from error
        event_at = self._mapped(row, profile, "event_at")
        assert isinstance(event_at, datetime)
        return GatewayValues(
            source_record_id,
            event_type,
            str(self._mapped(row, profile, "payment_reference")),
            str(self._mapped(row, profile, "settlement_reference")),
            amount,
            currency,
            event_at,
            str(self._mapped(row, profile, "external_reference")),
            str(self._mapped(row, profile, "narration")),
        )

    def _build_event(
        self,
        document: SourceDocument,
        row: TabularRow,
        profile: FileMappingProfile,
        context: NormalizationContext,
        parsed: object,
    ) -> CanonicalEvent:
        if not isinstance(parsed, GatewayValues):
            raise TypeError("expected GatewayValues")
        default_direction = (
            Direction.CREDIT
            if parsed.event_type in {EventType.PAYMENT, EventType.SETTLEMENT}
            else Direction.DEBIT
        )
        direction = (
            default_direction if parsed.signed_amount_minor > 0 else _opposite(default_direction)
        )
        return CanonicalEvent(
            event_id=self._event_id(context, parsed.source_record_id),
            run_id=context.run_id,
            source_type=self.source_type,
            source_record_id=parsed.source_record_id,
            legal_entity_id=context.legal_entity_id,
            event_type=parsed.event_type,
            money=Money(abs(parsed.signed_amount_minor), parsed.currency),
            direction=direction,
            event_at=parsed.event_at,
            value_date=None,
            external_reference=parsed.external_reference or None,
            settlement_reference=parsed.settlement_reference or None,
            payment_reference=parsed.payment_reference or None,
            bank_utr=None,
            account_code=None,
            narration=parsed.narration or None,
            lineage=self._lineage(document, row),
            raw_fields=self._raw_fields(row),
            mapping_profile_version=profile.ref.versioned_id,
        )

    def control_totals(self, events: Sequence[CanonicalEvent]) -> ControlTotals:
        _require_source(events, self.source_type)
        components = tuple(
            ControlTotal(
                event_type.value,
                _currency(members),
                sum(event.money.amount_minor for event in members),
                len(members),
            )
            for event_type in EventType
            if (members := tuple(event for event in events if event.event_type is event_type))
        )
        return ControlTotals(self.source_type, len(events), components)


def _opposite(direction: Direction) -> Direction:
    return Direction.DEBIT if direction is Direction.CREDIT else Direction.CREDIT


def _require_source(events: Sequence[CanonicalEvent], source: SourceType) -> None:
    if any(event.source_type is not source for event in events):
        raise ValueError("control totals received events from another source")


def _currency(events: Sequence[CanonicalEvent]) -> str:
    currencies = {event.money.currency for event in events}
    if len(currencies) != 1:
        raise ValueError("control-total components cannot mix currencies")
    return next(iter(currencies))
