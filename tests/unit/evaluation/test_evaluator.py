from core.vericlose.domain.enums import (
    ActionType,
    ExceptionCategory,
    ProofLevel,
    Severity,
    SourceType,
)
from evaluation.benchmark import SafetyThresholds, evaluate_thresholds
from evaluation.evaluate import PredictedCase, evaluate_predictions
from synthetic.truth.models import CaseTruth, EventTruth, TruthDataset


def _truth() -> TruthDataset:
    cases = (
        CaseTruth(
            "case-clean",
            "clean",
            ("GATEWAY:clean",),
            ProofLevel.PROVED,
            None,
            None,
            ActionType.NO_ACTION,
            False,
            "clean",
        ),
        CaseTruth(
            "case-missing",
            "missing_bank",
            ("GATEWAY:missing",),
            ProofLevel.SUPPORTED,
            ExceptionCategory.MISSING_SOURCE,
            Severity.HIGH,
            ActionType.CLARIFICATION_REQUEST,
            False,
            "missing",
        ),
        CaseTruth(
            "case-unsafe",
            "amount_mismatch",
            ("GATEWAY:unsafe",),
            ProofLevel.CONTRADICTED,
            ExceptionCategory.AMOUNT,
            Severity.CRITICAL,
            ActionType.CLARIFICATION_REQUEST,
            False,
            "unsafe",
        ),
    )
    events = tuple(
        EventTruth(SourceType.GATEWAY, source_id, case.case_id, "GATEWAY_SETTLEMENT")
        for source_id, case in zip(("clean", "missing", "unsafe"), cases, strict=True)
    )
    return TruthDataset("1.0", 7, events, cases)


def test_evaluator_separates_false_clear_from_wrong_exception_classification() -> None:
    predictions = (
        PredictedCase(
            "decision-clean",
            ("event-clean",),
            frozenset({"GATEWAY:clean"}),
            ProofLevel.PROVED,
            True,
            None,
            None,
            None,
        ),
        PredictedCase(
            "decision-missing",
            ("event-missing",),
            frozenset({"GATEWAY:missing"}),
            ProofLevel.SUPPORTED,
            False,
            ExceptionCategory.MISSING_SOURCE,
            Severity.HIGH,
            ActionType.CLARIFICATION_REQUEST,
        ),
        PredictedCase(
            "decision-unsafe",
            ("event-unsafe",),
            frozenset({"GATEWAY:unsafe"}),
            ProofLevel.PROVED,
            True,
            None,
            None,
            None,
        ),
    )
    report = evaluate_predictions("run-7", _truth(), predictions)
    counts = report.metrics.counts
    assert counts.false_clear_count == 1
    assert counts.wrong_exception_classification_count == 1
    assert report.metrics.auto_clear_precision_bps == 5_000
    assert report.metrics.exception_recall_bps == 5_000
    assert report.incorrect_event_ids == ("GATEWAY:unsafe",)
    assert ("CONTRADICTED", "PROVED", 1) in report.confusion_matrix

    violations = evaluate_thresholds(
        report.metrics,
        SafetyThresholds(10_000, 10_000, 0, 0),
    )
    assert {item.split(":", 1)[0] for item in violations} == {
        "AUTO_CLEAR_PRECISION_BELOW_MINIMUM",
        "EXCEPTION_RECALL_BELOW_MINIMUM",
        "FALSE_CLEAR_COUNT_ABOVE_MAXIMUM",
        "FALSE_CLEAR_RATE_ABOVE_MAXIMUM",
    }


def test_wrong_exception_category_does_not_count_as_a_false_clear() -> None:
    truth = _truth()
    prediction = PredictedCase(
        "decision-missing",
        ("event-missing",),
        frozenset({"GATEWAY:missing"}),
        ProofLevel.SUPPORTED,
        False,
        ExceptionCategory.REFERENCE,
        Severity.MEDIUM,
        ActionType.CLARIFICATION_REQUEST,
    )
    report = evaluate_predictions(
        "run-wrong-category",
        TruthDataset("1.0", 7, truth.event_labels[1:2], truth.case_labels[1:2]),
        (prediction,),
    )
    assert report.metrics.counts.false_clear_count == 0
    assert report.metrics.counts.wrong_exception_classification_count == 1
    assert report.metrics.exception_recall_bps == 10_000
