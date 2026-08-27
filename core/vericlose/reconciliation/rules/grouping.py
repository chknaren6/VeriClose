"""Deterministic bounded subset search used only where policy permits aggregation."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from core.vericlose.domain.events import CanonicalEvent
from core.vericlose.reconciliation.policy import GroupingPolicy


@dataclass(frozen=True, slots=True)
class GroupingResult:
    groups: tuple[tuple[CanonicalEvent, ...], ...]
    bounded_out: bool


def amount_groups(
    candidates: tuple[CanonicalEvent, ...],
    target_minor: int,
    policy: GroupingPolicy,
) -> GroupingResult:
    """Return up to the ambiguity threshold; never guess after a configured bound."""

    ordered = tuple(sorted(candidates, key=lambda event: event.event_id))
    if len(ordered) > policy.max_candidates:
        return GroupingResult((), True)
    found: list[tuple[CanonicalEvent, ...]] = []
    for size in range(1, min(policy.max_group_size, len(ordered)) + 1):
        for group in combinations(ordered, size):
            if sum(event.money.amount_minor for event in group) == target_minor:
                found.append(group)
                if len(found) >= policy.max_valid_groups:
                    return GroupingResult(tuple(found), False)
    return GroupingResult(tuple(found), False)
