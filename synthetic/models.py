"""Generator-internal source rows; `to_csv_row` exposes only runtime-safe fields."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime
from typing import Any

from core.vericlose.domain.enums import EventType, SourceType
from synthetic.truth.models import EventTruth, TruthDataset, source_key


def format_rupees(amount_minor: int) -> str:
    """Format integer paise without ever passing through binary floating point."""

    if amount_minor < 0:
        raise ValueError("format_rupees expects a non-negative magnitude")
    rupees, paise = divmod(amount_minor, 100)
    return f"{rupees}.{paise:02d}"


@dataclass(frozen=True, slots=True)
class GatewayRow:
    case_id: str  # generator-only metadata; intentionally omitted from CSV
    gateway_event_id: str
    event_type: EventType
    transaction_id: str
    settlement_id: str
    amount_minor: int
    currency: str
    event_at: datetime
    status: str
    reference: str
    narration: str

    @property
    def source_type(self) -> SourceType:
        return SourceType.GATEWAY

    @property
    def source_record_id(self) -> str:
        return self.gateway_event_id

    def to_csv_row(self) -> dict[str, str | int]:
        return {
            "gateway_event_id": self.gateway_event_id,
            "event_type": self.event_type.value,
            "transaction_id": self.transaction_id,
            "settlement_id": self.settlement_id,
            "amount_minor": self.amount_minor,
            "currency": self.currency,
            "event_at": self.event_at.isoformat(),
            "status": self.status,
            "reference": self.reference,
            "narration": self.narration,
        }


@dataclass(frozen=True, slots=True)
class BankRow:
    case_id: str
    bank_record_id: str
    value_date: date
    booking_date: date
    credit_minor: int
    debit_minor: int
    utr: str
    narration: str
    currency: str
    account_reference: str

    @property
    def source_type(self) -> SourceType:
        return SourceType.BANK

    @property
    def source_record_id(self) -> str:
        return self.bank_record_id

    def to_csv_row(self) -> dict[str, str]:
        return {
            "bank_record_id": self.bank_record_id,
            "value_date": self.value_date.isoformat(),
            "booking_date": self.booking_date.isoformat(),
            "credit_amount": format_rupees(self.credit_minor),
            "debit_amount": format_rupees(self.debit_minor),
            "utr": self.utr,
            "narration": self.narration,
            "currency": self.currency,
            "account_reference": self.account_reference,
        }


@dataclass(frozen=True, slots=True)
class ErpRow:
    case_id: str
    erp_record_id: str
    journal_id: str
    line_number: int
    posting_date: date
    account_code: str
    debit_minor: int
    credit_minor: int
    currency: str
    external_reference: str
    narration: str

    @property
    def source_type(self) -> SourceType:
        return SourceType.ERP

    @property
    def source_record_id(self) -> str:
        return self.erp_record_id

    def to_csv_row(self) -> dict[str, str | int]:
        return {
            "journal_id": self.journal_id,
            "line_number": self.line_number,
            "posting_date": self.posting_date.isoformat(),
            "account_code": self.account_code,
            "debit_amount": format_rupees(self.debit_minor),
            "credit_amount": format_rupees(self.credit_minor),
            "currency": self.currency,
            "external_reference": self.external_reference,
            "narration": self.narration,
        }


SourceRow = GatewayRow | BankRow | ErpRow


@dataclass(frozen=True, slots=True)
class CaseContext:
    """Generator-only accounting facts used to target one controlled mutation."""

    case_id: str
    settlement_id: str
    utr: str
    gross_minor: int
    fee_minor: int
    tax_minor: int
    refund_minor: int
    net_minor: int


@dataclass(frozen=True, slots=True)
class GeneratedBatch:
    seed: int
    gateway_rows: tuple[GatewayRow, ...]
    bank_rows: tuple[BankRow, ...]
    erp_rows: tuple[ErpRow, ...]
    cases: tuple[CaseContext, ...]
    truth: TruthDataset

    def context(self, case_id: str) -> CaseContext:
        try:
            return next(context for context in self.cases if context.case_id == case_id)
        except StopIteration as error:
            raise KeyError(case_id) from error

    def rows_for_case(self, case_id: str) -> tuple[SourceRow, ...]:
        return tuple(
            row
            for row in (*self.gateway_rows, *self.bank_rows, *self.erp_rows)
            if row.case_id == case_id
        )

    def refresh_truth_members(self, case_id: str) -> GeneratedBatch:
        """Rebuild event labels after an injector adds/removes source rows."""

        rows = self.rows_for_case(case_id)
        events = tuple(
            EventTruth(
                source_type=row.source_type,
                source_record_id=row.source_record_id,
                expected_case_id=case_id,
                expected_role=_role_for_row(row),
            )
            for row in rows
        )
        member_keys = tuple(source_key(row.source_type, row.source_record_id) for row in rows)
        current_case = self.truth.case(case_id)
        truth = self.truth.replace_case_events(case_id, events).replace_case(
            replace(current_case, expected_member_keys=member_keys)
        )
        return replace(self, truth=truth)

    def control_totals(self) -> dict[str, Any]:
        gateway_by_type = {
            event_type.value: sum(
                row.amount_minor for row in self.gateway_rows if row.event_type is event_type
            )
            for event_type in EventType
            if any(row.event_type is event_type for row in self.gateway_rows)
        }
        return {
            "row_counts": {
                "gateway": len(self.gateway_rows),
                "bank": len(self.bank_rows),
                "erp_gl": len(self.erp_rows),
                "total": len(self.gateway_rows) + len(self.bank_rows) + len(self.erp_rows),
            },
            "gateway_amount_minor_by_event_type": gateway_by_type,
            "bank_credit_minor": sum(row.credit_minor for row in self.bank_rows),
            "bank_debit_minor": sum(row.debit_minor for row in self.bank_rows),
            "erp_debit_minor": sum(row.debit_minor for row in self.erp_rows),
            "erp_credit_minor": sum(row.credit_minor for row in self.erp_rows),
        }


def _role_for_row(row: SourceRow) -> str:
    if isinstance(row, GatewayRow):
        return f"GATEWAY_{row.event_type.value}"
    if isinstance(row, BankRow):
        return "BANK_RECEIPT" if row.credit_minor else "BANK_DEBIT"
    return "ERP_DEBIT" if row.debit_minor else "ERP_CREDIT"
