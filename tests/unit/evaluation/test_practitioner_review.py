from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from evaluation.practitioner_review import (
    FEATURE_FIELDS,
    LABEL_FIELDS,
    RESOLUTION_FIELDS,
    _protect_completed_forms,
    _select_five,
    analyze_pack,
)
from synthetic.base_case import SyntheticConfig
from synthetic.generate import build_synthetic_batch


def test_blind_selection_spans_five_proof_levels() -> None:
    batch = build_synthetic_batch(SyntheticConfig())
    selected = _select_five(batch.truth.case_labels)
    assert len(selected) == 5
    assert {item.expected_proof_level.value for item in selected} == {
        "PROVED",
        "SUPPORTED",
        "AMBIGUOUS",
        "CONTRADICTED",
        "INVALID_INPUT",
    }


def test_analysis_refuses_incomplete_practitioner_labels(tmp_path: Path) -> None:
    pack, private = _review_inputs(tmp_path, complete=False)
    with pytest.raises(ValueError, match="incomplete"):
        analyze_pack(pack, private, tmp_path / "report.md")


def test_analysis_computes_agreement_and_requires_task_ids_for_accepted_work(
    tmp_path: Path,
) -> None:
    pack, private = _review_inputs(tmp_path, complete=True)
    _write_csv(
        pack / "feature_priorities.csv",
        FEATURE_FIELDS,
        [
            {
                "feedback_id": "F-001",
                "observation_or_request": "OBSERVATION",
                "description": "Show the bank row before the ERP row",
                "priority": "MUST_HAVE",
                "trust_impact": "5",
                "review_time_impact": "4",
                "build_cost": "1",
                "scope_risk": "1",
                "decision": "ACCEPT",
                "task_id": "S7-F001",
                "rationale": "Evidence inspection order",
            }
        ],
    )
    report = tmp_path / "DOMAIN_REVIEW_01.md"
    result = analyze_pack(pack, private, report)
    assert result["agreement_count"] == 1
    assert result["disagreement_count"] == 0
    content = report.read_text(encoding="utf-8")
    assert "one experienced ERP reconciliation practitioner" in content
    assert "not an audit, certification" in content
    assert "S7-F001" in content


def test_pack_generation_refuses_to_overwrite_practitioner_input(tmp_path: Path) -> None:
    pack = tmp_path / "pack"
    pack.mkdir()
    label = dict.fromkeys(LABEL_FIELDS, "")
    label.update({"case_id": "PR-001", "reviewer_id": "practitioner-01"})
    _write_csv(pack / "labels.csv", LABEL_FIELDS, [label])
    with pytest.raises(ValueError, match="refusing to overwrite"):
        _protect_completed_forms(pack)


def test_committed_blind_pack_contains_no_outcome_labels() -> None:
    payload = json.loads(Path("docs/practitioner/review_01/cases.json").read_text(encoding="utf-8"))
    assert payload["case_count"] == 25
    assert payload["system_labels_hidden"] is True
    serialized = json.dumps(payload).casefold()
    assert "expected_proof" not in serialized
    assert '"scenario"' not in serialized


def _review_inputs(tmp_path: Path, *, complete: bool) -> tuple[Path, Path]:
    pack = tmp_path / "pack"
    private = tmp_path / "private"
    pack.mkdir()
    private.mkdir()
    label = dict.fromkeys(LABEL_FIELDS, "")
    label.update(
        {
            "case_id": "PR-001",
            "reviewer_id": "practitioner-01" if complete else "",
            "expected_status": "CLEAR" if complete else "",
            "expected_proof_level": "PROVED" if complete else "",
            "reason_category": "NONE" if complete else "",
            "severity": "NONE" if complete else "",
            "next_action": "NO_ACTION" if complete else "",
            "rationale": "All evidence agrees" if complete else "",
        }
    )
    _write_csv(pack / "labels.csv", LABEL_FIELDS, [label])
    _write_csv(pack / "feature_priorities.csv", FEATURE_FIELDS, [])
    _write_csv(pack / "resolutions.csv", RESOLUTION_FIELDS, [])
    (private / "answer_key.json").write_text(
        json.dumps(
            {
                "answers": [
                    {
                        "case_id": "PR-001",
                        "system_proof_level": "PROVED",
                        "expected_reason_category": "NONE",
                        "expected_severity": "NONE",
                        "expected_next_action": "NO_ACTION",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return pack, private


def _write_csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fields)
        writer.writeheader()
        writer.writerows(rows)
