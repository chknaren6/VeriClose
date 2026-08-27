import csv
import json
from decimal import Decimal
from pathlib import Path

from core.vericlose.domain.enums import EventType, ProofLevel
from synthetic.base_case import SyntheticConfig
from synthetic.generate import build_synthetic_batch, generate


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_same_seed_is_byte_reproducible_and_other_seed_differs(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    different = tmp_path / "different"
    generate(SyntheticConfig(seed=42), first)
    generate(SyntheticConfig(seed=42), second)
    generate(SyntheticConfig(seed=43), different)
    assert _snapshot(first) == _snapshot(second)
    assert (first / "inputs/gateway.csv").read_bytes() != (
        different / "inputs/gateway.csv"
    ).read_bytes()


def test_generated_manifest_and_files_reconcile(tmp_path: Path) -> None:
    output = tmp_path / "seed-42"
    manifest = generate(SyntheticConfig(seed=42), output)
    inputs = output / "inputs"
    assert {path.name for path in inputs.iterdir()} == {"gateway.csv", "bank.csv", "erp_gl.csv"}
    assert manifest["control_totals"]["row_counts"]["total"] > 50

    with (inputs / "bank.csv").open(encoding="utf-8", newline="") as handle:
        bank_rows = list(csv.DictReader(handle))
    bank_credit_minor = sum(
        int(Decimal(row["credit_amount"]) * 100) for row in bank_rows
    )
    assert bank_credit_minor == manifest["control_totals"]["bank_credit_minor"]

    truth = json.loads((output / "private/ground_truth.json").read_text(encoding="utf-8"))
    assert len(truth["event_labels"]) == manifest["control_totals"]["row_counts"]["total"]


def test_runtime_source_files_do_not_leak_truth_labels(tmp_path: Path) -> None:
    output = tmp_path / "seed-42"
    generate(SyntheticConfig(seed=42), output)
    forbidden = {
        "case_id",
        "scenario",
        "expected_match",
        "expected_proof_level",
        "is_exception",
        "ground_truth",
    }
    for path in (output / "inputs").glob("*.csv"):
        with path.open(encoding="utf-8", newline="") as handle:
            header = set(next(csv.reader(handle)))
        assert header.isdisjoint(forbidden), path


def test_every_generated_proved_case_satisfies_accounting_invariants() -> None:
    batch = build_synthetic_batch(SyntheticConfig(seed=42))
    for truth_case in batch.truth.case_labels:
        if truth_case.expected_proof_level is not ProofLevel.PROVED:
            continue

        gateway = [row for row in batch.gateway_rows if row.case_id == truth_case.case_id]
        bank = [row for row in batch.bank_rows if row.case_id == truth_case.case_id]
        erp = [row for row in batch.erp_rows if row.case_id == truth_case.case_id]
        payment_minor = sum(
            row.amount_minor for row in gateway if row.event_type is EventType.PAYMENT
        )
        refund_minor = sum(
            row.amount_minor for row in gateway if row.event_type is EventType.REFUND
        )
        fee_minor = sum(row.amount_minor for row in gateway if row.event_type is EventType.FEE)
        tax_minor = sum(row.amount_minor for row in gateway if row.event_type is EventType.TAX)
        settlement_minor = sum(
            row.amount_minor for row in gateway if row.event_type is EventType.SETTLEMENT
        )
        expected_net = payment_minor - refund_minor - fee_minor - tax_minor

        assert settlement_minor == expected_net, truth_case.case_id
        assert sum(row.credit_minor - row.debit_minor for row in bank) == expected_net
        assert sum(row.debit_minor for row in erp) == sum(row.credit_minor for row in erp)
