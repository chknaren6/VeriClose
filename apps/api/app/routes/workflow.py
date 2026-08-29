"""Segment 6 import, reconciliation, evidence, metrics, and review routes."""

from __future__ import annotations

import base64
import binascii
import json
from collections import Counter
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request, status

from apps.api.app.schemas import (
    CaseDetailResponse,
    CaseListItemResponse,
    ControlTotalResponse,
    DetectionBatchResponse,
    DetectionCandidateResponse,
    ErrorEnvelope,
    EventResponse,
    EvidenceResponse,
    FileDetectionResponse,
    ImportBatchResponse,
    ImportedFileResponse,
    MappingFieldResponse,
    OperationalMetricsResponse,
    OperationalSummaryResponse,
    ProofCheckResponse,
    ReviewRequest,
    ReviewResponse,
    RunResponse,
    SourceFileResponse,
    StageTimingResponse,
    StartRunRequest,
    UploadBatchRequest,
    ValidationIssueResponse,
)
from core.vericlose.application.review_cases import CaseView, RunView
from core.vericlose.domain.enums import ReviewState
from core.vericlose.ingestion.contracts import NormalizationContext, SourceDocument
from core.vericlose.ingestion.service import AdapterConfirmation, ImportBatchResult

router = APIRouter(prefix="/api/v1", tags=["finance workflow"])
ERRORS = {
    400: {"model": ErrorEnvelope},
    404: {"model": ErrorEnvelope},
    409: {"model": ErrorEnvelope},
}


class WorkflowError(Exception):
    def __init__(self, code: str, message: str, http_status: int, suggested_fix: str | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status
        self.suggested_fix = suggested_fix


@router.post("/uploads/detect", response_model=DetectionBatchResponse, responses=ERRORS)
async def detect_uploads(payload: UploadBatchRequest, request: Request) -> DetectionBatchResponse:
    documents = _documents(payload, request)
    registry = request.app.state.container.adapter_registry
    files = []
    for document in documents:
        summary = registry.detect(document)
        files.append(
            FileDetectionResponse(
                file_id=document.file_id,
                requires_confirmation=summary.requires_confirmation,
                candidates=[
                    DetectionCandidateResponse(
                        adapter_id=item.adapter_id,
                        profile_versioned_id=item.profile_versioned_id,
                        confidence_bps=item.confidence_bps,
                        reasons=list(item.reasons),
                    )
                    for item in summary.candidates
                ],
            )
        )
    return DetectionBatchResponse(files=files)


@router.post(
    "/uploads",
    response_model=ImportBatchResponse,
    status_code=status.HTTP_201_CREATED,
    responses=ERRORS,
)
async def import_uploads(payload: UploadBatchRequest, request: Request) -> ImportBatchResponse:
    container = request.app.state.container
    result = container.import_batch.import_batch(
        run_id=payload.run_id,
        documents=_documents(payload, request),
        context=NormalizationContext(payload.run_id, payload.legal_entity_id),
        confirmations=tuple(
            AdapterConfirmation(item.file_id, item.adapter_id, item.profile_versioned_id)
            for item in payload.confirmations
        ),
        policy_version=container.reconciliation_policy.versioned_id,
        rule_version=container.settings.rule_version,
        seed=container.settings.deterministic_seed,
        build_commit=container.settings.build_commit,
    )
    return _import_response(result)


@router.post("/runs", response_model=RunResponse, responses=ERRORS)
async def start_run(payload: StartRunRequest, request: Request) -> RunResponse:
    container = request.app.state.container
    container.run_reconciliation.run(payload.run_id)
    return _run_response(container.review_query.get_run(payload.run_id))


@router.get("/runs/{run_id}", response_model=RunResponse, responses=ERRORS)
async def get_run(run_id: str, request: Request) -> RunResponse:
    return _run_response(request.app.state.container.review_query.get_run(run_id))


@router.get("/runs/{run_id}/cases", response_model=list[CaseListItemResponse], responses=ERRORS)
async def list_cases(run_id: str, request: Request) -> list[CaseListItemResponse]:
    cases = request.app.state.container.review_query.list_cases(run_id)
    severity = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, None: 0}
    ordered = sorted(
        cases,
        key=lambda item: (
            -severity[item.exception.severity.value if item.exception else None],
            -(item.exception.amount_at_risk.amount_minor if item.exception else 0),
            item.case_id,
        ),
    )
    return [_case_item(item) for item in ordered]


@router.get("/cases/{case_id}", response_model=CaseDetailResponse, responses=ERRORS)
async def get_case(case_id: str, request: Request) -> CaseDetailResponse:
    return _case_detail(request.app.state.container.review_query.get_case(case_id), request)


@router.get("/cases/{case_id}/evidence", response_model=list[EvidenceResponse], responses=ERRORS)
async def get_evidence(case_id: str, request: Request) -> list[EvidenceResponse]:
    case = request.app.state.container.review_query.get_case(case_id)
    return [_evidence(item) for item in case.decision.evidence_links]


@router.get(
    "/cases/{case_id}/proof-checks", response_model=list[ProofCheckResponse], responses=ERRORS
)
async def get_proof_checks(case_id: str, request: Request) -> list[ProofCheckResponse]:
    case = request.app.state.container.review_query.get_case(case_id)
    return [_proof_check(item) for item in case.decision.proof_checks]


@router.post(
    "/cases/{case_id}/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    responses=ERRORS,
)
async def record_review(case_id: str, payload: ReviewRequest, request: Request) -> ReviewResponse:
    review = request.app.state.container.preliminary_review.record(
        case_id,
        state=ReviewState(payload.state),
        reviewer_id=payload.reviewer_id,
        comment=payload.comment,
    )
    return _review(review)


@router.get("/runs/{run_id}/metrics", response_model=OperationalMetricsResponse, responses=ERRORS)
async def operational_metrics(run_id: str, request: Request) -> OperationalMetricsResponse:
    container = request.app.state.container
    view = container.review_query.get_run(run_id)
    if view.summary is None:
        raise WorkflowError("RUN_NOT_COMPLETED", "Operational metrics are not ready", 409)
    cases = container.review_query.list_cases(run_id)
    return OperationalMetricsResponse(
        run_id=run_id,
        summary=_operational_summary(view),
        reason_distribution=dict(
            sorted(Counter(item.exception.reason_code for item in cases if item.exception).items())
        ),
        proof_distribution=dict(
            sorted(Counter(item.decision.proof_level.value for item in cases).items())
        ),
    )


@router.get("/benchmarks/latest", responses=ERRORS)
async def latest_benchmark(request: Request) -> dict[str, Any]:
    settings = request.app.state.container.settings
    if settings.environment != "benchmark":
        raise WorkflowError(
            "BENCHMARK_MODE_REQUIRED",
            "Benchmark results are isolated from operational mode",
            404,
        )
    report = Path("evaluation/reports/benchmark-latest.json")
    if not report.is_file():
        raise WorkflowError("BENCHMARK_NOT_FOUND", "No benchmark report is available", 404)
    return json.loads(report.read_text(encoding="utf-8"))


def _documents(payload: UploadBatchRequest, request: Request) -> tuple[SourceDocument, ...]:
    if len({item.file_id for item in payload.documents}) != len(payload.documents):
        raise WorkflowError("DUPLICATE_FILE_SLOT", "Each source slot may be uploaded once", 400)
    documents = []
    for item in payload.documents:
        try:
            content = base64.b64decode(item.content_base64, validate=True)
        except (binascii.Error, ValueError) as error:
            raise WorkflowError(
                "UPLOAD_BASE64_INVALID", f"{item.file_id} is not valid base64", 400
            ) from error
        if not content:
            raise WorkflowError("UPLOAD_EMPTY", f"{item.file_id} is empty", 400)
        if len(content) > request.app.state.container.settings.upload_max_bytes:
            raise WorkflowError("UPLOAD_TOO_LARGE", f"{item.file_id} exceeds the upload limit", 400)
        if Path(item.original_name).suffix.lower() not in {".csv", ".xlsx"}:
            raise WorkflowError("UPLOAD_FORMAT_UNSUPPORTED", "Only CSV and XLSX are accepted", 400)
        documents.append(
            SourceDocument.from_bytes(
                file_id=item.file_id,
                original_name=Path(item.original_name).name,
                media_type=item.media_type,
                content=content,
            )
        )
    return tuple(documents)


def _issue(item: Any) -> ValidationIssueResponse:
    return ValidationIssueResponse(
        stage=item.stage.value,
        severity=item.severity.value,
        code=item.code,
        message=item.message,
        file_id=item.file_id,
        table_name=item.table_name,
        row_number=item.row_number,
        field_name=item.field_name,
        supplied_value=item.supplied_value,
        suggested_fix=item.suggested_fix,
        blocking=item.blocking,
    )


def _import_response(result: ImportBatchResult) -> ImportBatchResponse:
    files = []
    for item in result.files:
        profile = item.selected.mapping_profile
        samples = []
        if item.normalization:
            for event in item.normalization.events[:3]:
                samples.append({field.name: field.value for field in event.raw_fields})
        files.append(
            ImportedFileResponse(
                file_id=item.document.file_id,
                original_name=item.document.original_name,
                source_type=item.selected.adapter.source_type.value,
                adapter_id=item.selected.adapter.adapter_id,
                profile_versioned_id=profile.ref.versioned_id,
                explicitly_confirmed=item.selected.explicitly_confirmed,
                rows_seen=item.validation.rows_seen,
                is_valid=item.validation.is_valid,
                mapping=[
                    MappingFieldResponse(
                        canonical_field=field.canonical_field,
                        source_column=profile.source_column_for(field.canonical_field),
                        required=field.required,
                        transform=field.transform,
                    )
                    for field in profile.fields
                ],
                sample_rows=samples,
                issues=[_issue(issue) for issue in item.validation.issues],
                control_totals=[
                    ControlTotalResponse(
                        component=total.component,
                        currency=total.currency,
                        amount_minor=total.amount_minor,
                        record_count=total.record_count,
                    )
                    for total in (item.control_totals.components if item.control_totals else ())
                ],
            )
        )
    return ImportBatchResponse(
        run_id=result.manifest.run_id,
        state=result.manifest.state.value,
        is_ready=result.is_ready,
        event_count=len(result.events),
        files=files,
        cross_source_issues=[_issue(issue) for issue in result.cross_source.issues],
    )


def _run_response(view: RunView) -> RunResponse:
    return RunResponse(
        run_id=view.manifest.run_id,
        state=view.manifest.state.value,
        policy_version=view.manifest.policy_version,
        rule_version=view.manifest.rule_version,
        created_at=view.manifest.created_at.isoformat(),
        files=[
            SourceFileResponse(
                file_id=item.source_file.file_id,
                source_type=item.source_file.source_type.value,
                original_name=item.source_file.original_name,
                sha256=item.source_file.sha256,
                size_bytes=item.source_file.size_bytes,
                adapter_id=item.adapter_id,
                mapping_profile_version=item.mapping_profile_version,
            )
            for item in view.source_files
        ],
        validation_issues=[_issue(item) for item in view.validation_issues],
        operational_summary=_operational_summary(view) if view.summary else None,
    )


def _operational_summary(view: RunView) -> OperationalSummaryResponse:
    assert view.summary is not None
    return OperationalSummaryResponse(
        decision_count=view.summary.decision_count,
        verified_count=view.summary.auto_cleared_count,
        review_or_exception_count=view.summary.exception_count,
        amount_at_risk_minor=view.summary.amount_at_risk_minor,
        stage_timings=[
            StageTimingResponse(stage=a, duration_ms=b, input_count=c, output_count=d)
            for a, b, c, d in view.summary.stage_timings
        ],
    )


def _case_item(case: CaseView) -> CaseListItemResponse:
    exception = case.exception
    return CaseListItemResponse(
        case_id=case.case_id,
        decision_id=case.decision.decision_id,
        state=case.decision.state.value,
        proof_level=case.decision.proof_level.value,
        reason_code=exception.reason_code if exception else None,
        severity=exception.severity.value if exception else None,
        amount_at_risk_minor=exception.amount_at_risk.amount_minor if exception else 0,
        recommended_action=exception.recommended_action.value if exception else None,
        requires_company_input=exception.requires_company_input if exception else False,
        latest_review=_review(case.reviews[-1]) if case.reviews else None,
    )


def _case_detail(case: CaseView, request: Request) -> CaseDetailResponse:
    item = _case_item(case)
    return CaseDetailResponse(
        **item.model_dump(),
        uniqueness_passed=case.decision.uniqueness_passed,
        contradiction_reason=case.decision.contradiction_reason,
        policy_allows_auto_clear=case.decision.policy_allows_auto_clear,
        rules_attempted=list(case.exception.rules_attempted if case.exception else ()),
        events=[_event(event) for event in case.events],
        evidence=[_evidence(link) for link in case.decision.evidence_links],
        proof_checks=[_proof_check(check) for check in case.decision.proof_checks],
        reviews=[_review(review) for review in case.reviews],
        advisory={
            "status": "model-enabled"
            if request.app.state.container.settings.model_enabled
            else "unavailable",
            "message": (
                "AI explanation is optional; deterministic proof above remains authoritative."
            ),
        },
    )


def _event(item: Any) -> EventResponse:
    return EventResponse(
        event_id=item.event_id,
        source_type=item.source_type.value,
        source_record_id=item.source_record_id,
        event_type=item.event_type.value,
        amount_minor=item.money.amount_minor,
        currency=item.money.currency,
        direction=item.direction.value,
        event_at=item.event_at.isoformat(),
        value_date=item.value_date.isoformat() if item.value_date else None,
        external_reference=item.external_reference,
        settlement_reference=item.settlement_reference,
        bank_utr=item.bank_utr,
        account_code=item.account_code,
        narration=item.narration,
        source_file_id=item.lineage.source_file_id,
        table_name=item.lineage.table_name,
        row_number=item.lineage.row_number,
        raw_fields={field.name: field.value for field in item.raw_fields},
    )


def _evidence(item: Any) -> EvidenceResponse:
    return EvidenceResponse(**{name: getattr(item, name) for name in EvidenceResponse.model_fields})


def _proof_check(item: Any) -> ProofCheckResponse:
    return ProofCheckResponse(
        check_code=item.check_code,
        expected=item.expected,
        observed=item.observed,
        tolerance_minor=item.tolerance_minor,
        passed=item.passed,
        required=item.required,
        evidence=[_evidence(link) for link in item.evidence_links],
    )


def _review(item: Any) -> ReviewResponse:
    return ReviewResponse(
        review_id=item.review_id,
        state=item.state.value,
        reviewer_id=item.reviewer_id,
        reviewed_at=item.reviewed_at.isoformat(),
        comment=item.comment,
    )
