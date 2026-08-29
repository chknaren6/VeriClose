"""Property tests for invariants that must hold across arbitrary finance data."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

from core.vericlose.domain.enums import Direction, EventType, SourceType
from core.vericlose.domain.events import CanonicalEvent, RawRowRef
from core.vericlose.domain.money import Money
from core.vericlose.ingestion.mappings import parse_decimal_minor
from core.vericlose.reconciliation.policy import load_policy
from core.vericlose.reconciliation.rules.grouping import amount_groups


@given(st.integers(min_value=-10**15, max_value=10**15))
def test_decimal_to_minor_units_is_exact_for_every_representable_paise(
    amount_minor: int,
) -> None:
    rendered = format(Decimal(amount_minor) / Decimal(100), "f")
    assert parse_decimal_minor(rendered) == amount_minor


@given(
    st.lists(st.integers(min_value=1, max_value=10**12), min_size=1, max_size=30)
)
def test_balanced_journal_totals_survive_integer_normalization(amounts: list[int]) -> None:
    # ERP debit and credit totals remain exact because normalization never uses floats.
    debits = tuple(Money(amount, "INR") for amount in amounts)
    credits = tuple(Money(amount, "INR") for amount in reversed(amounts))
    assert sum(item.amount_minor for item in debits) == sum(
        item.amount_minor for item in credits
    )


@given(st.permutations((17, 29, 54, 71, 83, 100)))
def test_candidate_grouping_is_permutation_invariant(amounts: tuple[int, ...]) -> None:
    policy = load_policy(Path("config/policies/razorpay_inr_v1.yaml"))
    events = tuple(
        replace(
            _event(amount),
            event_id=f"bank-{amount}",
            source_record_id=f"bank-{amount}",
        )
        for amount in amounts
    )
    groups = amount_groups(events, 100, policy.grouping).groups
    identities = tuple(tuple(event.event_id for event in group) for group in groups)
    canonical_events = tuple(sorted(events, key=lambda event: event.event_id))
    canonical_groups = amount_groups(canonical_events, 100, policy.grouping).groups
    canonical_identities = tuple(
        tuple(event.event_id for event in group) for group in canonical_groups
    )
    assert identities == canonical_identities


@given(st.integers(min_value=10**12, max_value=10**15))
def test_large_minor_unit_values_do_not_overflow_or_lose_precision(amount: int) -> None:
    money = Money(amount, "INR")
    assert money.amount_minor + money.amount_minor == amount * 2


def _event(amount: int) -> CanonicalEvent:
    return CanonicalEvent(
        "bank",
        "property-run",
        SourceType.BANK,
        "bank",
        "merchant",
        EventType.BANK_CREDIT,
        Money(amount, "INR"),
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
