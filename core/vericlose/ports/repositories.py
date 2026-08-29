"""Persistence ports; domain/application code never sees SQL."""

from dataclasses import dataclass
from types import TracebackType
from typing import Protocol, Self, runtime_checkable

from core.vericlose.audit.events import AuditEvent
from core.vericlose.domain.actions import ActionReceipt, ProposedAction, ReviewDecision
from core.vericlose.domain.decisions import ReconciliationDecision
from core.vericlose.domain.events import CanonicalEvent
from core.vericlose.domain.exceptions import ExceptionCase
from core.vericlose.domain.runs import RunManifest, SourceFile
from core.vericlose.ingestion.contracts import (
    ControlTotals,
    NormalizationResult,
    ValidationIssue,
    ValidationReport,
)


@dataclass(frozen=True, slots=True)
class SourceFileRecord:
    run_id: str
    source_file: SourceFile
    adapter_id: str
    adapter_version: str
    mapping_profile_version: str
    relative_path: str


@runtime_checkable
class RunRepository(Protocol):
    def append(self, manifest: RunManifest) -> None: ...

    def get(self, run_id: str) -> RunManifest | None: ...

    def list_ids(self) -> tuple[str, ...]: ...


@runtime_checkable
class SourceFileRepository(Protocol):
    def add(self, record: SourceFileRecord) -> None: ...

    def exists_hash(self, run_id: str, sha256: str) -> bool: ...

    def list_for_run(self, run_id: str) -> tuple[SourceFileRecord, ...]: ...


@runtime_checkable
class EventRepository(Protocol):
    def append(self, run_id: str, events: tuple[CanonicalEvent, ...]) -> None: ...

    def list_for_run(self, run_id: str) -> tuple[CanonicalEvent, ...]: ...


@runtime_checkable
class DecisionRepository(Protocol):
    def append(self, run_id: str, decision: ReconciliationDecision) -> None: ...

    def list_for_run(self, run_id: str) -> tuple[ReconciliationDecision, ...]: ...


@runtime_checkable
class ExceptionRepository(Protocol):
    def append(self, run_id: str, exception: ExceptionCase) -> None: ...

    def list_for_run(self, run_id: str) -> tuple[ExceptionCase, ...]: ...


@dataclass(frozen=True, slots=True)
class ReconciliationRunRecord:
    run_id: str
    policy_version: str
    rule_version: str
    decision_count: int
    auto_cleared_count: int
    exception_count: int
    amount_at_risk_minor: int
    stage_timings: tuple[tuple[str, int, int, int], ...]


@runtime_checkable
class ReconciliationRunRepository(Protocol):
    def append(self, record: ReconciliationRunRecord) -> None: ...

    def get(self, run_id: str) -> ReconciliationRunRecord | None: ...


@runtime_checkable
class ReviewRepository(Protocol):
    def append(self, run_id: str, review: ReviewDecision) -> None: ...

    def list_for_run(self, run_id: str) -> tuple[ReviewDecision, ...]: ...


@runtime_checkable
class ActionRepository(Protocol):
    def append_action(self, run_id: str, action: ProposedAction) -> None: ...

    def append_receipt(self, run_id: str, receipt: ActionReceipt) -> None: ...


@runtime_checkable
class AuditRepository(Protocol):
    def append(self, event: AuditEvent) -> None: ...


@runtime_checkable
class IngestionRepository(Protocol):
    def append_file_result(
        self,
        run_id: str,
        validation: ValidationReport,
        normalization: NormalizationResult | None,
        control_totals: ControlTotals | None,
    ) -> None: ...

    def list_issues(self, run_id: str) -> tuple[ValidationIssue, ...]: ...


@runtime_checkable
class PersistenceUnitOfWork(Protocol):
    runs: RunRepository
    source_files: SourceFileRepository
    events: EventRepository
    decisions: DecisionRepository
    exceptions: ExceptionRepository
    reconciliation: ReconciliationRunRepository
    reviews: ReviewRepository
    actions: ActionRepository
    audit: AuditRepository
    ingestion: IngestionRepository

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...
