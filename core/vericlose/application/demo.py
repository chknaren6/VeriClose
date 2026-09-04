"""Restore a known synthetic batch through the public import and proof services."""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from core.vericlose.application.review_cases import ReviewQueryService, RunView
from core.vericlose.application.run_reconciliation import RunReconciliationService
from core.vericlose.ingestion.contracts import NormalizationContext
from core.vericlose.ingestion.service import ImportBatchService
from core.vericlose.ports.demo_source import DemoSourceProvider


@dataclass(frozen=True, slots=True)
class DemoResetResult:
    run: RunView


class DemoResetService:
    def __init__(
        self,
        source: DemoSourceProvider,
        importer: ImportBatchService,
        reconciler: RunReconciliationService,
        query: ReviewQueryService,
        *,
        policy_version: str,
        rule_version: str,
        seed: int,
        build_commit: str,
    ) -> None:
        self._source = source
        self._importer = importer
        self._reconciler = reconciler
        self._query = query
        self._policy_version = policy_version
        self._rule_version = rule_version
        self._seed = seed
        self._build_commit = build_commit

    def reset(
        self, *, run_id: str | None = None, now: datetime | None = None
    ) -> DemoResetResult:
        timestamp = now or datetime.now(UTC)
        resolved_run_id = run_id or (
            f"demo-{self._seed}-{timestamp:%Y%m%d%H%M%S}-{uuid4().hex[:8]}"
        )
        imported = self._importer.import_batch(
            run_id=resolved_run_id,
            documents=self._source.load(),
            context=NormalizationContext(resolved_run_id, "demo-merchant-in"),
            policy_version=self._policy_version,
            rule_version=self._rule_version,
            seed=self._seed,
            build_commit=self._build_commit,
            imported_at=timestamp,
        )
        if not imported.is_ready:
            raise ValueError("known demo fixtures failed validation")
        self._reconciler.run(resolved_run_id, occurred_at=timestamp)
        return DemoResetResult(self._query.get_run(resolved_run_id))
