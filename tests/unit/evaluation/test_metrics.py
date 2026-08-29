from evaluation.metrics import EvaluationMetrics, MetricCounts


def test_metric_denominators_and_empty_set_conventions_are_explicit() -> None:
    metrics = EvaluationMetrics.from_counts(
        MetricCounts(
            truth_event_count=3,
            correct_event_count=2,
            truth_case_count=3,
            correct_case_count=2,
            predicted_auto_clear_count=2,
            correct_auto_clear_count=1,
            expected_exception_count=2,
            recalled_exception_count=1,
            false_clear_count=1,
        )
    )
    assert metrics.event_accuracy_bps == 6_666
    assert metrics.case_accuracy_bps == 6_666
    assert metrics.auto_clear_precision_bps == 5_000
    assert metrics.exception_recall_bps == 5_000
    assert metrics.false_clear_rate_bps == 5_000

    empty = EvaluationMetrics.from_counts(MetricCounts())
    assert empty.auto_clear_precision_bps == 10_000
    assert empty.exception_recall_bps == 10_000
    assert empty.false_clear_rate_bps == 0


def test_counts_aggregate_before_rates_are_calculated() -> None:
    first = MetricCounts(
        truth_case_count=1,
        correct_case_count=1,
        predicted_auto_clear_count=1,
        correct_auto_clear_count=1,
    )
    second = MetricCounts(
        truth_case_count=9,
        correct_case_count=0,
        predicted_auto_clear_count=9,
        correct_auto_clear_count=0,
        false_clear_count=9,
    )
    aggregate = EvaluationMetrics.from_counts(first + second)
    assert aggregate.case_accuracy_bps == 1_000
    assert aggregate.auto_clear_precision_bps == 1_000
    assert aggregate.false_clear_rate_bps == 9_000
