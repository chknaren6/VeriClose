from collections import defaultdict

from core.vericlose.domain.enums import EventType, ProofLevel
from synthetic.base_case import SyntheticConfig, generate_clean_batch, seeded_rng


def test_clean_batch_has_requested_payments_and_balanced_journals() -> None:
    batch = generate_clean_batch(SyntheticConfig(seed=7, payments=70, settlements=14))
    payments = [row for row in batch.gateway_rows if row.event_type is EventType.PAYMENT]
    assert len(payments) == 70
    assert all(case.expected_proof_level is ProofLevel.PROVED for case in batch.truth.case_labels)

    debits: dict[str, int] = defaultdict(int)
    credits: dict[str, int] = defaultdict(int)
    for row in batch.erp_rows:
        debits[row.journal_id] += row.debit_minor
        credits[row.journal_id] += row.credit_minor
    assert debits == credits


def test_namespaced_rng_is_reproducible_and_independent() -> None:
    first_rng = seeded_rng(42, "amounts")
    second_rng = seeded_rng(42, "amounts")
    first = [first_rng.randint(1, 1_000) for _ in range(2)]
    second = [second_rng.randint(1, 1_000) for _ in range(2)]
    other_namespace = seeded_rng(42, "identifiers").randint(1, 1_000)
    assert first == second
    assert first[0] != other_namespace


def test_control_totals_reconcile_clean_bank_and_erp() -> None:
    batch = generate_clean_batch(SyntheticConfig(seed=9, payments=70, settlements=14))
    totals = batch.control_totals()
    assert totals["bank_credit_minor"] == totals["erp_debit_minor"] - sum(
        row.debit_minor for row in batch.erp_rows if row.account_code != "110000"
    )
    assert totals["erp_debit_minor"] == totals["erp_credit_minor"]
