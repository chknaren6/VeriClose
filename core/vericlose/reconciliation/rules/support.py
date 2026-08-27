"""Interpretable candidate support scoring; never a source of proof."""

from __future__ import annotations

from difflib import SequenceMatcher

from core.vericlose.domain.events import CanonicalEvent
from core.vericlose.reconciliation.policy import ReconciliationPolicy
from core.vericlose.reconciliation.proposals import SupportFeature


def score_bank_group(
    group: tuple[CanonicalEvent, ...],
    *,
    expected_minor: int,
    settlement_reference: str,
    expected_utr: str | None,
    settlement_date,
    policy: ReconciliationPolicy,
) -> tuple[int, tuple[SupportFeature, ...]]:
    if not group:
        return 0, ()
    weights = policy.support_scoring_bps
    amount_equal = sum(event.money.amount_minor for event in group) == expected_minor
    references = {event.bank_utr for event in group if event.bank_utr}
    reference_equal = bool(expected_utr and references == {expected_utr})
    distances = tuple(
        abs(((event.value_date or event.event_at.date()) - settlement_date).days)
        for event in group
    )
    date_supported = max(distances) <= policy.dates.settlement_to_bank_max_days
    narration_text = " ".join(event.narration or "" for event in group).lower()
    narration_ratio = SequenceMatcher(
        None, settlement_reference.lower(), narration_text
    ).ratio()
    narration_score = round(weights["narration"] * narration_ratio)
    features = (
        SupportFeature("amount", weights["amount"] if amount_equal else 0, str(amount_equal)),
        SupportFeature(
            "reference", weights["reference"] if reference_equal else 0, str(reference_equal)
        ),
        SupportFeature("date", weights["date"] if date_supported else 0, str(max(distances))),
        SupportFeature("narration", narration_score, f"{narration_ratio:.4f}"),
    )
    return min(10_000, sum(feature.score_bps for feature in features)), features
