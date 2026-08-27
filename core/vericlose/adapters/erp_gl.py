"""Generic ERP general-ledger adapter with journal-level accounting validation."""

from __future__ import annotations

from collections import defaultdict
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
    ValidationIssue,
    ValidationStage,
)
from core.vericlose.ingestion.mappings import FileMappingProfile
from core.vericlose.ingestion.tabular import TabularData, TabularRow


@dataclass(frozen=True, slots=True)
class ErpValues:
    journal_id: str
    line_number: int
    posting_date: date
    account_code: str
    amount_minor: int
    direction: Direction
    currency: str
    external_reference: str
    narration: str

    @property
    def source_record_id(self) -> str:
        return f"{self.journal_id}:{self.line_number}"


class ErpGlAdapter(TabularSourceAdapter):
    adapter_id = "generic-erp-gl"
    source_type = SourceType.ERP

    def _parse_row(self, row: TabularRow, profile: FileMappingProfile) -> ErpValues:
        journal_id = str(self._mapped(row, profile, "journal_id"))
        if not journal_id:
            raise RowProblem(
                "JOURNAL_ID_MISSING",
                "Journal ID is blank",
                "journal_id",
                "Supply a journal or voucher ID",
            )
        line_number = self._mapped(row, profile, "line_number")
        if not isinstance(line_number, int) or line_number < 1:
            raise RowProblem(
                "LINE_NUMBER_INVALID",
                "Line number must be a positive integer",
                "line_number",
                "Supply a positive journal line number",
            )
        posting_date = self._mapped(row, profile, "posting_date")
        assert isinstance(posting_date, date)
        account_code = str(self._mapped(row, profile, "account_code"))
        if not account_code:
            raise RowProblem(
                "ACCOUNT_CODE_MISSING",
                "Account code is blank",
                "account_code",
                "Supply the source ERP account code",
            )
        debit = self._mapped(row, profile, "debit_minor")
        credit = self._mapped(row, profile, "credit_minor")
        assert isinstance(debit, int) and isinstance(credit, int)
        if debit < 0 or credit < 0:
            raise RowProblem(
                "ERP_AMOUNT_NEGATIVE",
                "ERP debit/credit magnitudes cannot be negative",
                "debit_minor" if debit < 0 else "credit_minor",
                "Use positive debit/credit magnitudes",
            )
        if (debit > 0) == (credit > 0):
            raise RowProblem(
                "ERP_SIDES_INVALID",
                "Exactly one of debit or credit must be non-zero",
                None,
                "Place the line amount on exactly one side",
            )
        amount, direction = (debit, Direction.DEBIT) if debit else (credit, Direction.CREDIT)
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
        return ErpValues(
            journal_id,
            line_number,
            posting_date,
            account_code,
            amount,
            direction,
            currency,
            str(self._mapped(row, profile, "external_reference")),
            str(self._mapped(row, profile, "narration")),
        )

    def _batch_issues(
        self,
        document: SourceDocument,
        data: TabularData,
        profile: FileMappingProfile,
        row_issues: tuple[ValidationIssue, ...],
    ) -> tuple[ValidationIssue, ...]:
        invalid_rows = {issue.row_number for issue in row_issues}
        journals: dict[str, list[tuple[TabularRow, ErpValues]]] = defaultdict(list)
        issues: list[ValidationIssue] = []
        for row in data.rows:
            if row.row_number in invalid_rows:
                continue
            parsed = self._parse_row(row, profile)
            assert isinstance(parsed, ErpValues)
            journals[parsed.journal_id].append((row, parsed))
        for journal_id, members in journals.items():
            line_numbers = [parsed.line_number for _, parsed in members]
            duplicate_lines = {number for number in line_numbers if line_numbers.count(number) > 1}
            debit_total = sum(
                parsed.amount_minor for _, parsed in members if parsed.direction is Direction.DEBIT
            )
            credit_total = sum(
                parsed.amount_minor for _, parsed in members if parsed.direction is Direction.CREDIT
            )
            for row, parsed in members:
                if parsed.line_number in duplicate_lines:
                    issues.append(
                        self._issue(
                            document,
                            row.row_number,
                            "ERP_LINE_DUPLICATE",
                            f"Journal {journal_id} repeats line {parsed.line_number}",
                            profile.source_column_for("line_number"),
                            str(parsed.line_number),
                            "Use a unique line number within the journal",
                            ValidationStage.ACCOUNTING,
                            table_name=row.table_name,
                        )
                    )
                if debit_total != credit_total:
                    issues.append(
                        self._issue(
                            document,
                            row.row_number,
                            "JOURNAL_UNBALANCED",
                            f"Journal {journal_id} is unbalanced: "
                            f"debits={debit_total}, credits={credit_total}",
                            None,
                            None,
                            "Correct the journal so total debits equal total credits",
                            ValidationStage.ACCOUNTING,
                            table_name=row.table_name,
                            blocking=False,
                        )
                    )
        return tuple(issues)

    def _build_event(
        self,
        document: SourceDocument,
        row: TabularRow,
        profile: FileMappingProfile,
        context: NormalizationContext,
        parsed: object,
    ) -> CanonicalEvent:
        if not isinstance(parsed, ErpValues):
            raise TypeError("expected ErpValues")
        return CanonicalEvent(
            event_id=self._event_id(context, parsed.source_record_id),
            run_id=context.run_id,
            source_type=self.source_type,
            source_record_id=parsed.source_record_id,
            legal_entity_id=context.legal_entity_id,
            event_type=EventType.ERP_JOURNAL_LINE,
            money=Money(parsed.amount_minor, parsed.currency),
            direction=parsed.direction,
            event_at=datetime.combine(parsed.posting_date, time(), tzinfo=UTC),
            value_date=parsed.posting_date,
            external_reference=parsed.external_reference or None,
            settlement_reference=parsed.external_reference or None,
            payment_reference=None,
            bank_utr=None,
            account_code=parsed.account_code,
            narration=parsed.narration or None,
            lineage=self._lineage(document, row),
            raw_fields=self._raw_fields(row),
            mapping_profile_version=profile.ref.versioned_id,
        )

    def group_journals(
        self, events: Sequence[CanonicalEvent]
    ) -> dict[str, tuple[CanonicalEvent, ...]]:
        groups: dict[str, list[CanonicalEvent]] = defaultdict(list)
        for event in events:
            if event.source_type is not self.source_type:
                raise ValueError("journal grouping received an event from another source")
            groups[event.source_record_id.rsplit(":", 1)[0]].append(event)
        return {journal: tuple(lines) for journal, lines in groups.items()}

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
