"""Generic bank statement adapter for debit/credit and signed layouts."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time

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
class BankValues:
    source_record_id: str
    value_date: date
    booking_date: date
    amount_minor: int
    direction: Direction
    bank_utr: str
    narration: str
    currency: str
    account_code: str


class BankAdapter(TabularSourceAdapter):
    adapter_id = "generic-bank-statement"
    source_type = SourceType.BANK

    def _parse_row(self, row: TabularRow, profile: FileMappingProfile) -> BankValues:
        source_record_id = str(self._mapped(row, profile, "source_record_id"))
        if not source_record_id:
            raise RowProblem(
                "SOURCE_RECORD_ID_MISSING",
                "Bank record ID is blank",
                "source_record_id",
                "Supply a stable statement line ID",
            )
        value_date = self._mapped(row, profile, "value_date")
        booking_date = self._mapped(row, profile, "booking_date")
        assert isinstance(value_date, date) and isinstance(booking_date, date)
        signed_column = profile.source_column_for("signed_amount_minor")
        if signed_column is not None:
            signed = self._mapped(row, profile, "signed_amount_minor")
            assert isinstance(signed, int)
            if signed == 0:
                raise RowProblem(
                    "BANK_AMOUNT_ZERO",
                    "Signed amount cannot be zero",
                    "signed_amount_minor",
                    "Supply a non-zero transaction amount",
                )
            amount, direction = abs(signed), Direction.CREDIT if signed > 0 else Direction.DEBIT
        else:
            credit = self._mapped(row, profile, "credit_minor")
            debit = self._mapped(row, profile, "debit_minor")
            assert isinstance(credit, int) and isinstance(debit, int)
            if credit < 0 or debit < 0:
                raise RowProblem(
                    "BANK_AMOUNT_NEGATIVE",
                    "Debit/credit columns cannot contain negative values",
                    "credit_minor" if credit < 0 else "debit_minor",
                    "Use positive magnitudes in debit/credit columns",
                )
            if (credit > 0) == (debit > 0):
                raise RowProblem(
                    "BANK_SIDES_INVALID",
                    "Exactly one of debit or credit must be non-zero",
                    None,
                    "Place the amount on exactly one side",
                )
            amount, direction = (credit, Direction.CREDIT) if credit else (debit, Direction.DEBIT)
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
        return BankValues(
            source_record_id,
            value_date,
            booking_date,
            amount,
            direction,
            str(self._mapped(row, profile, "bank_utr")),
            str(self._mapped(row, profile, "narration")),
            currency,
            str(self._mapped(row, profile, "account_code")),
        )

    def _build_event(
        self,
        document: SourceDocument,
        row: TabularRow,
        profile: FileMappingProfile,
        context: NormalizationContext,
        parsed: object,
    ) -> CanonicalEvent:
        if not isinstance(parsed, BankValues):
            raise TypeError("expected BankValues")
        event_type = (
            EventType.BANK_CREDIT if parsed.direction is Direction.CREDIT else EventType.BANK_DEBIT
        )
        return CanonicalEvent(
            event_id=self._event_id(context, parsed.source_record_id),
            run_id=context.run_id,
            source_type=self.source_type,
            source_record_id=parsed.source_record_id,
            legal_entity_id=context.legal_entity_id,
            event_type=event_type,
            money=Money(parsed.amount_minor, parsed.currency),
            direction=parsed.direction,
            event_at=datetime.combine(parsed.booking_date, time(), tzinfo=UTC),
            value_date=parsed.value_date,
            external_reference=parsed.bank_utr or None,
            settlement_reference=None,
            payment_reference=None,
            bank_utr=parsed.bank_utr or None,
            account_code=parsed.account_code or None,
            narration=parsed.narration or None,
            lineage=self._lineage(document, row),
            raw_fields=self._raw_fields(row),
            mapping_profile_version=profile.ref.versioned_id,
        )

    def control_totals(self, events: Sequence[CanonicalEvent]) -> ControlTotals:
        if any(event.source_type is not self.source_type for event in events):
            raise ValueError("control totals received events from another source")
        components = tuple(
            ControlTotal(
                direction.value,
                _currency(members),
                sum(event.money.amount_minor for event in members),
                len(members),
            )
            for direction in Direction
            if (members := tuple(event for event in events if event.direction is direction))
        )
        return ControlTotals(self.source_type, len(events), components)


def _currency(events: Sequence[CanonicalEvent]) -> str:
    currencies = {event.money.currency for event in events}
    if len(currencies) != 1:
        raise ValueError("control-total components cannot mix currencies")
    return next(iter(currencies))
