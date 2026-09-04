"""Reproducible close, exception, and audit artifacts for completed runs."""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from hashlib import sha256
from typing import Any

from core.vericlose.application.actions import ActionQueryService
from core.vericlose.application.review_cases import ReviewQueryService
from core.vericlose.domain.enums import RunState
from core.vericlose.ports.repositories import PersistenceUnitOfWork


@dataclass(frozen=True, slots=True)
class RunArtifact:
    filename: str
    media_type: str
    content: bytes
    sha256: str


class RunArtifactService:
    def __init__(
        self,
        runs: ReviewQueryService,
        actions: ActionQueryService,
        unit_of_work: Callable[[], PersistenceUnitOfWork],
    ) -> None:
        self._runs = runs
        self._actions = actions
        self._unit_of_work = unit_of_work

    def build(self, run_id: str, kind: str) -> RunArtifact:
        view = self._runs.get_run(run_id)
        if view.manifest.state is not RunState.COMPLETED:
            raise ValueError("run artifacts require a completed run")
        builders = {
            "close-report": self._close_report,
            "exception-pack": self._exception_pack,
            "audit-log": self._audit_log,
        }
        try:
            filename, media_type, content = builders[kind](run_id)
        except KeyError as error:
            raise LookupError(f"unknown run artifact: {kind}") from error
        return RunArtifact(filename, media_type, content, sha256(content).hexdigest())

    def _close_report(self, run_id: str) -> tuple[str, str, bytes]:
        cases = self._runs.list_cases(run_id)
        action_by_case = {item.action.case_id: item for item in self._actions.list_for_run(run_id)}
        output = io.StringIO(newline="")
        fields = (
            "run_id",
            "case_id",
            "decision_state",
            "proof_level",
            "reason_code",
            "amount_at_risk_minor",
            "currency",
            "action_type",
            "action_state",
            "evidence_count",
        )
        writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for case in cases:
            action = action_by_case.get(case.case_id)
            writer.writerow(
                {
                    "run_id": run_id,
                    "case_id": case.case_id,
                    "decision_state": case.decision.state.value,
                    "proof_level": case.decision.proof_level.value,
                    "reason_code": case.exception.reason_code if case.exception else "",
                    "amount_at_risk_minor": (
                        case.exception.amount_at_risk.amount_minor if case.exception else 0
                    ),
                    "currency": "INR",
                    "action_type": action.action.action_type.value if action else "",
                    "action_state": action.action.state.value if action else "",
                    "evidence_count": len(case.decision.evidence_links),
                }
            )
        return f"{run_id}-close-report.csv", "text/csv", output.getvalue().encode()

    def _exception_pack(self, run_id: str) -> tuple[str, str, bytes]:
        cases = self._runs.list_cases(run_id)
        payload = {
            "run_id": run_id,
            "currency": "INR",
            "exceptions": [
                {
                    "case_id": case.case_id,
                    "proof_level": case.decision.proof_level.value,
                    "reason_code": case.exception.reason_code,
                    "severity": case.exception.severity.value,
                    "amount_at_risk_minor": case.exception.amount_at_risk.amount_minor,
                    "requires_company_input": case.exception.requires_company_input,
                    "recommended_action": case.exception.recommended_action.value,
                    "evidence": [
                        {
                            "event_id": link.event_id,
                            "source_file_id": link.source_file_id,
                            "row_number": link.row_number,
                            "raw_row_hash": link.raw_row_hash,
                        }
                        for link in case.exception.evidence_links
                    ],
                }
                for case in cases
                if case.exception is not None
            ],
        }
        content = (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode()
        return f"{run_id}-exception-pack.json", "application/json", content

    def _audit_log(self, run_id: str) -> tuple[str, str, bytes]:
        with self._unit_of_work() as repositories:
            events = repositories.audit.list_for_run(run_id)
        payload: list[dict[str, Any]] = []
        for event in events:
            item = asdict(event)
            item["occurred_at"] = event.occurred_at.isoformat()
            payload.append(item)
        content = (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode()
        return f"{run_id}-audit-log.json", "application/json", content
