from collections import defaultdict

import pytest

from core.vericlose.domain.enums import ExceptionCategory, ProofLevel
from synthetic.base_case import SyntheticConfig, generate_clean_batch
from synthetic.scenarios.injectors import (
    inject_amount_mismatch,
    inject_duplicate_erp_posting,
    inject_equal_amount_ambiguity,
    inject_incorrect_fee_or_tax,
    inject_missing_bank_credit,
    inject_missing_erp_posting,
    inject_mistyped_reference,
    inject_orphan_bank_credit,
    inject_partial_settlement,
    inject_refund_in_later_settlement,
    inject_unbalanced_erp_journal,
    inject_working_day_shift,
    mark_many_payments_one_settlement,
)


def _batch():
    return generate_clean_batch(
        SyntheticConfig(seed=42, payments=70, settlements=14, exception_rate=0)
    )


@pytest.mark.parametrize(
    ("injector", "proof_level", "category"),
    [
        (inject_mistyped_reference, ProofLevel.SUPPORTED, ExceptionCategory.REFERENCE),
        (inject_duplicate_erp_posting, ProofLevel.CONTRADICTED, ExceptionCategory.DUPLICATE),
        (inject_missing_bank_credit, ProofLevel.SUPPORTED, ExceptionCategory.MISSING_SOURCE),
        (inject_missing_erp_posting, ProofLevel.SUPPORTED, ExceptionCategory.MISSING_SOURCE),
        (inject_incorrect_fee_or_tax, ProofLevel.CONTRADICTED, ExceptionCategory.AMOUNT),
        (inject_amount_mismatch, ProofLevel.CONTRADICTED, ExceptionCategory.AMOUNT),
        (inject_unbalanced_erp_journal, ProofLevel.INVALID_INPUT, ExceptionCategory.ACCOUNTING),
        (inject_equal_amount_ambiguity, ProofLevel.AMBIGUOUS, ExceptionCategory.AMBIGUOUS),
    ],
)
def test_anomaly_injectors_record_expected_safe_outcome(
    injector,
    proof_level: ProofLevel,
    category: ExceptionCategory,
) -> None:
    batch = _batch()
    case_id = batch.cases[5].case_id
    updated = injector(batch, case_id)
    truth = updated.truth.case(case_id)
    assert truth.expected_proof_level is proof_level
    assert truth.expected_exception_category is category
    assert updated.rows_for_case(batch.cases[0].case_id) == batch.rows_for_case(
        batch.cases[0].case_id
    )


def test_valid_complexity_is_not_labelled_as_error() -> None:
    batch = _batch()
    many = mark_many_payments_one_settlement(batch, batch.cases[0].case_id)
    partial = inject_partial_settlement(many, batch.cases[1].case_id)
    refunded = inject_refund_in_later_settlement(partial, batch.cases[2].case_id)
    shifted = inject_working_day_shift(refunded, batch.cases[3].case_id)
    for case_id in [context.case_id for context in batch.cases[:4]]:
        truth = shifted.truth.case(case_id)
        assert truth.expected_proof_level is ProofLevel.PROVED
        assert truth.expected_exception_category is None

    original_net = batch.context(batch.cases[1].case_id).net_minor
    partial_rows = [row for row in shifted.bank_rows if row.case_id == batch.cases[1].case_id]
    assert len(partial_rows) == 2
    assert sum(row.credit_minor for row in partial_rows) == original_net


def test_refund_scenario_keeps_erp_journal_balanced() -> None:
    batch = _batch()
    case_id = batch.cases[2].case_id
    updated = inject_refund_in_later_settlement(batch, case_id)
    debits: dict[str, int] = defaultdict(int)
    credits: dict[str, int] = defaultdict(int)
    for row in updated.erp_rows:
        if row.case_id == case_id:
            debits[row.journal_id] += row.debit_minor
            credits[row.journal_id] += row.credit_minor
    assert debits == credits


def test_orphan_creates_a_new_honestly_unresolved_case() -> None:
    batch = _batch()
    updated = inject_orphan_bank_credit(batch, ordinal=1)
    orphan = updated.truth.case("case_orphan_0042_01")
    assert orphan.expected_proof_level is ProofLevel.AMBIGUOUS
    assert len(orphan.expected_member_keys) == 1
