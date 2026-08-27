"""Focused scenario injectors with one intentional accounting/data-quality effect each."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

from core.vericlose.domain.enums import (
    ActionType,
    EventType,
    ExceptionCategory,
    ProofLevel,
    Severity,
    SourceType,
)
from synthetic.models import BankRow, ErpRow, GatewayRow, GeneratedBatch
from synthetic.truth.models import CaseTruth, EventTruth, source_key


def mark_many_payments_one_settlement(batch: GeneratedBatch, case_id: str) -> GeneratedBatch:
    payments = [
        row
        for row in batch.gateway_rows
        if row.case_id == case_id and row.event_type is EventType.PAYMENT
    ]
    if len(payments) < 2:
        raise ValueError("many-to-one scenario requires at least two payment rows")
    return _set_outcome(
        batch,
        case_id,
        scenario="many_payments_one_settlement",
        proof_level=ProofLevel.PROVED,
        category=None,
        severity=None,
        next_action=ActionType.NO_ACTION,
        description="Multiple gateway payments validly aggregate into one settlement.",
    )


def inject_partial_settlement(batch: GeneratedBatch, case_id: str) -> GeneratedBatch:
    """Split one bank receipt into two tranches whose total remains exactly correct."""

    original = _single_bank_row(batch, case_id)
    first_minor = original.credit_minor // 2
    second_minor = original.credit_minor - first_minor
    replacement_rows = (
        replace(
            original,
            bank_record_id=f"{original.bank_record_id}_part_1",
            credit_minor=first_minor,
            narration=f"{original.narration} tranche 1",
        ),
        replace(
            original,
            bank_record_id=f"{original.bank_record_id}_part_2",
            value_date=original.value_date + timedelta(days=1),
            booking_date=original.booking_date + timedelta(days=1),
            credit_minor=second_minor,
            narration=f"{original.narration} tranche 2",
        ),
    )
    updated = replace(
        batch,
        bank_rows=tuple(row for row in batch.bank_rows if row.case_id != case_id)
        + replacement_rows,
    ).refresh_truth_members(case_id)
    return _set_outcome(
        updated,
        case_id,
        scenario="partial_settlement",
        proof_level=ProofLevel.PROVED,
        category=None,
        severity=None,
        next_action=ActionType.NO_ACTION,
        valid_timing_difference=True,
        description="Two valid bank tranches sum to the gateway and ERP settlement amount.",
    )


def inject_refund_in_later_settlement(batch: GeneratedBatch, case_id: str) -> GeneratedBatch:
    """Add a prior-payment refund to this settlement while keeping every ledger balanced."""

    context = batch.context(case_id)
    refund_minor = min(2_500, max(100, context.gross_minor // 20))
    new_net = context.net_minor - refund_minor
    refund = GatewayRow(
        case_id=case_id,
        gateway_event_id=f"gwe_refund_{case_id}",
        event_type=EventType.REFUND,
        transaction_id=f"prior_payment_{case_id}",
        settlement_id=context.settlement_id,
        amount_minor=refund_minor,
        currency="INR",
        event_at=next(
            row.event_at for row in batch.gateway_rows if row.case_id == case_id
        ),
        status="processed",
        reference=f"refund_{case_id}",
        narration="Synthetic prior-payment refund deducted in a later settlement",
    )
    gateway_rows = tuple(
        replace(row, amount_minor=new_net)
        if row.case_id == case_id and row.event_type is EventType.SETTLEMENT
        else row
        for row in batch.gateway_rows
    ) + (refund,)
    bank_rows = tuple(
        replace(row, credit_minor=new_net) if row.case_id == case_id else row
        for row in batch.bank_rows
    )
    erp_rows = tuple(
        _reduce_erp_for_refund(row, refund_minor)
        if row.case_id == case_id
        else row
        for row in batch.erp_rows
    )
    cases = tuple(
        replace(context, refund_minor=refund_minor, net_minor=new_net)
        if context.case_id == case_id
        else context
        for context in batch.cases
    )
    updated = replace(
        batch,
        gateway_rows=gateway_rows,
        bank_rows=bank_rows,
        erp_rows=erp_rows,
        cases=cases,
    ).refresh_truth_members(case_id)
    return _set_outcome(
        updated,
        case_id,
        scenario="refund_later_settlement",
        proof_level=ProofLevel.PROVED,
        category=None,
        severity=None,
        next_action=ActionType.NO_ACTION,
        valid_timing_difference=True,
        description="A refund from an earlier payment is correctly deducted later.",
    )


def inject_working_day_shift(batch: GeneratedBatch, case_id: str) -> GeneratedBatch:
    bank_rows = tuple(
        replace(
            row,
            value_date=row.value_date + timedelta(days=2),
            booking_date=row.booking_date + timedelta(days=2),
        )
        if row.case_id == case_id
        else row
        for row in batch.bank_rows
    )
    return _set_outcome(
        replace(batch, bank_rows=bank_rows),
        case_id,
        scenario="working_day_shift",
        proof_level=ProofLevel.PROVED,
        category=None,
        severity=None,
        next_action=ActionType.NO_ACTION,
        valid_timing_difference=True,
        description="Bank value date is two days later but inside the allowed policy window.",
    )


def inject_mistyped_reference(batch: GeneratedBatch, case_id: str) -> GeneratedBatch:
    bank_rows = tuple(
        replace(row, utr=f"{row.utr[:-1]}X") if row.case_id == case_id else row
        for row in batch.bank_rows
    )
    return _set_outcome(
        replace(batch, bank_rows=bank_rows),
        case_id,
        scenario="mistyped_reference",
        proof_level=ProofLevel.SUPPORTED,
        category=ExceptionCategory.REFERENCE,
        severity=Severity.MEDIUM,
        next_action=ActionType.CLARIFICATION_REQUEST,
        description="Amount/date support the candidate, but the bank UTR is mistyped.",
    )


def inject_duplicate_erp_posting(batch: GeneratedBatch, case_id: str) -> GeneratedBatch:
    originals = tuple(row for row in batch.erp_rows if row.case_id == case_id)
    duplicates = tuple(
        replace(
            row,
            erp_record_id=f"{row.erp_record_id}_duplicate",
            journal_id=f"{row.journal_id}_duplicate",
            narration=f"{row.narration} duplicate posting",
        )
        for row in originals
    )
    updated = replace(batch, erp_rows=batch.erp_rows + duplicates).refresh_truth_members(case_id)
    return _set_outcome(
        updated,
        case_id,
        scenario="duplicate_erp_posting",
        proof_level=ProofLevel.CONTRADICTED,
        category=ExceptionCategory.DUPLICATE,
        severity=Severity.CRITICAL,
        next_action=ActionType.JOURNAL_EXPORT,
        description="A second balanced ERP journal duplicates the same settlement posting.",
    )


def inject_missing_bank_credit(batch: GeneratedBatch, case_id: str) -> GeneratedBatch:
    updated = replace(
        batch,
        bank_rows=tuple(row for row in batch.bank_rows if row.case_id != case_id),
    ).refresh_truth_members(case_id)
    return _set_outcome(
        updated,
        case_id,
        scenario="missing_bank_credit",
        proof_level=ProofLevel.SUPPORTED,
        category=ExceptionCategory.MISSING_SOURCE,
        severity=Severity.HIGH,
        next_action=ActionType.CLARIFICATION_REQUEST,
        description="Gateway and ERP agree, but required bank receipt evidence is absent.",
    )


def inject_missing_erp_posting(batch: GeneratedBatch, case_id: str) -> GeneratedBatch:
    updated = replace(
        batch,
        erp_rows=tuple(row for row in batch.erp_rows if row.case_id != case_id),
    ).refresh_truth_members(case_id)
    return _set_outcome(
        updated,
        case_id,
        scenario="missing_erp_posting",
        proof_level=ProofLevel.SUPPORTED,
        category=ExceptionCategory.MISSING_SOURCE,
        severity=Severity.HIGH,
        next_action=ActionType.JOURNAL_EXPORT,
        description="Gateway and bank agree, but the ERP journal is missing.",
    )


def inject_incorrect_fee_or_tax(batch: GeneratedBatch, case_id: str) -> GeneratedBatch:
    gateway_rows = tuple(
        replace(row, amount_minor=row.amount_minor + 127)
        if row.case_id == case_id and row.event_type is EventType.FEE
        else row
        for row in batch.gateway_rows
    )
    return _set_outcome(
        replace(batch, gateway_rows=gateway_rows),
        case_id,
        scenario="incorrect_fee_or_tax",
        proof_level=ProofLevel.CONTRADICTED,
        category=ExceptionCategory.AMOUNT,
        severity=Severity.HIGH,
        next_action=ActionType.CLARIFICATION_REQUEST,
        description="Gateway fee components no longer reconcile to settlement and ERP totals.",
    )


def inject_amount_mismatch(batch: GeneratedBatch, case_id: str) -> GeneratedBatch:
    bank_rows = tuple(
        replace(row, credit_minor=row.credit_minor + 101)
        if row.case_id == case_id
        else row
        for row in batch.bank_rows
    )
    return _set_outcome(
        replace(batch, bank_rows=bank_rows),
        case_id,
        scenario="amount_mismatch",
        proof_level=ProofLevel.CONTRADICTED,
        category=ExceptionCategory.AMOUNT,
        severity=Severity.CRITICAL,
        next_action=ActionType.CLARIFICATION_REQUEST,
        description="Bank receipt differs from the gateway and ERP amount by 101 paise.",
    )


def inject_unbalanced_erp_journal(batch: GeneratedBatch, case_id: str) -> GeneratedBatch:
    changed = False
    rows: list[ErpRow] = []
    for row in batch.erp_rows:
        if row.case_id == case_id and row.debit_minor and not changed:
            rows.append(replace(row, debit_minor=row.debit_minor + 99))
            changed = True
        else:
            rows.append(row)
    return _set_outcome(
        replace(batch, erp_rows=tuple(rows)),
        case_id,
        scenario="unbalanced_erp_journal",
        proof_level=ProofLevel.INVALID_INPUT,
        category=ExceptionCategory.ACCOUNTING,
        severity=Severity.CRITICAL,
        next_action=ActionType.CORRECTED_DATA_IMPORT,
        description="ERP journal debits exceed credits by 99 paise.",
    )


def inject_equal_amount_ambiguity(batch: GeneratedBatch, case_id: str) -> GeneratedBatch:
    original = _single_bank_row(batch, case_id)
    candidate = replace(
        original,
        bank_record_id=f"{original.bank_record_id}_candidate",
        utr=f"ALT{original.utr}",
        narration="Synthetic equal-amount competing bank candidate",
    )
    updated = replace(
        batch, bank_rows=batch.bank_rows + (candidate,)
    ).refresh_truth_members(case_id)
    return _set_outcome(
        updated,
        case_id,
        scenario="equal_amount_ambiguity",
        proof_level=ProofLevel.AMBIGUOUS,
        category=ExceptionCategory.AMBIGUOUS,
        severity=Severity.HIGH,
        next_action=ActionType.MANUAL_REVIEW,
        description="Two bank rows have equal amount/date support and neither is safely unique.",
    )


def inject_orphan_bank_credit(batch: GeneratedBatch, ordinal: int) -> GeneratedBatch:
    case_id = f"case_orphan_{batch.seed:04d}_{ordinal:02d}"
    anchor = batch.bank_rows[0]
    orphan = replace(
        anchor,
        case_id=case_id,
        bank_record_id=f"bnk_orphan_{batch.seed:04d}_{ordinal:02d}",
        credit_minor=73_421,
        utr=f"ORPHAN{batch.seed:04d}{ordinal:04d}",
        narration="Synthetic bank credit without gateway or ERP evidence",
    )
    event = EventTruth(SourceType.BANK, orphan.bank_record_id, case_id, "BANK_RECEIPT")
    case = CaseTruth(
        case_id=case_id,
        scenario="orphan_bank_credit",
        expected_member_keys=(source_key(SourceType.BANK, orphan.bank_record_id),),
        expected_proof_level=ProofLevel.AMBIGUOUS,
        expected_exception_category=ExceptionCategory.MISSING_SOURCE,
        expected_severity=Severity.HIGH,
        expected_next_action=ActionType.CLARIFICATION_REQUEST,
        valid_timing_difference=False,
        description="Bank receipt has no corresponding gateway settlement or ERP journal.",
    )
    return replace(
        batch,
        bank_rows=batch.bank_rows + (orphan,),
        truth=batch.truth.add_case(case, (event,)),
    )


def _single_bank_row(batch: GeneratedBatch, case_id: str) -> BankRow:
    rows = tuple(row for row in batch.bank_rows if row.case_id == case_id)
    if len(rows) != 1:
        raise ValueError(f"scenario requires one bank row for {case_id}; found {len(rows)}")
    return rows[0]


def _reduce_erp_for_refund(row: ErpRow, refund_minor: int) -> ErpRow:
    if row.account_code == "110000":
        return replace(row, debit_minor=row.debit_minor - refund_minor)
    if row.account_code == "120000":
        return replace(row, credit_minor=row.credit_minor - refund_minor)
    return row


def _set_outcome(
    batch: GeneratedBatch,
    case_id: str,
    *,
    scenario: str,
    proof_level: ProofLevel,
    category: ExceptionCategory | None,
    severity: Severity | None,
    next_action: ActionType,
    description: str,
    valid_timing_difference: bool = False,
) -> GeneratedBatch:
    current = batch.truth.case(case_id)
    updated = current.with_outcome(
        scenario=scenario,
        proof_level=proof_level,
        category=category,
        severity=severity,
        next_action=next_action,
        valid_timing_difference=valid_timing_difference,
        description=description,
    )
    return replace(batch, truth=batch.truth.replace_case(updated))


ANOMALY_INJECTORS = (
    inject_mistyped_reference,
    inject_duplicate_erp_posting,
    inject_missing_bank_credit,
    inject_missing_erp_posting,
    inject_incorrect_fee_or_tax,
    inject_amount_mismatch,
    inject_unbalanced_erp_journal,
    inject_equal_amount_ambiguity,
)
