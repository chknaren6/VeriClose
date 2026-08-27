import csv
from pathlib import Path

FIXTURE_ROOT = Path("tests/fixtures/schema")


def _header(filename: str) -> tuple[str, ...]:
    with (FIXTURE_ROOT / filename).open(encoding="utf-8", newline="") as handle:
        return tuple(next(csv.reader(handle)))


def test_gateway_fixture_contract() -> None:
    expected = (
        "gateway_event_id",
        "event_type",
        "transaction_id",
        "settlement_id",
        "amount_minor",
        "currency",
        "event_at",
        "status",
        "reference",
        "narration",
    )
    assert _header("gateway_valid.csv") == expected
    assert _header("gateway_invalid.csv") == expected


def test_both_bank_layouts_are_explicit() -> None:
    debit_credit = _header("bank_debit_credit_valid.csv")
    signed = _header("bank_signed_valid.csv")
    assert {"debit_amount", "credit_amount"} <= set(debit_credit)
    assert "signed_amount" in signed
    assert "signed_amount" not in debit_credit


def test_erp_fixture_contract_and_intentional_invalid_rows() -> None:
    expected = (
        "journal_id",
        "line_number",
        "posting_date",
        "account_code",
        "debit_amount",
        "credit_amount",
        "currency",
        "external_reference",
        "narration",
    )
    assert _header("erp_gl_valid.csv") == expected
    assert _header("erp_gl_invalid.csv") == expected
    invalid_text = (FIXTURE_ROOT / "erp_gl_invalid.csv").read_text(encoding="utf-8")
    assert invalid_text.count("jrn_bad,1") == 2
