from __future__ import annotations

import csv
from datetime import UTC, datetime
from functools import partial
from pathlib import Path

import pytest

from core.vericlose.adapters import AdapterRegistry, BankAdapter, ErpGlAdapter, GatewayAdapter
from core.vericlose.application.actions import ActionQueryService, ActionService
from core.vericlose.application.corrections import CorrectionService
from core.vericlose.application.review_cases import ReviewQueryService
from core.vericlose.application.run_reconciliation import RunReconciliationService
from core.vericlose.domain.enums import ActionState, ActionType, Direction, ReviewState, SourceType
from core.vericlose.infrastructure.duckdb import DuckDBUnitOfWork
from core.vericlose.infrastructure.local_action_exporter import LocalActionExporter
from core.vericlose.infrastructure.local_file_store import LocalFileStore
from core.vericlose.ingestion.contracts import NormalizationContext, SourceDocument
from core.vericlose.ingestion.mappings import MappingCatalog
from core.vericlose.ingestion.service import ImportBatchService
from core.vericlose.reconciliation.policy import load_policy
from synthetic.base_case import SyntheticConfig
from synthetic.generate import generate


def _services(tmp_path: Path):
    generated = tmp_path / "generated"
    generate(SyntheticConfig(), generated)
    policy = load_policy(Path("config/policies/razorpay_inr_v1.yaml"))
    catalog = MappingCatalog.from_directory(Path("config/mappings"))
    registry = AdapterRegistry(
        (
            GatewayAdapter(catalog.for_source(SourceType.GATEWAY)),
            BankAdapter(catalog.for_source(SourceType.BANK)),
            ErpGlAdapter(catalog.for_source(SourceType.ERP)),
        )
    )
    data_dir = tmp_path / "files"
    file_store = LocalFileStore(data_dir)
    unit_of_work = partial(DuckDBUnitOfWork, tmp_path / "actions.duckdb")
    importer = ImportBatchService(registry, file_store, unit_of_work)
    reconciler = RunReconciliationService(policy, unit_of_work)
    documents = tuple(
        SourceDocument.from_bytes(
            file_id=file_id,
            original_name=filename,
            media_type="text/csv",
            content=(generated / "inputs" / filename).read_bytes(),
        )
        for file_id, filename in (
            ("gateway", "gateway.csv"),
            ("bank", "bank.csv"),
            ("erp", "erp_gl.csv"),
        )
    )
    importer.import_batch(
        run_id="action-source",
        documents=documents,
        context=NormalizationContext("action-source", "demo-merchant-in"),
        policy_version=policy.versioned_id,
    )
    reconciler.run("action-source")
    cases = ReviewQueryService(unit_of_work)
    action_query = ActionQueryService(unit_of_work)
    actions = ActionService(
        cases,
        action_query,
        policy,
        LocalActionExporter(data_dir),
        unit_of_work,
    )
    corrections = CorrectionService(
        action_query,
        cases,
        importer,
        reconciler,
        file_store,
        unit_of_work,
    )
    return data_dir, cases, actions, action_query, corrections


def test_balanced_action_requires_approval_and_exports_idempotently(tmp_path: Path) -> None:
    data_dir, cases, actions, action_query, _corrections = _services(tmp_path)
    case = next(
        item
        for item in cases.list_cases("action-source")
        if item.exception and item.exception.reason_code == "MISSING_ERP_POSTING"
    )
    proposal = actions.propose(case.case_id, proposed_at=datetime(2026, 9, 2, tzinfo=UTC))
    assert proposal.action_type is ActionType.JOURNAL_EXPORT
    assert proposal.journal is not None
    assert sum(
        line.money.amount_minor
        for line in proposal.journal.lines
        if line.direction is Direction.DEBIT
    ) == sum(
        line.money.amount_minor
        for line in proposal.journal.lines
        if line.direction is Direction.CREDIT
    )
    with pytest.raises(ValueError, match="approved"):
        actions.export(proposal.action_id)

    approved = actions.review(
        proposal.action_id,
        state=ReviewState.APPROVED,
        reviewer_id="controller-01",
        comment="Evidence and accounts checked",
        reviewed_at=datetime(2026, 9, 2, 0, 1, tzinfo=UTC),
    )
    assert approved.action.state is ActionState.APPROVED
    first = actions.export(proposal.action_id, exported_at=datetime(2026, 9, 2, 0, 2, tzinfo=UTC))
    second = actions.export(proposal.action_id)
    assert first == second
    exported = data_dir / dict(first.result_payload)["relative_path"]
    rows = list(csv.DictReader(exported.read_text(encoding="utf-8").splitlines()))
    assert sum(int(row["amount_minor"]) for row in rows if row["direction"] == "DEBIT") == sum(
        int(row["amount_minor"]) for row in rows if row["direction"] == "CREDIT"
    )
    assert action_query.get(proposal.action_id).action.state is ActionState.EXPORTED


def test_approved_mock_correction_creates_new_version_and_resolves_case(tmp_path: Path) -> None:
    _data_dir, cases, actions, _action_query, corrections = _services(tmp_path)
    old_case = next(
        item
        for item in cases.list_cases("action-source")
        if item.exception and item.exception.reason_code == "MISSING_ERP_POSTING"
    )
    proposal = actions.propose(old_case.case_id)
    actions.review(
        proposal.action_id,
        state=ReviewState.APPROVED,
        reviewer_id="controller-01",
        comment="Post approved mock entry",
    )
    actions.export(proposal.action_id)

    result = corrections.apply_approved_journal(proposal.action_id, "action-corrected")
    assert result.previous_run_id == "action-source"
    assert result.new_run_id == "action-corrected"
    assert result.previous_proof_level == "SUPPORTED"
    assert result.new_proof_level == "PROVED"
    assert result.resolved
    assert cases.get_case(old_case.case_id).decision.proof_level.value == "SUPPORTED"

    repeated = corrections.apply_approved_journal(proposal.action_id, "ignored-second-id")
    assert repeated.receipt == result.receipt
    assert repeated.new_run_id == "action-corrected"


def test_clarification_export_is_approved_evidence_backed_and_non_mutating(
    tmp_path: Path,
) -> None:
    data_dir, cases, actions, action_query, _corrections = _services(tmp_path)
    case = next(
        item
        for item in cases.list_cases("action-source")
        if item.exception and item.exception.recommended_action is ActionType.CLARIFICATION_REQUEST
    )
    proposal = actions.propose(case.case_id)
    assert proposal.action_type is ActionType.CLARIFICATION_REQUEST
    approved = actions.review(
        proposal.action_id,
        state=ReviewState.APPROVED,
        reviewer_id="controller-02",
        comment="Send the evidence-backed question",
        edits={"clarification_text": "Please confirm the cited synthetic settlement evidence."},
    )
    assert approved.action.state is ActionState.APPROVED
    receipt = actions.export(proposal.action_id)
    content = (data_dir / dict(receipt.result_payload)["relative_path"]).read_text(
        encoding="utf-8"
    )
    assert "Evidence clarification request" in content
    assert case.case_id in content
    assert "does not mutate source data" in content
    assert action_query.get(proposal.action_id).action.state is ActionState.EXPORTED
    assert cases.get_case(case.case_id).decision == case.decision
