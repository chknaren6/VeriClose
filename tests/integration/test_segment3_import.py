from __future__ import annotations

from datetime import UTC, datetime
from functools import partial
from pathlib import Path

import duckdb
import pytest

from core.vericlose.adapters import AdapterRegistry, BankAdapter, ErpGlAdapter, GatewayAdapter
from core.vericlose.audit.events import AuditEvent
from core.vericlose.domain.actions import ProposedAction, ReviewDecision
from core.vericlose.domain.enums import ActionState, ActionType, ReviewState, RunState, SourceType
from core.vericlose.domain.evidence import EvidenceLink
from core.vericlose.infrastructure.duckdb import DuckDBUnitOfWork
from core.vericlose.infrastructure.local_file_store import LocalFileStore
from core.vericlose.ingestion.contracts import NormalizationContext, SourceDocument
from core.vericlose.ingestion.mappings import MappingCatalog
from core.vericlose.ingestion.service import DuplicateUploadError, ImportBatchService
from synthetic.base_case import SyntheticConfig
from synthetic.generate import generate


def _registry() -> AdapterRegistry:
    catalog = MappingCatalog.from_directory(Path("config/mappings"))
    return AdapterRegistry(
        (
            GatewayAdapter(catalog.for_source(SourceType.GATEWAY)),
            BankAdapter(catalog.for_source(SourceType.BANK)),
            ErpGlAdapter(catalog.for_source(SourceType.ERP)),
        )
    )


def _documents(input_dir: Path) -> tuple[SourceDocument, ...]:
    return tuple(
        SourceDocument.from_bytes(
            file_id=file_id,
            original_name=filename,
            media_type="text/csv",
            content=(input_dir / filename).read_bytes(),
        )
        for file_id, filename in (
            ("gateway", "gateway.csv"),
            ("bank", "bank.csv"),
            ("erp", "erp_gl.csv"),
        )
    )


def test_generated_batch_passes_complete_import_and_persistence_loop(tmp_path: Path) -> None:
    generated = tmp_path / "generated"
    manifest = generate(
        SyntheticConfig(seed=73, payments=60, settlements=14, exception_rate=0.3),
        generated,
    )
    database = tmp_path / "vericlose.duckdb"
    storage = tmp_path / "storage"
    service = ImportBatchService(
        _registry(),
        LocalFileStore(storage),
        partial(DuckDBUnitOfWork, database),
    )
    documents = _documents(generated / "inputs")
    result = service.import_batch(
        run_id="run-segment3-a",
        documents=documents,
        context=NormalizationContext("run-segment3-a", "merchant-in"),
        seed=73,
        imported_at=datetime(2026, 8, 27, tzinfo=UTC),
    )

    expected_count = manifest["control_totals"]["row_counts"]["total"]
    assert result.is_ready
    assert result.manifest.state is RunState.VALIDATED
    assert len(result.events) == expected_count
    assert sum(file.validation.rows_seen for file in result.files) == expected_count
    assert all(file.validation.is_valid for file in result.files)
    assert all(
        file.normalization and file.normalization.quarantined_row_count == 0
        for file in result.files
    )
    assert dict(result.manifest.mapping_versions) == {
        "BANK": "bank_debit_credit@1.0.0",
        "ERP": "erp_gl_standard@1.0.0",
        "GATEWAY": "gateway_standard@1.0.0",
    }

    with DuckDBUnitOfWork(database) as repositories:
        assert repositories.runs.get("run-segment3-a") == result.manifest
        restored = repositories.events.list_for_run("run-segment3-a")
        stored_files = repositories.source_files.list_for_run("run-segment3-a")
        persisted_issues = repositories.ingestion.list_issues("run-segment3-a")
    assert restored == tuple(sorted(result.events, key=lambda event: event.event_id))
    assert len(stored_files) == 3
    expected_issues = sorted(
        (issue.file_id, issue.code)
        for file_result in result.files
        for issue in file_result.validation.issues
    )
    assert sorted((issue.file_id, issue.code) for issue in persisted_issues) == expected_issues
    assert all(
        event.lineage.source_file_id in {item.source_file.file_id for item in stored_files}
        for event in restored
    )

    # Re-importing identical evidence is legal only as a new immutable run/version.
    second = service.import_batch(
        run_id="run-segment3-b",
        documents=documents,
        context=NormalizationContext("run-segment3-b", "merchant-in"),
        seed=73,
        imported_at=datetime(2026, 8, 27, 0, 1, tzinfo=UTC),
    )
    assert second.is_ready
    assert {event.event_id for event in result.events}.isdisjoint(
        event.event_id for event in second.events
    )


def test_duplicate_upload_hash_is_rejected_before_persistence(tmp_path: Path) -> None:
    content = b"id,amount\n1,100\n"
    documents = (
        SourceDocument.from_bytes(
            file_id="one", original_name="one.csv", media_type="text/csv", content=content
        ),
        SourceDocument.from_bytes(
            file_id="two", original_name="two.csv", media_type="text/csv", content=content
        ),
    )
    service = ImportBatchService(
        _registry(),
        LocalFileStore(tmp_path / "storage"),
        partial(DuckDBUnitOfWork, tmp_path / "db.duckdb"),
    )
    with pytest.raises(DuplicateUploadError) as caught:
        service.import_batch(
            run_id="duplicate-run",
            documents=documents,
            context=NormalizationContext("duplicate-run", "merchant-in"),
        )
    assert caught.value.file_ids == ("one", "two")
    assert not (tmp_path / "db.duckdb").exists()


def test_review_and_action_append_without_mutating_raw_or_canonical_layers(
    tmp_path: Path,
) -> None:
    generated = tmp_path / "generated"
    generate(SyntheticConfig(seed=74, payments=50, settlements=14, exception_rate=0), generated)
    database = tmp_path / "vericlose.duckdb"
    service = ImportBatchService(
        _registry(),
        LocalFileStore(tmp_path / "storage"),
        partial(DuckDBUnitOfWork, database),
    )
    result = service.import_batch(
        run_id="append-only-run",
        documents=_documents(generated / "inputs"),
        context=NormalizationContext("append-only-run", "merchant-in"),
    )
    evidence_event = result.events[0]
    evidence = EvidenceLink(
        evidence_event.event_id,
        evidence_event.lineage.source_file_id,
        evidence_event.lineage.table_name,
        evidence_event.lineage.row_number,
        evidence_event.lineage.raw_row_hash,
        "review source",
    )
    action = ProposedAction(
        "action-1",
        ActionType.NO_ACTION,
        "case-1",
        ActionState.PROPOSED,
        None,
        (),
        (evidence,),
        datetime(2026, 8, 27, tzinfo=UTC),
    )
    review = ReviewDecision(
        "review-1",
        action.action_id,
        ReviewState.APPROVED,
        "reviewer-1",
        datetime(2026, 8, 27, 0, 1, tzinfo=UTC),
        "Evidence checked",
    )
    with DuckDBUnitOfWork(database) as repositories:
        before_files = repositories.source_files.list_for_run("append-only-run")
        before_events = repositories.events.list_for_run("append-only-run")
        repositories.actions.append_action("append-only-run", action)
        repositories.reviews.append("append-only-run", review)
    with DuckDBUnitOfWork(database) as repositories:
        assert repositories.source_files.list_for_run("append-only-run") == before_files
        assert repositories.events.list_for_run("append-only-run") == before_events
        assert repositories.connection.execute("SELECT count(*) FROM actions").fetchone()[0] == 1
        assert repositories.connection.execute("SELECT count(*) FROM reviews").fetchone()[0] == 1


def test_duckdb_unit_of_work_rolls_back_on_failure(tmp_path: Path) -> None:
    database = tmp_path / "rollback.duckdb"
    with (
        pytest.raises(RuntimeError, match="force rollback"),
        DuckDBUnitOfWork(database) as repositories,
    ):
        repositories.audit.append(
            AuditEvent(
                "audit-rollback",
                "run-rollback",
                "TEST",
                datetime(2026, 8, 27, tzinfo=UTC),
            )
        )
        raise RuntimeError("force rollback")
    connection = duckdb.connect(str(database), read_only=True)
    try:
        assert connection.execute("SELECT count(*) FROM audit_events").fetchone()[0] == 0
    finally:
        connection.close()
