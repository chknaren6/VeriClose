from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime
from functools import partial
from pathlib import Path

import duckdb
import pytest

from core.vericlose.adapters import AdapterRegistry, BankAdapter, ErpGlAdapter, GatewayAdapter
from core.vericlose.application.run_reconciliation import RunReconciliationService
from core.vericlose.domain.enums import ProofLevel, RunState, SourceType
from core.vericlose.infrastructure.duckdb import DuckDBUnitOfWork
from core.vericlose.infrastructure.local_file_store import LocalFileStore
from core.vericlose.ingestion.contracts import NormalizationContext, SourceDocument
from core.vericlose.ingestion.mappings import MappingCatalog
from core.vericlose.ingestion.service import ImportBatchService
from core.vericlose.reconciliation.pipeline import reconcile
from core.vericlose.reconciliation.policy import load_policy
from synthetic.base_case import SyntheticConfig
from synthetic.generate import generate
from synthetic.truth.models import TruthDataset, source_key


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


def test_complete_batch_matches_every_hidden_scenario_without_false_clears(
    tmp_path: Path,
) -> None:
    generated = tmp_path / "generated"
    generate(SyntheticConfig(), generated)
    truth = TruthDataset.from_dict(
        json.loads(
            (generated / "private" / "ground_truth.json").read_text(encoding="utf-8")
        )
    )
    policy = load_policy(Path("config/policies/razorpay_inr_v1.yaml"))
    database = tmp_path / "segment4.duckdb"
    unit_of_work = partial(DuckDBUnitOfWork, database)
    imported = ImportBatchService(
        _registry(), LocalFileStore(tmp_path / "files"), unit_of_work
    ).import_batch(
        run_id="segment4-full-batch",
        documents=_documents(generated / "inputs"),
        context=NormalizationContext("segment4-full-batch", "demo-merchant-in"),
        policy_version=policy.versioned_id,
        rule_version="segment4-v1",
        seed=42,
        imported_at=datetime(2026, 8, 27, tzinfo=UTC),
    )
    result = RunReconciliationService(policy, unit_of_work).run(
        imported.manifest.run_id,
        occurred_at=datetime(2026, 8, 27, 0, 1, tzinfo=UTC),
    )
    assert result.manifest.state is RunState.COMPLETED
    assert len(imported.events) == 315
    assert len(result.kernel.decisions) == len(truth.case_labels) == 25

    event_by_id = {event.event_id: event for event in imported.events}
    predicted = {
        frozenset(
            source_key(event_by_id[event_id].source_type, event_by_id[event_id].source_record_id)
            for event_id in decision.event_ids
        ): decision
        for decision in result.kernel.decisions
    }
    exception_by_members = {
        frozenset(link.event_id for link in exception.evidence_links): exception
        for exception in result.kernel.exceptions
    }
    for expected in truth.case_labels:
        decision = predicted[frozenset(expected.expected_member_keys)]
        assert decision.proof_level is expected.expected_proof_level, expected.scenario
        if expected.expected_proof_level is ProofLevel.PROVED:
            assert decision.policy_allows_auto_clear, expected.scenario
        else:
            assert not decision.policy_allows_auto_clear, expected.scenario
            exception = exception_by_members[frozenset(decision.event_ids)]
            assert exception.category is expected.expected_exception_category, expected.scenario
            assert exception.severity is expected.expected_severity, expected.scenario
            assert exception.recommended_action is expected.expected_next_action, expected.scenario
        if expected.scenario == "mistyped_reference":
            assert any(
                check.check_code.startswith("SUPPORT_") for check in decision.proof_checks
            )
            assert decision.proof_level is ProofLevel.SUPPORTED

    reversed_result = reconcile(tuple(reversed(imported.events)), policy)
    assert reversed_result.decisions == result.kernel.decisions
    assert reversed_result.exceptions == result.kernel.exceptions

    with DuckDBUnitOfWork(database) as repositories:
        assert repositories.runs.get(imported.manifest.run_id).state is RunState.COMPLETED
        assert repositories.decisions.list_for_run(imported.manifest.run_id) == tuple(
            sorted(result.kernel.decisions, key=lambda item: item.decision_id)
        )
        assert repositories.exceptions.list_for_run(imported.manifest.run_id) == tuple(
            sorted(result.kernel.exceptions, key=lambda item: item.case_id)
        )
        assert repositories.reconciliation.get(imported.manifest.run_id) == result.summary
    connection = duckdb.connect(str(database), read_only=True)
    try:
        proof_count = connection.execute("SELECT count(*) FROM proof_checks").fetchone()[0]
        evidence_count = connection.execute("SELECT count(*) FROM evidence_links").fetchone()[0]
    finally:
        connection.close()
    assert proof_count >= len(result.kernel.decisions)
    assert evidence_count >= len(imported.events)

    bank_line = next(event for event in imported.events if event.account_code == "110000")
    wrong_account = tuple(
        replace(event, account_code="999999") if event.event_id == bank_line.event_id else event
        for event in imported.events
    )
    wrong_result = reconcile(wrong_account, policy)
    wrong_decision = next(
        decision for decision in wrong_result.decisions if bank_line.event_id in decision.event_ids
    )
    assert wrong_decision.proof_level is ProofLevel.CONTRADICTED
    assert not wrong_decision.policy_allows_auto_clear


def test_kernel_failure_leaves_an_explicit_failed_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    generated = tmp_path / "generated"
    generate(
        SyntheticConfig(seed=91, payments=50, settlements=14, exception_rate=0),
        generated,
    )
    policy = load_policy(Path("config/policies/razorpay_inr_v1.yaml"))
    database = tmp_path / "failed.duckdb"
    unit_of_work = partial(DuckDBUnitOfWork, database)
    imported = ImportBatchService(
        _registry(), LocalFileStore(tmp_path / "files"), unit_of_work
    ).import_batch(
        run_id="segment4-failed",
        documents=_documents(generated / "inputs"),
        context=NormalizationContext("segment4-failed", "demo-merchant-in"),
        policy_version=policy.versioned_id,
    )

    def fail_kernel(*args, **kwargs):
        del args, kwargs
        raise RuntimeError("synthetic kernel failure")

    monkeypatch.setattr(
        "core.vericlose.application.run_reconciliation.reconcile", fail_kernel
    )
    with pytest.raises(RuntimeError, match="synthetic kernel failure"):
        RunReconciliationService(policy, unit_of_work).run(imported.manifest.run_id)
    with DuckDBUnitOfWork(database) as repositories:
        assert repositories.runs.get(imported.manifest.run_id).state is RunState.FAILED
        assert repositories.decisions.list_for_run(imported.manifest.run_id) == ()
