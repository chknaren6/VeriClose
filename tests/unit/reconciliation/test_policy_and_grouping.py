from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from core.vericlose.domain.enums import Direction, EventType, SourceType
from core.vericlose.domain.events import CanonicalEvent, RawRowRef
from core.vericlose.domain.money import Money
from core.vericlose.reconciliation.context import ReconciliationContext
from core.vericlose.reconciliation.policy import load_policy
from core.vericlose.reconciliation.rules.grouping import amount_groups

POLICY_PATH = Path("config/policies/razorpay_inr_v1.yaml")


def test_versioned_policy_loads_with_strict_account_and_auto_clear_contract() -> None:
    policy = load_policy(POLICY_PATH)
    assert policy.versioned_id == "razorpay_inr_v1@1.0.0"
    assert policy.currency == "INR"
    assert policy.role("bank").account_codes == frozenset({"110000"})
    assert policy.role("bank").direction is Direction.DEBIT
    assert "BANK_RECEIPT_UNIQUE" in policy.auto_clear_required_checks
    with pytest.raises(TypeError):
        policy.tolerances_minor["bank_receipt"] = 99  # type: ignore[index]


def test_policy_rejects_unknown_root_keys(tmp_path: Path) -> None:
    payload = POLICY_PATH.read_text(encoding="utf-8") + "\nunsafe_expression: eval(amount)\n"
    path = tmp_path / "unsafe.yaml"
    path.write_text(payload, encoding="utf-8")
    with pytest.raises(ValueError, match="unknown"):
        load_policy(path)


def test_bounded_grouping_is_deterministic_and_reports_ambiguity() -> None:
    policy = load_policy(POLICY_PATH)
    events = tuple(
        replace(
            _event(),
            event_id=f"bank-{index}",
            source_record_id=f"bank-{index}",
            money=Money(amount, "INR"),
        )
        for index, amount in enumerate((40, 60, 100), start=1)
    )
    result = amount_groups(tuple(reversed(events)), 100, policy.grouping)
    assert len(result.groups) == 2
    assert tuple(tuple(event.event_id for event in group) for group in result.groups) == (
        ("bank-3",),
        ("bank-1", "bank-2"),
    )

    bounded = amount_groups(events * 5, 100, policy.grouping)
    assert bounded.bounded_out
    assert bounded.groups == ()


def test_context_rejects_cross_currency_and_cross_entity_inputs_before_matching() -> None:
    policy = load_policy(POLICY_PATH)
    with pytest.raises(ValueError, match="currency"):
        ReconciliationContext.build(
            (_event(), replace(_event(), event_id="usd", money=Money(100, "USD"))),
            policy,
        )
    with pytest.raises(ValueError, match="one run and one legal entity"):
        ReconciliationContext.build(
            (_event(), replace(_event(), event_id="other", legal_entity_id="other")),
            policy,
        )


def _event() -> CanonicalEvent:
    return CanonicalEvent(
        "bank",
        "run",
        SourceType.BANK,
        "bank",
        "merchant",
        EventType.BANK_CREDIT,
        Money(100, "INR"),
        Direction.CREDIT,
        datetime(2026, 4, 1, tzinfo=UTC),
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        RawRowRef("bank-file", "a" * 64, "rows", 2, "b" * 64),
        (),
        "bank@1",
    )
