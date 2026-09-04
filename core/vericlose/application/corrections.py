"""Approved mock-entry import and full deterministic re-verification."""

from __future__ import annotations

import csv
import io
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256

from core.vericlose.application.actions import ActionQueryService
from core.vericlose.application.review_cases import CaseView, ReviewQueryService
from core.vericlose.application.run_reconciliation import RunReconciliationService
from core.vericlose.audit.events import AuditEvent
from core.vericlose.domain.actions import ActionReceipt
from core.vericlose.domain.enums import ActionState, ActionType, Direction, SourceType
from core.vericlose.ingestion.contracts import NormalizationContext, SourceDocument
from core.vericlose.ingestion.service import AdapterConfirmation, ImportBatchService
from core.vericlose.ports.file_store import FileStore, StoredFile
from core.vericlose.ports.repositories import PersistenceUnitOfWork, SourceFileRecord


@dataclass(frozen=True, slots=True)
class CorrectionResult:
    previous_run_id: str
    new_run_id: str
    previous_case_id: str
    new_case_id: str | None
    previous_proof_level: str
    new_proof_level: str | None
    resolved: bool
    receipt: ActionReceipt


class CorrectionService:
    """Applies an approved journal to a new mock ERP source version and replays the batch."""

    def __init__(
        self,
        actions: ActionQueryService,
        cases: ReviewQueryService,
        importer: ImportBatchService,
        reconciler: RunReconciliationService,
        file_store: FileStore,
        unit_of_work: Callable[[], PersistenceUnitOfWork],
    ) -> None:
        self._actions = actions
        self._cases = cases
        self._importer = importer
        self._reconciler = reconciler
        self._file_store = file_store
        self._unit_of_work = unit_of_work

    def apply_approved_journal(
        self,
        action_id: str,
        new_run_id: str,
        *,
        applied_at: datetime | None = None,
    ) -> CorrectionResult:
        view = self._actions.get(action_id)
        action = view.action
        if action.action_type is not ActionType.JOURNAL_EXPORT or action.journal is None:
            raise ValueError("only a deterministic journal action can create a mock correction")
        if action.state is not ActionState.EXPORTED:
            raise ValueError("journal must be approved and exported before correction import")
        timestamp = applied_at or datetime.now(UTC)
        prior_case = self._cases.get_case(action.case_id)
        source_files, manifest, prior_events = self._source_context(view.run_id)
        erp_record = next(
            item for item in source_files if item.source_file.source_type is SourceType.ERP
        )
        erp_bytes = self._read_source(erp_record)
        corrected_erp = _append_journal(erp_bytes, action)
        correction_sha = sha256(corrected_erp).hexdigest()
        key = f"correction:{action_id}:{correction_sha}"
        with self._unit_of_work() as repositories:
            existing = repositories.actions.find_receipt(view.run_id, key)
        if existing is not None:
            existing_run = dict(existing.result_payload)["new_run_id"]
            return self._result(prior_case, existing_run, existing)

        documents = []
        confirmations = []
        for record in source_files:
            if record.source_file.source_type is SourceType.ERP:
                content = corrected_erp
                original_name = "vericlose-corrected-erp.csv"
                media_type = "text/csv"
            else:
                content = self._read_source(record)
                original_name = record.source_file.original_name
                media_type = _media_type(original_name)
            documents.append(
                SourceDocument.from_bytes(
                    file_id=record.source_file.file_id,
                    original_name=original_name,
                    media_type=media_type,
                    content=content,
                )
            )
            confirmations.append(
                AdapterConfirmation(
                    record.source_file.file_id,
                    record.adapter_id,
                    record.mapping_profile_version,
                )
            )
        legal_entity = prior_events[0].legal_entity_id
        imported = self._importer.import_batch(
            run_id=new_run_id,
            documents=tuple(documents),
            context=NormalizationContext(new_run_id, legal_entity),
            confirmations=tuple(confirmations),
            policy_version=manifest.policy_version,
            rule_version=manifest.rule_version,
            seed=manifest.seed,
            build_commit=manifest.build_commit,
            imported_at=timestamp,
        )
        if not imported.is_ready:
            raise ValueError("corrected ERP import failed validation")
        self._reconciler.run(new_run_id, occurred_at=timestamp)
        receipt_id = f"receipt_{sha256(key.encode()).hexdigest()[:20]}"
        receipt = ActionReceipt(
            receipt_id,
            action_id,
            key,
            timestamp,
            (
                ("new_run_id", new_run_id),
                ("corrected_erp_sha256", correction_sha),
                ("source_run_id", view.run_id),
            ),
        )
        with self._unit_of_work() as repositories:
            repositories.actions.append_receipt(view.run_id, receipt)
            repositories.audit.append(
                AuditEvent(
                    f"audit_{receipt_id}",
                    view.run_id,
                    "CORRECTION_IMPORTED_AND_RERUN",
                    timestamp,
                    (
                        ("action_id", action_id),
                        ("new_run_id", new_run_id),
                        ("corrected_erp_sha256", correction_sha),
                    ),
                )
            )
        return self._result(prior_case, new_run_id, receipt)

    def _source_context(self, run_id: str):
        with self._unit_of_work() as repositories:
            manifest = repositories.runs.get(run_id)
            if manifest is None:
                raise LookupError(run_id)
            source_files = repositories.source_files.list_for_run(run_id)
            events = repositories.events.list_for_run(run_id)
        if not events:
            raise ValueError("source run has no canonical events")
        return source_files, manifest, events

    def _read_source(self, record: SourceFileRecord) -> bytes:
        return self._file_store.get(
            StoredFile(
                record.run_id,
                record.source_file.file_id,
                record.relative_path,
                record.source_file.sha256,
                record.source_file.size_bytes,
            )
        )

    def _result(
        self, prior_case: CaseView, new_run_id: str, receipt: ActionReceipt
    ) -> CorrectionResult:
        new_case = _find_related_case(prior_case, self._cases.list_cases(new_run_id))
        return CorrectionResult(
            prior_case.run_id,
            new_run_id,
            prior_case.case_id,
            new_case.case_id if new_case else None,
            prior_case.decision.proof_level.value,
            new_case.decision.proof_level.value if new_case else None,
            bool(new_case and new_case.decision.policy_allows_auto_clear),
            receipt,
        )


def _append_journal(content: bytes, action) -> bytes:
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    if reader.fieldnames is None:
        raise ValueError("ERP source is missing a header")
    required = {
        "journal_id",
        "line_number",
        "posting_date",
        "account_code",
        "debit_amount",
        "credit_amount",
        "currency",
        "external_reference",
        "narration",
    }
    if set(reader.fieldnames) != required:
        raise ValueError("mock correction requires the configured ERP CSV layout")
    payload = dict(action.payload)
    reference = payload.get("reference", action.case_id)
    posting_date = payload.get("posting_date", datetime.now(UTC).date().isoformat())
    journal_id = f"VC_{action.action_id[-12:]}"
    for number, line in enumerate(action.journal.lines, start=1):
        amount = _rupees(line.money.amount_minor)
        rows.append(
            {
                "journal_id": journal_id,
                "line_number": str(number),
                "posting_date": posting_date,
                "account_code": line.account_code,
                "debit_amount": amount if line.direction is Direction.DEBIT else "0.00",
                "credit_amount": amount if line.direction is Direction.CREDIT else "0.00",
                "currency": line.money.currency,
                "external_reference": reference,
                "narration": f"VeriClose approved mock correction: {line.narration}",
            }
        )
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=reader.fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def _rupees(amount_minor: int) -> str:
    rupees, paise = divmod(amount_minor, 100)
    return f"{rupees}.{paise:02d}"


def _media_type(name: str) -> str:
    return (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        if name.lower().endswith(".xlsx")
        else "text/csv"
    )


def _find_related_case(prior: CaseView, candidates: tuple[CaseView, ...]) -> CaseView | None:
    prior_gateway = {
        event.source_record_id for event in prior.events if event.source_type is SourceType.GATEWAY
    }
    return next(
        (
            candidate
            for candidate in candidates
            if prior_gateway
            & {
                event.source_record_id
                for event in candidate.events
                if event.source_type is SourceType.GATEWAY
            }
        ),
        None,
    )
