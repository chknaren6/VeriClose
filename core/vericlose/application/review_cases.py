"""Read models and append-only preliminary review workflow."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256

from core.vericlose.audit.events import AuditEvent
from core.vericlose.domain.actions import ReviewDecision
from core.vericlose.domain.decisions import ReconciliationDecision
from core.vericlose.domain.enums import ReviewState
from core.vericlose.domain.events import CanonicalEvent
from core.vericlose.domain.exceptions import ExceptionCase
from core.vericlose.domain.runs import RunManifest
from core.vericlose.ingestion.contracts import ValidationIssue
from core.vericlose.ports.repositories import (
    PersistenceUnitOfWork,
    ReconciliationRunRecord,
    SourceFileRecord,
)


class RunNotFoundError(LookupError):
    pass


class CaseNotFoundError(LookupError):
    pass


@dataclass(frozen=True, slots=True)
class RunView:
    manifest: RunManifest
    source_files: tuple[SourceFileRecord, ...]
    validation_issues: tuple[ValidationIssue, ...]
    summary: ReconciliationRunRecord | None


@dataclass(frozen=True, slots=True)
class CaseView:
    run_id: str
    case_id: str
    decision: ReconciliationDecision
    exception: ExceptionCase | None
    events: tuple[CanonicalEvent, ...]
    reviews: tuple[ReviewDecision, ...]


class ReviewQueryService:
    def __init__(self, unit_of_work: Callable[[], PersistenceUnitOfWork]) -> None:
        self._unit_of_work = unit_of_work

    def get_run(self, run_id: str) -> RunView:
        with self._unit_of_work() as repositories:
            manifest = repositories.runs.get(run_id)
            if manifest is None:
                raise RunNotFoundError(run_id)
            return RunView(
                manifest,
                repositories.source_files.list_for_run(run_id),
                repositories.ingestion.list_issues(run_id),
                repositories.reconciliation.get(run_id),
            )

    def check_ready(self) -> None:
        """Open storage and apply migrations without exposing persistence to delivery code."""
        with self._unit_of_work() as repositories:
            repositories.runs.list_ids()

    def list_cases(self, run_id: str) -> tuple[CaseView, ...]:
        with self._unit_of_work() as repositories:
            if repositories.runs.get(run_id) is None:
                raise RunNotFoundError(run_id)
            decisions = repositories.decisions.list_for_run(run_id)
            exceptions = repositories.exceptions.list_for_run(run_id)
            events = repositories.events.list_for_run(run_id)
            reviews = repositories.reviews.list_for_run(run_id)
        event_by_id = {event.event_id: event for event in events}
        exception_by_members = {
            frozenset(link.event_id for link in item.evidence_links if link.event_id): item
            for item in exceptions
        }
        cases = []
        for decision in decisions:
            exception = exception_by_members.get(frozenset(decision.event_ids))
            case_id = exception.case_id if exception else decision.decision_id
            cases.append(
                CaseView(
                    run_id,
                    case_id,
                    decision,
                    exception,
                    tuple(event_by_id[event_id] for event_id in decision.event_ids),
                    tuple(review for review in reviews if review.action_id == case_id),
                )
            )
        return tuple(cases)

    def get_case(self, case_id: str) -> CaseView:
        # Case IDs are globally stable hashes within the local controller. We deliberately
        # scan run IDs here because Segment 6 has one merchant and modest batch sizes.
        with self._unit_of_work() as repositories:
            run_ids = repositories.runs.list_ids()
        for run_id in run_ids:
            match = next(
                (item for item in self.list_cases(run_id) if item.case_id == case_id), None
            )
            if match is not None:
                return match
        raise CaseNotFoundError(case_id)


class PreliminaryReviewService:
    """Records reviewer judgment without mutating evidence or finance decisions."""

    def __init__(
        self,
        query: ReviewQueryService,
        unit_of_work: Callable[[], PersistenceUnitOfWork],
    ) -> None:
        self._query = query
        self._unit_of_work = unit_of_work

    def record(
        self,
        case_id: str,
        *,
        state: ReviewState,
        reviewer_id: str,
        comment: str | None,
        reviewed_at: datetime | None = None,
    ) -> ReviewDecision:
        case = self._query.get_case(case_id)
        timestamp = reviewed_at or datetime.now(UTC)
        identity = sha256(
            f"{case.run_id}|{case_id}|{reviewer_id}|{timestamp.isoformat()}".encode()
        ).hexdigest()[:20]
        review = ReviewDecision(
            f"review_{identity}", case_id, state, reviewer_id, timestamp, comment
        )
        with self._unit_of_work() as repositories:
            repositories.reviews.append(case.run_id, review)
            repositories.audit.append(
                AuditEvent(
                    f"audit_{identity}",
                    case.run_id,
                    "PRELIMINARY_REVIEW_RECORDED",
                    timestamp,
                    (("case_id", case_id), ("state", state.value), ("reviewer_id", reviewer_id)),
                )
            )
        return review
