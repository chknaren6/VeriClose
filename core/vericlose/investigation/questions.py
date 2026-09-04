"""Run-scoped grounded Q&A that abstains when no stored case is identified."""

from __future__ import annotations

from dataclasses import dataclass

from core.vericlose.application.review_cases import ReviewQueryService
from core.vericlose.domain.enums import RunState


@dataclass(frozen=True, slots=True)
class GroundedAnswer:
    status: str
    answer: str
    case_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]


class GroundedQuestionService:
    def __init__(self, query: ReviewQueryService) -> None:
        self._query = query

    def answer(self, run_id: str, question: str) -> GroundedAnswer:
        if not isinstance(question, str) or not question.strip():
            raise ValueError("question cannot be blank")
        run = self._query.get_run(run_id)
        if run.manifest.state is not RunState.COMPLETED:
            raise ValueError("questions require a completed run")
        normalized = question.casefold()
        cases = self._query.list_cases(run_id)
        matches = []
        for case in cases:
            tokens = {case.case_id.casefold()}
            tokens.update(event.source_record_id.casefold() for event in case.events)
            tokens.update(
                reference.casefold()
                for event in case.events
                for reference in (
                    event.settlement_reference,
                    event.external_reference,
                    event.bank_utr,
                )
                if reference
            )
            if any(token in normalized for token in tokens):
                matches.append(case)
        if len(matches) != 1:
            return GroundedAnswer(
                "ABSTAINED",
                "I can answer only when one stored case or source reference is named.",
                (),
                (),
            )
        case = matches[0]
        reason = case.exception.reason_code if case.exception else "no exception"
        answer = (
            f"Case {case.case_id} is {case.decision.proof_level.value} with {reason}. "
            f"The conclusion is based on {len(case.decision.proof_checks)} deterministic checks "
            f"and {len(case.decision.evidence_links)} cited source rows."
        )
        return GroundedAnswer(
            "ANSWERED",
            answer,
            (case.case_id,),
            tuple(link.event_id for link in case.decision.evidence_links if link.event_id),
        )
