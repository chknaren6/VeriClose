"""Build and analyze a blinded, synthetic-only practitioner review pack."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from core.vericlose.domain.enums import ActionType, ExceptionCategory, ProofLevel, Severity
from evaluation.benchmark import load_benchmark_config, run_benchmark
from synthetic.base_case import SyntheticConfig
from synthetic.generate import build_synthetic_batch

REVIEW_SEEDS = (42, 73, 101, 211, 307)
HOLDOUT_SEEDS = (401, 503)
PROOF_ORDER = ("AMBIGUOUS", "INVALID_INPUT", "SUPPORTED", "CONTRADICTED", "PROVED")
LABEL_FIELDS = (
    "case_id",
    "reviewer_id",
    "expected_status",
    "expected_proof_level",
    "reason_category",
    "severity",
    "next_action",
    "requires_company_input",
    "required_evidence_ids",
    "journal_behavior",
    "rationale",
    "review_seconds",
)
FEATURE_FIELDS = (
    "feedback_id",
    "observation_or_request",
    "description",
    "priority",
    "trust_impact",
    "review_time_impact",
    "build_cost",
    "scope_risk",
    "decision",
    "task_id",
    "rationale",
)
RESOLUTION_FIELDS = (
    "case_id",
    "decision",
    "disagreement_reason",
    "accepted_proof_level",
    "accepted_reason_category",
    "accepted_severity",
    "accepted_next_action",
    "task_id",
)


@dataclass(frozen=True, slots=True)
class ReviewCase:
    blind_id: str
    seed: int
    source_rows: tuple[dict[str, Any], ...]


def build_pack(output_dir: Path, private_dir: Path) -> dict[str, Any]:
    """Create committed blind artifacts and separately stored reveal/holdout data."""

    _protect_completed_forms(output_dir)
    benchmark = run_benchmark(
        load_benchmark_config(Path("config/evaluation/default.yaml")), seeds=REVIEW_SEEDS
    )
    selected: list[ReviewCase] = []
    answers: list[dict[str, Any]] = []
    ordinal = 1
    for seed_result in benchmark.seed_results:
        batch = build_synthetic_batch(
            SyntheticConfig(seed=seed_result.seed, payments=120, settlements=24, exception_rate=0.4)
        )
        evaluations = {item.expected_case_id: item for item in seed_result.evaluation.case_results}
        cases = _select_five(batch.truth.case_labels)
        for truth in cases:
            blind_id = f"PR-{ordinal:03d}"
            rows = tuple(
                {
                    "evidence_id": f"{blind_id}-E{index:02d}",
                    "source_type": row.source_type.value,
                    "source_record_id": row.source_record_id,
                    "source_values": row.to_csv_row(),
                }
                for index, row in enumerate(batch.rows_for_case(truth.case_id), start=1)
            )
            selected.append(ReviewCase(blind_id, seed_result.seed, rows))
            evaluated = evaluations[truth.case_id]
            answers.append(
                {
                    "case_id": blind_id,
                    "seed": seed_result.seed,
                    "internal_case_id": truth.case_id,
                    "scenario": truth.scenario,
                    "system_proof_level": (
                        evaluated.predicted_proof_level.value
                        if evaluated.predicted_proof_level
                        else "MISSING"
                    ),
                    "expected_proof_level": truth.expected_proof_level.value,
                    "expected_reason_category": (
                        truth.expected_exception_category.value
                        if truth.expected_exception_category
                        else "NONE"
                    ),
                    "expected_severity": (
                        truth.expected_severity.value if truth.expected_severity else "NONE"
                    ),
                    "expected_next_action": truth.expected_next_action.value,
                    "description": truth.description,
                    "benchmark_case_correct": evaluated.correct,
                }
            )
            ordinal += 1

    output_dir.mkdir(parents=True, exist_ok=True)
    private_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        output_dir / "cases.json",
        {
            "schema_version": "1.0",
            "synthetic_data_only": True,
            "system_labels_hidden": True,
            "case_count": len(selected),
            "seeds": list(REVIEW_SEEDS),
            "cases": [
                {
                    "case_id": item.blind_id,
                    "source_rows": list(item.source_rows),
                }
                for item in selected
            ],
        },
    )
    _write_cases_markdown(output_dir / "CASES.md", selected)
    _write_csv(
        output_dir / "labels.csv",
        LABEL_FIELDS,
        [dict.fromkeys(LABEL_FIELDS, "") | {"case_id": item.blind_id} for item in selected],
    )
    _write_csv(output_dir / "feature_priorities.csv", FEATURE_FIELDS, [])
    _write_csv(
        output_dir / "resolutions.csv",
        RESOLUTION_FIELDS,
        [dict.fromkeys(RESOLUTION_FIELDS, "") | {"case_id": item.blind_id} for item in selected],
    )
    _write_json(
        private_dir / "answer_key.json",
        {
            "schema_version": "1.0",
            "generated_at": datetime.now(UTC).isoformat(),
            "answers": answers,
        },
    )
    _write_json(
        private_dir / "holdout_manifest.json",
        {
            "schema_version": "1.0",
            "seeds": list(HOLDOUT_SEEDS),
            "status": "RESERVED_UNUSED",
            "instruction": "Do not inspect or label until the 90% validation review.",
        },
    )
    _write_least_certain(private_dir / "LEAST_CERTAIN.md", answers)
    return {
        "case_count": len(selected),
        "seed_count": len(REVIEW_SEEDS),
        "proof_mix": dict(
            sorted(Counter(item["expected_proof_level"] for item in answers).items())
        ),
        "scenario_count": len({item["scenario"] for item in answers}),
        "output": str(output_dir),
        "private_output": str(private_dir),
    }


def analyze_pack(
    pack_dir: Path,
    private_dir: Path,
    report_path: Path,
    golden_path: Path | None = None,
) -> dict[str, Any]:
    """Publish proportional findings only after every independent label is complete."""

    labels = _read_csv(pack_dir / "labels.csv")
    answers = json.loads((private_dir / "answer_key.json").read_text(encoding="utf-8"))["answers"]
    if len(labels) != len(answers):
        raise ValueError("label count does not match the blinded answer key")
    required = (
        "reviewer_id",
        "expected_status",
        "expected_proof_level",
        "reason_category",
        "severity",
        "next_action",
        "rationale",
    )
    incomplete = [
        row["case_id"] for row in labels if any(not row[field].strip() for field in required)
    ]
    if incomplete:
        raise ValueError(f"practitioner labels are incomplete: {', '.join(incomplete)}")
    _validate_labels(labels)
    answer_by_id = {row["case_id"]: row for row in answers}
    comparisons = []
    for label in labels:
        answer = answer_by_id[label["case_id"]]
        agreement = (
            label["expected_proof_level"] == answer["system_proof_level"]
            and label["reason_category"] == answer["expected_reason_category"]
            and label["severity"] == answer["expected_severity"]
            and label["next_action"] == answer["expected_next_action"]
        )
        comparisons.append((label, answer, agreement))
    features = _read_csv(pack_dir / "feature_priorities.csv")
    _validate_features(features)
    resolutions = {
        row["case_id"]: row
        for row in _read_csv(pack_dir / "resolutions.csv")
        if row["decision"].strip()
    }
    _validate_resolutions(comparisons, resolutions)
    agreed = sum(item[2] for item in comparisons)
    content = _domain_review_markdown(comparisons, features, resolutions, agreed)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(content, encoding="utf-8")
    golden_count = 0
    if golden_path is not None:
        golden_count = _write_golden(pack_dir, golden_path, comparisons, resolutions)
    return {
        "case_count": len(comparisons),
        "agreement_count": agreed,
        "disagreement_count": len(comparisons) - agreed,
        "feature_count": len(features),
        "golden_case_count": golden_count,
        "report": str(report_path),
    }


def _select_five(cases: tuple[Any, ...]) -> tuple[Any, ...]:
    selected = []
    for proof in PROOF_ORDER:
        candidate = next(
            (
                item
                for item in cases
                if item.expected_proof_level.value == proof and item not in selected
            ),
            None,
        )
        if candidate:
            selected.append(candidate)
    for candidate in sorted(cases, key=lambda item: (item.scenario, item.case_id)):
        if len(selected) == 5:
            break
        if candidate not in selected and candidate.scenario not in {
            item.scenario for item in selected
        }:
            selected.append(candidate)
    if len(selected) != 5:
        raise ValueError("could not select five diverse practitioner cases")
    return tuple(selected)


def _write_cases_markdown(path: Path, cases: list[ReviewCase]) -> None:
    lines = [
        "# Blinded practitioner cases",
        "",
        "> Synthetic data only. System decisions and benchmark labels are intentionally hidden.",
        "",
    ]
    for case in cases:
        lines.extend((f"## {case.blind_id}", ""))
        for source in ("GATEWAY", "BANK", "ERP"):
            rows = [item for item in case.source_rows if item["source_type"] == source]
            lines.extend((f"### {source}", ""))
            if not rows:
                lines.extend(("No source row is present.", ""))
            for row in rows:
                values = ", ".join(f"{key}={value}" for key, value in row["source_values"].items())
                lines.extend((f"- `{row['evidence_id']}` — {values}", ""))
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_least_certain(path: Path, answers: list[dict[str, Any]]) -> None:
    priority = {"AMBIGUOUS": 0, "INVALID_INPUT": 1, "SUPPORTED": 2, "CONTRADICTED": 3, "PROVED": 4}
    ordered = sorted(
        answers, key=lambda item: (priority[item["system_proof_level"]], item["case_id"])
    )
    selected = []
    for item in ordered:
        if item["scenario"] not in {chosen["scenario"] for chosen in selected}:
            selected.append(item)
        if len(selected) == 5:
            break
    lines = ["# Five least-certain system decisions", "", "Open only after blind labelling.", ""]
    for item in selected:
        lines.append(
            f"- `{item['case_id']}` — {item['system_proof_level']} / {item['scenario']}: "
            "abstention or incomplete/contradictory evidence needs practitioner judgment."
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _validate_features(rows: list[dict[str, str]]) -> None:
    allowed_priorities = {"MUST_HAVE", "SHOULD_HAVE", "LATER", "REJECT"}
    allowed_decisions = {"ACCEPT", "DEFER", "REJECT"}
    for row in rows:
        if row["priority"] not in allowed_priorities or row["decision"] not in allowed_decisions:
            raise ValueError(f"invalid priority/decision for {row['feedback_id']}")
        for field in ("trust_impact", "review_time_impact", "build_cost", "scope_risk"):
            if row[field] not in {"1", "2", "3", "4", "5"}:
                raise ValueError(f"{field} must be 1..5 for {row['feedback_id']}")
        if row["decision"] == "ACCEPT" and not row["task_id"].strip():
            raise ValueError(f"accepted feedback requires a task_id: {row['feedback_id']}")
        if row["priority"] == "MUST_HAVE" and int(row["trust_impact"]) < 4:
            raise ValueError(f"must-have feedback requires trust impact >= 4: {row['feedback_id']}")


def _validate_labels(rows: list[dict[str, str]]) -> None:
    allowed_proof = {item.value for item in ProofLevel}
    allowed_categories = {item.value for item in ExceptionCategory} | {"NONE"}
    allowed_severity = {item.value for item in Severity} | {"NONE"}
    allowed_actions = {item.value for item in ActionType}
    for row in rows:
        if row["expected_status"] not in {"CLEAR", "REVIEW", "UNRESOLVED"}:
            raise ValueError(f"invalid expected_status for {row['case_id']}")
        if row["expected_proof_level"] not in allowed_proof:
            raise ValueError(f"invalid proof level for {row['case_id']}")
        if row["reason_category"] not in allowed_categories:
            raise ValueError(f"invalid reason category for {row['case_id']}")
        if row["severity"] not in allowed_severity:
            raise ValueError(f"invalid severity for {row['case_id']}")
        if row["next_action"] not in allowed_actions:
            raise ValueError(f"invalid next action for {row['case_id']}")


def _validate_resolutions(
    comparisons: list[tuple[dict[str, str], dict[str, Any], bool]],
    resolutions: dict[str, dict[str, str]],
) -> None:
    for label, _, agreement in comparisons:
        if agreement:
            continue
        resolution = resolutions.get(label["case_id"])
        if not resolution:
            raise ValueError(f"disagreement has no resolution: {label['case_id']}")
        if resolution["decision"] not in {
            "ACCEPT_SYSTEM",
            "ACCEPT_PRACTITIONER",
            "DEFER",
        }:
            raise ValueError(f"invalid disagreement decision: {label['case_id']}")
        if not resolution["disagreement_reason"].strip():
            raise ValueError(f"disagreement requires a reason: {label['case_id']}")
        if resolution["decision"] == "ACCEPT_PRACTITIONER" and not resolution["task_id"].strip():
            raise ValueError(
                f"accepted practitioner correction requires a task_id: {label['case_id']}"
            )


def _domain_review_markdown(
    comparisons: list[tuple[dict[str, str], dict[str, Any], bool]],
    features: list[dict[str, str]],
    resolutions: dict[str, dict[str, str]],
    agreed: int,
) -> str:
    lines = [
        "# Domain Review 01",
        "",
        "**Status:** completed practitioner review",
        "",
        (
            "> This is feedback from one experienced ERP reconciliation practitioner. "
            "It is not an audit, certification, or universal accounting policy."
        ),
        "",
        "## Methodology",
        "",
        (
            f"One practitioner independently labelled {len(comparisons)} blinded synthetic "
            "cases across five seeds before system outcomes were revealed."
        ),
        "No real client data or identifiers were used.",
        "",
        "## Agreement",
        "",
        f"- Full-label agreement: {agreed}/{len(comparisons)}",
        f"- Disagreements requiring investigation: {len(comparisons) - agreed}",
        "",
        "## Disagreements",
        "",
    ]
    disagreements = [item for item in comparisons if not item[2]]
    if not disagreements:
        lines.append("No full-label disagreements were recorded.")
    for label, answer, _ in disagreements:
        resolution = resolutions[label["case_id"]]
        lines.extend(
            (
                f"### {label['case_id']}",
                "",
                (
                    f"- Practitioner: {label['expected_proof_level']} / "
                    f"{label['reason_category']} / {label['severity']} / "
                    f"{label['next_action']}"
                ),
                (
                    f"- System: {answer['system_proof_level']} / "
                    f"{answer['expected_reason_category']} / "
                    f"{answer['expected_severity']} / {answer['expected_next_action']}"
                ),
                f"- Practitioner rationale: {label['rationale']}",
                (
                    f"- Resolution: {resolution['decision']} — "
                    f"{resolution['disagreement_reason']} "
                    f"(task: {resolution['task_id'] or 'none'})"
                ),
                "",
            )
        )
    lines.extend(("## Feature decisions", ""))
    if not features:
        lines.append("No feature requests were recorded.")
    for row in features:
        score = (
            int(row["trust_impact"])
            + int(row["review_time_impact"])
            - int(row["build_cost"])
            - int(row["scope_risk"])
        )
        lines.append(
            f"- `{row['feedback_id']}` — **{row['decision']} / {row['priority']}** — "
            f"{row['description']} (impact score: {score}; "
            f"task: {row['task_id'] or 'none'})"
        )
    lines.extend(
        (
            "",
            "## Privacy and limitations",
            "",
            (
                "All reviewed evidence was seeded synthetic data. Findings represent one "
                "practitioner and must be regression-tested before changing finance behavior. "
                "The reserved holdout was not used."
            ),
            "",
        )
    )
    return "\n".join(lines)


def _write_golden(
    pack_dir: Path,
    path: Path,
    comparisons: list[tuple[dict[str, str], dict[str, Any], bool]],
    resolutions: dict[str, dict[str, str]],
) -> int:
    visible = json.loads((pack_dir / "cases.json").read_text(encoding="utf-8"))
    visible_by_id = {item["case_id"]: item for item in visible["cases"]}
    cases = []
    for label, answer, agreement in comparisons:
        resolution = resolutions.get(label["case_id"])
        if not agreement and resolution and resolution["decision"] == "DEFER":
            continue
        use_practitioner = agreement or (
            resolution is not None and resolution["decision"] == "ACCEPT_PRACTITIONER"
        )
        cases.append(
            {
                "case_id": label["case_id"],
                "source_rows": visible_by_id[label["case_id"]]["source_rows"],
                "expected_proof_level": (
                    label["expected_proof_level"]
                    if use_practitioner
                    else answer["system_proof_level"]
                ),
                "expected_reason_category": (
                    label["reason_category"]
                    if use_practitioner
                    else answer["expected_reason_category"]
                ),
                "expected_severity": (
                    label["severity"] if use_practitioner else answer["expected_severity"]
                ),
                "expected_next_action": (
                    label["next_action"] if use_practitioner else answer["expected_next_action"]
                ),
                "practitioner_rationale": label["rationale"],
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(
        path,
        {
            "schema_version": "1.0",
            "synthetic_data_only": True,
            "holdout_excluded": True,
            "cases": cases,
        },
    )
    return len(cases)


def _write_csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _protect_completed_forms(output_dir: Path) -> None:
    for filename in ("labels.csv", "feature_priorities.csv", "resolutions.csv"):
        path = output_dir / filename
        if path.is_file() and any(
            any(value.strip() for key, value in row.items() if key != "case_id")
            for row in _read_csv(path)
        ):
            raise ValueError(f"refusing to overwrite practitioner input: {path}")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build")
    build.add_argument("--output", type=Path, default=Path("docs/practitioner/review_01"))
    build.add_argument("--private", type=Path, default=Path(".data/practitioner/review_01/private"))
    analyze = subparsers.add_parser("analyze")
    analyze.add_argument("--pack", type=Path, default=Path("docs/practitioner/review_01"))
    analyze.add_argument(
        "--private", type=Path, default=Path(".data/practitioner/review_01/private")
    )
    analyze.add_argument("--report", type=Path, default=Path("docs/domain/DOMAIN_REVIEW_01.md"))
    analyze.add_argument(
        "--golden",
        type=Path,
        default=Path("evaluation/golden/practitioner_review_01.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    try:
        result = (
            build_pack(args.output, args.private)
            if args.command == "build"
            else analyze_pack(args.pack, args.private, args.report, args.golden)
        )
    except ValueError as error:
        print(json.dumps({"status": "blocked", "reason": str(error)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
