"""Auditable count aggregation and documented evaluation denominators."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MetricCounts:
    truth_event_count: int = 0
    correct_event_count: int = 0
    truth_case_count: int = 0
    correct_case_count: int = 0
    predicted_auto_clear_count: int = 0
    correct_auto_clear_count: int = 0
    expected_exception_count: int = 0
    recalled_exception_count: int = 0
    false_clear_count: int = 0
    wrong_exception_classification_count: int = 0

    def __add__(self, other: MetricCounts) -> MetricCounts:
        return MetricCounts(
            **{
                field: getattr(self, field) + getattr(other, field)
                for field in self.__dataclass_fields__
            }
        )


@dataclass(frozen=True, slots=True)
class EvaluationMetrics:
    counts: MetricCounts
    event_accuracy_bps: int
    case_accuracy_bps: int
    auto_clear_precision_bps: int
    exception_recall_bps: int
    false_clear_rate_bps: int

    @classmethod
    def from_counts(cls, counts: MetricCounts) -> EvaluationMetrics:
        return cls(
            counts,
            _rate(counts.correct_event_count, counts.truth_event_count),
            _rate(counts.correct_case_count, counts.truth_case_count),
            _rate(
                counts.correct_auto_clear_count,
                counts.predicted_auto_clear_count,
                empty_value=10_000,
            ),
            _rate(
                counts.recalled_exception_count,
                counts.expected_exception_count,
                empty_value=10_000,
            ),
            _rate(
                counts.false_clear_count,
                counts.predicted_auto_clear_count,
                empty_value=0,
            ),
        )


def _rate(numerator: int, denominator: int, *, empty_value: int = 0) -> int:
    """Return basis points using integer arithmetic; empty precision/recall is vacuously safe."""

    if numerator < 0 or denominator < 0 or numerator > denominator:
        raise ValueError("metric counts require 0 <= numerator <= denominator")
    return empty_value if denominator == 0 else numerator * 10_000 // denominator
