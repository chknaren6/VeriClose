"""A storage implementation can be replaced without changing application contracts."""

from __future__ import annotations

from datetime import UTC, datetime

from core.vericlose.audit.events import AuditEvent
from core.vericlose.domain.enums import RunState
from core.vericlose.domain.runs import RunManifest
from core.vericlose.ports.repositories import (
    ActionRepository,
    AuditRepository,
    DecisionRepository,
    EventRepository,
    ExceptionRepository,
    IngestionRepository,
    InvestigationRepository,
    PersistenceUnitOfWork,
    ReconciliationRunRecord,
    ReconciliationRunRepository,
    ReviewRepository,
    RunRepository,
    SourceFileRecord,
    SourceFileRepository,
)


class FakeRunRepository:
    def __init__(self) -> None:
        self.items: dict[str, list[RunManifest]] = {}

    def append(self, manifest: RunManifest) -> None:
        self.items.setdefault(manifest.run_id, []).append(manifest)

    def get(self, run_id: str) -> RunManifest | None:
        snapshots = self.items.get(run_id, [])
        return snapshots[-1] if snapshots else None

    def list_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self.items))


class FakeSourceFileRepository:
    def __init__(self) -> None:
        self.items: list[SourceFileRecord] = []

    def add(self, record: SourceFileRecord) -> None:
        self.items.append(record)

    def exists_hash(self, run_id: str, sha256: str) -> bool:
        return any(
            item.run_id == run_id and item.source_file.sha256 == sha256 for item in self.items
        )

    def list_for_run(self, run_id: str) -> tuple[SourceFileRecord, ...]:
        return tuple(item for item in self.items if item.run_id == run_id)


class FakeEventRepository:
    def __init__(self) -> None:
        self.items: dict[str, tuple] = {}

    def append(self, run_id: str, events: tuple) -> None:
        self.items[run_id] = self.items.get(run_id, ()) + events

    def list_for_run(self, run_id: str) -> tuple:
        return self.items.get(run_id, ())


class FakeDecisionRepository:
    def __init__(self) -> None:
        self.items: dict[str, tuple] = {}

    def append(self, run_id: str, decision: object) -> None:
        self.items[run_id] = self.items.get(run_id, ()) + (decision,)

    def list_for_run(self, run_id: str) -> tuple:
        return self.items.get(run_id, ())


class FakeExceptionRepository(FakeDecisionRepository):
    pass


class FakeReconciliationRunRepository:
    def __init__(self) -> None:
        self.items: dict[str, ReconciliationRunRecord] = {}

    def append(self, record: ReconciliationRunRecord) -> None:
        self.items[record.run_id] = record

    def get(self, run_id: str) -> ReconciliationRunRecord | None:
        return self.items.get(run_id)


class FakeReviewRepository:
    def __init__(self) -> None:
        self.items: dict[str, tuple] = {}

    def append(self, run_id: str, review: object) -> None:
        self.items[run_id] = self.items.get(run_id, ()) + (review,)

    def list_for_run(self, run_id: str) -> tuple:
        return self.items.get(run_id, ())


class FakeActionRepository:
    def __init__(self) -> None:
        self.actions: dict[str, tuple] = {}
        self.receipts: dict[str, tuple] = {}

    def append_action(self, run_id: str, action: object) -> None:
        self.actions[run_id] = self.actions.get(run_id, ()) + (action,)

    def append_receipt(self, run_id: str, receipt: object) -> None:
        self.receipts[run_id] = self.receipts.get(run_id, ()) + (receipt,)

    def list_for_run(self, run_id: str) -> tuple:
        return self.actions.get(run_id, ())

    def list_receipts(self, run_id: str) -> tuple:
        return self.receipts.get(run_id, ())

    def find_receipt(self, run_id: str, idempotency_key: str):
        return next(
            (
                item
                for item in self.receipts.get(run_id, ())
                if item.idempotency_key == idempotency_key
            ),
            None,
        )


class FakeInvestigationRepository:
    def __init__(self) -> None:
        self.items: dict[tuple[str, str], tuple] = {}

    def append(self, result: object) -> None:
        key = (result.run_id, result.case_id)
        self.items[key] = self.items.get(key, ()) + (result,)

    def list_for_case(self, run_id: str, case_id: str) -> tuple:
        return self.items.get((run_id, case_id), ())


class FakeAuditRepository:
    def __init__(self) -> None:
        self.items: list[AuditEvent] = []

    def append(self, event: AuditEvent) -> None:
        self.items.append(event)

    def list_for_run(self, run_id: str) -> tuple[AuditEvent, ...]:
        return tuple(item for item in self.items if item.run_id == run_id)


class FakeIngestionRepository:
    def append_file_result(
        self,
        run_id: str,
        validation: object,
        normalization: object,
        control_totals: object,
    ) -> None:
        del run_id, validation, normalization, control_totals

    def list_issues(self, run_id: str) -> tuple:
        del run_id
        return ()


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.runs = FakeRunRepository()
        self.source_files = FakeSourceFileRepository()
        self.events = FakeEventRepository()
        self.decisions = FakeDecisionRepository()
        self.exceptions = FakeExceptionRepository()
        self.reconciliation = FakeReconciliationRunRepository()
        self.reviews = FakeReviewRepository()
        self.actions = FakeActionRepository()
        self.investigations = FakeInvestigationRepository()
        self.audit = FakeAuditRepository()
        self.ingestion = FakeIngestionRepository()

    def __enter__(self) -> FakeUnitOfWork:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        del exc_type, exc, traceback


def test_fake_repositories_implement_replaceable_ports_and_append_snapshots() -> None:
    fake = FakeUnitOfWork()
    assert isinstance(fake, PersistenceUnitOfWork)
    assert isinstance(fake.runs, RunRepository)
    assert isinstance(fake.source_files, SourceFileRepository)
    assert isinstance(fake.events, EventRepository)
    assert isinstance(fake.decisions, DecisionRepository)
    assert isinstance(fake.exceptions, ExceptionRepository)
    assert isinstance(fake.reconciliation, ReconciliationRunRepository)
    assert isinstance(fake.reviews, ReviewRepository)
    assert isinstance(fake.actions, ActionRepository)
    assert isinstance(fake.investigations, InvestigationRepository)
    assert isinstance(fake.audit, AuditRepository)
    assert isinstance(fake.ingestion, IngestionRepository)

    created = RunManifest(
        "fake-run",
        RunState.CREATED,
        0,
        "policy-v1",
        "rules-v1",
        (),
        (),
        "test",
        datetime(2026, 8, 27, tzinfo=UTC),
    )
    fake.runs.append(created)
    fake.runs.append(created)
    assert fake.runs.get("fake-run") == created
    assert len(fake.runs.items["fake-run"]) == 2
