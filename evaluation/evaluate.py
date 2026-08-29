"""Compare stored runtime outputs with evaluation-only hidden truth."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from core.vericlose.domain.decisions import ReconciliationDecision
from core.vericlose.domain.enums import (
    ActionType,
    ExceptionCategory,
    ProofLevel,
    Severity,
)
from core.vericlose.domain.events import CanonicalEvent
from core.vericlose.domain.exceptions import ExceptionCase
from core.vericlose.infrastructure.duckdb import DuckDBUnitOfWork
from evaluation.metrics import EvaluationMetrics, MetricCounts
from synthetic.truth.models import CaseTruth, TruthDataset, source_key


@dataclass(frozen=True, slots=True)
class PredictedCase:
    decision_id: str
    event_ids: tuple[str, ...]
    member_keys: frozenset[str]
    proof_level: ProofLevel
    auto_cleared: bool
    exception_category: ExceptionCategory | None
    exception_severity: Severity | None
    recommended_action: ActionType | None


@dataclass(frozen=True, slots=True)
class EventEvaluation:
    event_key: str
    expected_case_id: str | None
    predicted_decision_id: str | None
    membership_correct: bool
    disposition_correct: bool

    @property
    def correct(self) -> bool:
        return self.membership_correct and self.disposition_correct


@dataclass(frozen=True, slots=True)
class CaseEvaluation:
    expected_case_id: str
    scenario: str
    predicted_decision_id: str | None
    expected_proof_level: ProofLevel
    predicted_proof_level: ProofLevel | None
    group_correct: bool
    proof_correct: bool
    exception_classification_correct: bool
    false_clear: bool
    exception_recalled: bool
    expected_member_keys: tuple[str, ...]
    predicted_member_keys: tuple[str, ...]

    @property
    def correct(self) -> bool:
        return self.group_correct and self.proof_correct and self.exception_classification_correct


@dataclass(frozen=True, slots=True)
class ScenarioResult:
    scenario: str
    case_count: int
    correct_case_count: int
    false_clear_count: int


@dataclass(frozen=True, slots=True)
class EvaluationReport:
    run_id: str
    seed: int
    metrics: EvaluationMetrics
    event_results: tuple[EventEvaluation, ...]
    case_results: tuple[CaseEvaluation, ...]
    scenario_results: tuple[ScenarioResult, ...]
    confusion_matrix: tuple[tuple[str, str, int], ...]
    incorrect_event_ids: tuple[str, ...]
    unmatched_prediction_ids: tuple[str, ...]


def evaluate_stored_run(
    database_path: Path,
    run_id: str,
    truth_path: Path,
) -> EvaluationReport:
    truth = TruthDataset.from_dict(json.loads(truth_path.read_text(encoding="utf-8")))
    with DuckDBUnitOfWork(database_path) as repositories:
        events = repositories.events.list_for_run(run_id)
        decisions = repositories.decisions.list_for_run(run_id)
        exceptions = repositories.exceptions.list_for_run(run_id)
    predictions = build_predictions(events, decisions, exceptions)
    return evaluate_predictions(run_id, truth, predictions)


def build_predictions(
    events: tuple[CanonicalEvent, ...],
    decisions: tuple[ReconciliationDecision, ...],
    exceptions: tuple[ExceptionCase, ...],
) -> tuple[PredictedCase, ...]:
    event_by_id = {event.event_id: event for event in events}
    exception_by_events = {
        frozenset(
            link.event_id for link in exception.evidence_links if link.event_id is not None
        ): exception
        for exception in exceptions
    }
    predictions: list[PredictedCase] = []
    for decision in decisions:
        missing = set(decision.event_ids) - event_by_id.keys()
        if missing:
            raise ValueError(
                f"decision {decision.decision_id} cites missing events: {sorted(missing)}"
            )
        member_keys = frozenset(
            source_key(event_by_id[event_id].source_type, event_by_id[event_id].source_record_id)
            for event_id in decision.event_ids
        )
        exception = exception_by_events.get(frozenset(decision.event_ids))
        predictions.append(
            PredictedCase(
                decision.decision_id,
                decision.event_ids,
                member_keys,
                decision.proof_level,
                decision.policy_allows_auto_clear,
                exception.category if exception else None,
                exception.severity if exception else None,
                exception.recommended_action if exception else None,
            )
        )
    return tuple(sorted(predictions, key=lambda item: item.decision_id))


def evaluate_predictions(
    run_id: str,
    truth: TruthDataset,
    predictions: tuple[PredictedCase, ...],
) -> EvaluationReport:
    assignments, unmatched = _assign_predictions(truth.case_labels, predictions)
    case_results = tuple(
        _evaluate_case(case, assignments.get(case.case_id))
        for case in sorted(truth.case_labels, key=lambda item: item.case_id)
    )
    predicted_by_event: dict[str, list[PredictedCase]] = {}
    for prediction in predictions:
        for key in prediction.member_keys:
            predicted_by_event.setdefault(key, []).append(prediction)
    case_result_by_id = {result.expected_case_id: result for result in case_results}
    truth_event_by_key = {event.key: event for event in truth.event_labels}
    all_event_keys = sorted(set(truth_event_by_key) | set(predicted_by_event))
    event_results: list[EventEvaluation] = []
    for key in all_event_keys:
        expected_event = truth_event_by_key.get(key)
        candidates = predicted_by_event.get(key, [])
        expected_case_id = expected_event.expected_case_id if expected_event else None
        case_result = case_result_by_id.get(expected_case_id or "")
        predicted_id = candidates[0].decision_id if len(candidates) == 1 else None
        membership_correct = bool(
            expected_event
            and len(candidates) == 1
            and case_result
            and case_result.group_correct
            and case_result.predicted_decision_id == predicted_id
        )
        disposition_correct = bool(membership_correct and case_result and case_result.proof_correct)
        event_results.append(
            EventEvaluation(
                key,
                expected_case_id,
                predicted_id,
                membership_correct,
                disposition_correct,
            )
        )

    counts = MetricCounts(
        truth_event_count=len(truth.event_labels),
        correct_event_count=sum(result.correct for result in event_results),
        truth_case_count=len(case_results),
        correct_case_count=sum(result.correct for result in case_results),
        predicted_auto_clear_count=sum(item.auto_cleared for item in predictions),
        correct_auto_clear_count=sum(
            result.correct
            and result.expected_proof_level is ProofLevel.PROVED
            and _prediction_for(result, predictions).auto_cleared
            for result in case_results
            if result.predicted_decision_id is not None
        ),
        expected_exception_count=sum(
            case.expected_proof_level is not ProofLevel.PROVED for case in truth.case_labels
        ),
        recalled_exception_count=sum(result.exception_recalled for result in case_results),
        false_clear_count=sum(result.false_clear for result in case_results)
        + sum(item.auto_cleared for item in unmatched),
        wrong_exception_classification_count=sum(
            result.expected_proof_level is not ProofLevel.PROVED
            and result.predicted_decision_id is not None
            and not result.exception_classification_correct
            for result in case_results
        ),
    )
    confusion: dict[tuple[str, str], int] = {}
    for result in case_results:
        key = (
            result.expected_proof_level.value,
            result.predicted_proof_level.value if result.predicted_proof_level else "MISSING",
        )
        confusion[key] = confusion.get(key, 0) + 1
    scenarios = tuple(
        ScenarioResult(
            scenario,
            len(members),
            sum(member.correct for member in members),
            sum(member.false_clear for member in members),
        )
        for scenario in sorted({result.scenario for result in case_results})
        if (members := tuple(result for result in case_results if result.scenario == scenario))
    )
    return EvaluationReport(
        run_id,
        truth.seed,
        EvaluationMetrics.from_counts(counts),
        tuple(event_results),
        case_results,
        scenarios,
        tuple(
            (expected, predicted, count)
            for (expected, predicted), count in sorted(confusion.items())
        ),
        tuple(result.event_key for result in event_results if not result.correct),
        tuple(item.decision_id for item in unmatched),
    )


def _assign_predictions(
    truth_cases: tuple[CaseTruth, ...],
    predictions: tuple[PredictedCase, ...],
) -> tuple[dict[str, PredictedCase], tuple[PredictedCase, ...]]:
    pairs = []
    for case in truth_cases:
        expected = frozenset(case.expected_member_keys)
        for prediction in predictions:
            overlap = len(expected & prediction.member_keys)
            if overlap:
                union = len(expected | prediction.member_keys)
                pairs.append((-overlap, union, case.case_id, prediction.decision_id, prediction))
    assigned_cases: set[str] = set()
    assigned_predictions: set[str] = set()
    assignments: dict[str, PredictedCase] = {}
    for _, _, case_id, decision_id, prediction in sorted(pairs):
        if case_id in assigned_cases or decision_id in assigned_predictions:
            continue
        assignments[case_id] = prediction
        assigned_cases.add(case_id)
        assigned_predictions.add(decision_id)
    return assignments, tuple(
        item for item in predictions if item.decision_id not in assigned_predictions
    )


def _evaluate_case(case: CaseTruth, prediction: PredictedCase | None) -> CaseEvaluation:
    expected_members = frozenset(case.expected_member_keys)
    group_correct = prediction is not None and prediction.member_keys == expected_members
    proof_correct = prediction is not None and prediction.proof_level is case.expected_proof_level
    if case.expected_proof_level is ProofLevel.PROVED:
        classification_correct = prediction is not None and prediction.exception_category is None
    else:
        classification_correct = bool(
            prediction
            and prediction.exception_category is case.expected_exception_category
            and prediction.exception_severity is case.expected_severity
            and prediction.recommended_action is case.expected_next_action
        )
    correct_clear = bool(
        prediction
        and prediction.auto_cleared
        and case.expected_proof_level is ProofLevel.PROVED
        and group_correct
        and proof_correct
    )
    false_clear = bool(prediction and prediction.auto_cleared and not correct_clear)
    exception_recalled = bool(
        case.expected_proof_level is not ProofLevel.PROVED
        and prediction
        and group_correct
        and not prediction.auto_cleared
        and prediction.exception_category is not None
    )
    return CaseEvaluation(
        case.case_id,
        case.scenario,
        prediction.decision_id if prediction else None,
        case.expected_proof_level,
        prediction.proof_level if prediction else None,
        group_correct,
        proof_correct,
        classification_correct,
        false_clear,
        exception_recalled,
        tuple(sorted(expected_members)),
        tuple(sorted(prediction.member_keys)) if prediction else (),
    )


def _prediction_for(
    result: CaseEvaluation, predictions: tuple[PredictedCase, ...]
) -> PredictedCase:
    return next(item for item in predictions if item.decision_id == result.predicted_decision_id)
