"""Application-level import loop: detect → validate → normalize → persist."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from core.vericlose.adapters.registry import AdapterRegistry, SelectedAdapter
from core.vericlose.audit.events import AuditEvent
from core.vericlose.domain.enums import RunState, SourceType
from core.vericlose.domain.events import CanonicalEvent
from core.vericlose.domain.runs import RunManifest, SourceFile
from core.vericlose.ingestion.contracts import (
    ControlTotals,
    NormalizationContext,
    NormalizationResult,
    SourceDocument,
    ValidationReport,
)
from core.vericlose.ingestion.validation import (
    CrossSourceValidationReport,
    validate_cross_source_readiness,
)
from core.vericlose.ports.file_store import FileStore, StoredFile
from core.vericlose.ports.repositories import PersistenceUnitOfWork, SourceFileRecord


class DuplicateUploadError(ValueError):
    def __init__(self, file_ids: tuple[str, ...], sha256: str) -> None:
        super().__init__(f"duplicate upload content for files {file_ids}: {sha256}")
        self.file_ids = file_ids
        self.sha256 = sha256


class RunAlreadyExistsError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class AdapterConfirmation:
    file_id: str
    adapter_id: str
    profile_versioned_id: str


@dataclass(frozen=True, slots=True)
class FileImportResult:
    document: SourceDocument
    selected: SelectedAdapter
    validation: ValidationReport
    normalization: NormalizationResult | None
    control_totals: ControlTotals | None
    stored_file: StoredFile


@dataclass(frozen=True, slots=True)
class ImportBatchResult:
    manifest: RunManifest
    files: tuple[FileImportResult, ...]
    events: tuple[CanonicalEvent, ...]
    cross_source: CrossSourceValidationReport

    @property
    def is_ready(self) -> bool:
        return self.manifest.state is RunState.VALIDATED


class ImportBatchService:
    def __init__(
        self,
        registry: AdapterRegistry,
        file_store: FileStore,
        unit_of_work: Callable[[], PersistenceUnitOfWork],
    ) -> None:
        self._registry = registry
        self._file_store = file_store
        self._unit_of_work = unit_of_work

    def import_batch(
        self,
        *,
        run_id: str,
        documents: tuple[SourceDocument, ...],
        context: NormalizationContext,
        confirmations: tuple[AdapterConfirmation, ...] = (),
        policy_version: str = "razorpay_inr_v1@1.0.0",
        rule_version: str = "segment4-v1",
        seed: int = 0,
        build_commit: str = "local",
        imported_at: datetime | None = None,
    ) -> ImportBatchResult:
        if context.run_id != run_id:
            raise ValueError("normalization context run_id must match import run_id")
        if not documents:
            raise ValueError("at least one source document is required")
        self._reject_duplicate_content(documents)
        with self._unit_of_work() as repositories:
            if repositories.runs.get(run_id) is not None:
                raise RunAlreadyExistsError(f"run already exists: {run_id}")
        timestamp = imported_at or datetime.now(UTC)
        confirmation_by_file = {item.file_id: item for item in confirmations}
        if len(confirmation_by_file) != len(confirmations):
            raise ValueError("adapter confirmations must have unique file IDs")

        prepared: list[FileImportResult] = []
        all_events: list[CanonicalEvent] = []
        source_files: list[SourceFile] = []
        mapping_versions: dict[str, str] = {}
        for document in documents:
            confirmation = confirmation_by_file.get(document.file_id)
            selected = self._registry.select(
                document,
                confirmed_adapter_id=confirmation.adapter_id if confirmation else None,
                confirmed_profile_versioned_id=(
                    confirmation.profile_versioned_id if confirmation else None
                ),
            )
            validation = selected.adapter.validate(document, selected.mapping_profile)
            normalization: NormalizationResult | None = None
            totals: ControlTotals | None = None
            if validation.can_normalize_valid_rows:
                normalization = selected.adapter.normalize(
                    document,
                    selected.mapping_profile,
                    context,
                )
                totals = selected.adapter.control_totals(normalization.events)
                all_events.extend(normalization.events)
            stored = self._file_store.put(run_id, document)
            source_file = SourceFile(
                document.file_id,
                selected.adapter.source_type,
                document.sha256,
                document.original_name,
                len(document.content),
                timestamp,
            )
            source_files.append(source_file)
            mapping_versions[selected.adapter.source_type.value] = (
                selected.mapping_profile.ref.versioned_id
            )
            prepared.append(
                FileImportResult(
                    document,
                    selected,
                    validation,
                    normalization,
                    totals,
                    stored,
                )
            )

        events = tuple(all_events)
        cross_source = validate_cross_source_readiness(events)
        has_source_errors = any(not item.validation.is_valid for item in prepared)
        final_state = (
            RunState.FAILED_VALIDATION
            if has_source_errors or not cross_source.is_ready
            else RunState.VALIDATED
        )
        created = RunManifest(
            run_id=run_id,
            state=RunState.CREATED,
            seed=seed,
            policy_version=policy_version,
            rule_version=rule_version,
            mapping_versions=tuple(sorted(mapping_versions.items())),
            input_files=(),
            build_commit=build_commit,
            created_at=timestamp,
        )
        attached = created.with_files(tuple(source_files))
        final_manifest = attached.transition(final_state)

        with self._unit_of_work() as repositories:
            repositories.runs.append(created)
            repositories.runs.append(attached)
            for item, source_file in zip(prepared, source_files, strict=True):
                if repositories.source_files.exists_hash(run_id, source_file.sha256):
                    raise DuplicateUploadError((source_file.file_id,), source_file.sha256)
                repositories.source_files.add(
                    SourceFileRecord(
                        run_id,
                        source_file,
                        item.selected.adapter.adapter_id,
                        item.selected.adapter.adapter_version,
                        item.selected.mapping_profile.ref.versioned_id,
                        item.stored_file.relative_path,
                    )
                )
                repositories.ingestion.append_file_result(
                    run_id,
                    item.validation,
                    item.normalization,
                    item.control_totals,
                )
            repositories.events.append(run_id, events)
            repositories.runs.append(final_manifest)
            repositories.audit.append(
                AuditEvent(
                    audit_id=f"{run_id}:import",
                    run_id=run_id,
                    event_type="IMPORT_COMPLETED"
                    if final_state is RunState.VALIDATED
                    else "IMPORT_FAILED_VALIDATION",
                    occurred_at=timestamp,
                    details=(
                        ("file_count", str(len(prepared))),
                        ("event_count", str(len(events))),
                        ("state", final_state.value),
                    ),
                )
            )
        return ImportBatchResult(final_manifest, tuple(prepared), events, cross_source)

    @staticmethod
    def _reject_duplicate_content(documents: tuple[SourceDocument, ...]) -> None:
        by_hash: dict[str, list[str]] = {}
        for document in documents:
            by_hash.setdefault(document.sha256, []).append(document.file_id)
        duplicate = next(
            ((sha256, ids) for sha256, ids in by_hash.items() if len(ids) > 1),
            None,
        )
        if duplicate:
            sha256, file_ids = duplicate
            raise DuplicateUploadError(tuple(file_ids), sha256)


def required_source_types(result: ImportBatchResult) -> frozenset[SourceType]:
    return frozenset(item.selected.adapter.source_type for item in result.files)
