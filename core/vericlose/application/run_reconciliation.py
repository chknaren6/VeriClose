"""Application service coordinating persisted canonical events through the risk gate."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from core.vericlose.audit.events import AuditEvent
from core.vericlose.domain.enums import RunState
from core.vericlose.domain.runs import RunManifest
from core.vericlose.ports.repositories import (
    PersistenceUnitOfWork,
    ReconciliationRunRecord,
)
from core.vericlose.reconciliation.pipeline import KernelResult, reconcile
from core.vericlose.reconciliation.policy import ReconciliationPolicy
from core.vericlose.reconciliation.rules.settlement import RULE_VERSION


class ReconciliationRunStateError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ReconcileRunResult:
    manifest: RunManifest
    kernel: KernelResult
    summary: ReconciliationRunRecord


class RunReconciliationService:
    def __init__(
        self,
        policy: ReconciliationPolicy,
        unit_of_work: Callable[[], PersistenceUnitOfWork],
    ) -> None:
        self._policy = policy
        self._unit_of_work = unit_of_work

    def run(self, run_id: str, *, occurred_at: datetime | None = None) -> ReconcileRunResult:
        timestamp = occurred_at or datetime.now(UTC)
        with self._unit_of_work() as repositories:
            manifest = repositories.runs.get(run_id)
            if manifest is None:
                raise ReconciliationRunStateError(f"run does not exist: {run_id}")
            if manifest.state is not RunState.VALIDATED:
                raise ReconciliationRunStateError(
                    f"run must be VALIDATED, found {manifest.state.value}"
                )
            if manifest.policy_version not in {
                self._policy.policy_id,
                self._policy.versioned_id,
            }:
                raise ReconciliationRunStateError(
                    f"run policy {manifest.policy_version} does not match "
                    f"{self._policy.versioned_id}"
                )
            events = repositories.events.list_for_run(run_id)
            reconciling = manifest.transition(RunState.RECONCILING)
            repositories.runs.append(reconciling)
            repositories.audit.append(
                AuditEvent(
                    f"{run_id}:reconciliation-started",
                    run_id,
                    "RECONCILIATION_STARTED",
                    timestamp,
                    (("event_count", str(len(events))),),
                )
            )

        try:
            kernel = reconcile(events, self._policy)
            summary = ReconciliationRunRecord(
                run_id,
                self._policy.versioned_id,
                RULE_VERSION,
                len(kernel.decisions),
                kernel.auto_cleared_count,
                len(kernel.exceptions),
                sum(item.amount_at_risk.amount_minor for item in kernel.exceptions),
                tuple(
                    (item.stage, item.duration_ms, item.input_count, item.output_count)
                    for item in kernel.timings
                ),
            )
            completed = reconciling.transition(RunState.COMPLETED)
            with self._unit_of_work() as repositories:
                for decision in kernel.decisions:
                    repositories.decisions.append(run_id, decision)
                for exception in kernel.exceptions:
                    repositories.exceptions.append(run_id, exception)
                repositories.reconciliation.append(summary)
                repositories.runs.append(completed)
                repositories.audit.append(
                    AuditEvent(
                        f"{run_id}:reconciliation-completed",
                        run_id,
                        "RECONCILIATION_COMPLETED",
                        timestamp,
                        (
                            ("decision_count", str(summary.decision_count)),
                            ("auto_cleared_count", str(summary.auto_cleared_count)),
                            ("exception_count", str(summary.exception_count)),
                            ("amount_at_risk_minor", str(summary.amount_at_risk_minor)),
                        ),
                    )
                )
        except Exception:
            self._mark_failed(reconciling, timestamp)
            raise
        return ReconcileRunResult(completed, kernel, summary)

    def _mark_failed(self, reconciling: RunManifest, timestamp: datetime) -> None:
        with self._unit_of_work() as repositories:
            current = repositories.runs.get(reconciling.run_id)
            if current is not None and current.state is RunState.RECONCILING:
                repositories.runs.append(current.transition(RunState.FAILED))
                repositories.audit.append(
                    AuditEvent(
                        f"{reconciling.run_id}:reconciliation-failed",
                        reconciling.run_id,
                        "RECONCILIATION_FAILED",
                        timestamp,
                    )
                )
