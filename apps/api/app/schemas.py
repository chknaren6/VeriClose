"""Stable HTTP contracts expressed in VeriClose domain terminology."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str
    message: str
    field: str | None = None
    suggested_fix: str | None = None


class ErrorEnvelope(BaseModel):
    error: ErrorDetail


class UploadDocument(BaseModel):
    file_id: Literal["gateway", "bank", "erp"]
    original_name: str = Field(min_length=1, max_length=255)
    media_type: str = Field(min_length=1, max_length=100)
    content_base64: str = Field(min_length=1)


class AdapterConfirmationRequest(BaseModel):
    file_id: Literal["gateway", "bank", "erp"]
    adapter_id: str
    profile_versioned_id: str


class UploadBatchRequest(BaseModel):
    run_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{2,79}$")
    legal_entity_id: str = Field(default="demo-merchant-in", min_length=1, max_length=100)
    documents: list[UploadDocument] = Field(min_length=1, max_length=3)
    confirmations: list[AdapterConfirmationRequest] = Field(default_factory=list)


class DetectionCandidateResponse(BaseModel):
    adapter_id: str
    profile_versioned_id: str
    confidence_bps: int
    reasons: list[str]


class FileDetectionResponse(BaseModel):
    file_id: str
    requires_confirmation: bool
    candidates: list[DetectionCandidateResponse]


class DetectionBatchResponse(BaseModel):
    files: list[FileDetectionResponse]


class ValidationIssueResponse(BaseModel):
    stage: str
    severity: str
    code: str
    message: str
    file_id: str
    table_name: str | None
    row_number: int | None
    field_name: str | None
    supplied_value: str | int | bool | None
    suggested_fix: str
    blocking: bool


class MappingFieldResponse(BaseModel):
    canonical_field: str
    source_column: str | None
    required: bool
    transform: str


class ControlTotalResponse(BaseModel):
    component: str
    currency: str
    amount_minor: int
    record_count: int


class ImportedFileResponse(BaseModel):
    file_id: str
    original_name: str
    source_type: str
    adapter_id: str
    profile_versioned_id: str
    explicitly_confirmed: bool
    rows_seen: int
    is_valid: bool
    mapping: list[MappingFieldResponse]
    sample_rows: list[dict[str, Any]]
    issues: list[ValidationIssueResponse]
    control_totals: list[ControlTotalResponse]


class ImportBatchResponse(BaseModel):
    run_id: str
    state: str
    is_ready: bool
    event_count: int
    files: list[ImportedFileResponse]
    cross_source_issues: list[ValidationIssueResponse]


class StartRunRequest(BaseModel):
    run_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{2,79}$")


class SourceFileResponse(BaseModel):
    file_id: str
    source_type: str
    original_name: str
    sha256: str
    size_bytes: int
    adapter_id: str
    mapping_profile_version: str


class StageTimingResponse(BaseModel):
    stage: str
    duration_ms: int
    input_count: int
    output_count: int


class OperationalSummaryResponse(BaseModel):
    decision_count: int
    verified_count: int
    review_or_exception_count: int
    amount_at_risk_minor: int
    currency: Literal["INR"] = "INR"
    stage_timings: list[StageTimingResponse]


class RunResponse(BaseModel):
    run_id: str
    state: str
    policy_version: str
    rule_version: str
    created_at: str
    files: list[SourceFileResponse]
    validation_issues: list[ValidationIssueResponse]
    operational_summary: OperationalSummaryResponse | None
    benchmark_accuracy_available: bool = False


class ReviewResponse(BaseModel):
    review_id: str
    state: str
    reviewer_id: str
    reviewed_at: str
    comment: str | None


class CaseListItemResponse(BaseModel):
    case_id: str
    decision_id: str
    state: str
    proof_level: str
    reason_code: str | None
    severity: str | None
    amount_at_risk_minor: int
    currency: Literal["INR"] = "INR"
    recommended_action: str | None
    requires_company_input: bool
    latest_review: ReviewResponse | None


class EventResponse(BaseModel):
    event_id: str
    source_type: str
    source_record_id: str
    event_type: str
    amount_minor: int
    currency: str
    direction: str
    event_at: str
    value_date: str | None
    external_reference: str | None
    settlement_reference: str | None
    bank_utr: str | None
    account_code: str | None
    narration: str | None
    source_file_id: str
    table_name: str
    row_number: int
    raw_fields: dict[str, str | int | bool | None]


class EvidenceResponse(BaseModel):
    event_id: str | None
    source_file_id: str
    table_name: str
    row_number: int
    raw_row_hash: str
    purpose: str


class ProofCheckResponse(BaseModel):
    check_code: str
    expected: str | int | bool | None
    observed: str | int | bool | None
    tolerance_minor: int | None
    passed: bool
    required: bool
    evidence: list[EvidenceResponse]


class CaseDetailResponse(CaseListItemResponse):
    uniqueness_passed: bool
    contradiction_reason: str | None
    policy_allows_auto_clear: bool
    rules_attempted: list[str]
    events: list[EventResponse]
    evidence: list[EvidenceResponse]
    proof_checks: list[ProofCheckResponse]
    reviews: list[ReviewResponse]
    advisory: dict[str, str]


class ReviewRequest(BaseModel):
    state: Literal["APPROVED", "REJECTED", "EDIT_REQUESTED", "DEFERRED", "INFORMATION_REQUESTED"]
    reviewer_id: str = Field(min_length=1, max_length=100)
    comment: str | None = Field(default=None, max_length=2000)


class OperationalMetricsResponse(BaseModel):
    run_id: str
    kind: Literal["operational"] = "operational"
    summary: OperationalSummaryResponse
    reason_distribution: dict[str, int]
    proof_distribution: dict[str, int]
    accuracy_claims: None = None
