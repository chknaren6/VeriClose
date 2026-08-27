import json

import pytest

from core.vericlose.domain.enums import (
    ActionType,
    ExceptionCategory,
    ProofLevel,
    Severity,
    SourceType,
)
from synthetic.truth.models import CaseTruth, EventTruth, TruthDataset


def _truth() -> TruthDataset:
    event = EventTruth(SourceType.BANK, "bank-1", "case-1", "BANK_RECEIPT")
    case = CaseTruth(
        case_id="case-1",
        scenario="missing_gateway",
        expected_member_keys=(event.key,),
        expected_proof_level=ProofLevel.AMBIGUOUS,
        expected_exception_category=ExceptionCategory.MISSING_SOURCE,
        expected_severity=Severity.HIGH,
        expected_next_action=ActionType.CLARIFICATION_REQUEST,
        valid_timing_difference=False,
        description="Synthetic truth round-trip case.",
    )
    return TruthDataset("1.0", 42, (event,), (case,))


def test_truth_round_trips_through_json() -> None:
    original = _truth()
    payload = json.loads(json.dumps(original.to_dict()))
    assert TruthDataset.from_dict(payload) == original


def test_truth_event_keys_are_namespaced_and_unique() -> None:
    assert _truth().event_labels[0].key == "BANK:bank-1"
    duplicate = _truth().event_labels[0]
    with pytest.raises(ValueError, match="unique"):
        TruthDataset("1.0", 42, (duplicate, duplicate), _truth().case_labels)


def test_non_proved_truth_requires_honest_exception_classification() -> None:
    with pytest.raises(ValueError, match="exception category"):
        CaseTruth(
            "case-1",
            "unknown",
            ("BANK:bank-1",),
            ProofLevel.AMBIGUOUS,
            None,
            None,
            ActionType.MANUAL_REVIEW,
            False,
            "Missing classification",
        )
