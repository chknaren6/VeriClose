"""Typed, source-neutral contracts shared by all ingestion adapters."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePath

from core.vericlose.domain.enums import SourceType
from core.vericlose.domain.events import CanonicalEvent, RawScalar
from core.vericlose.domain.money import Money


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} cannot be blank")


def _require_non_negative_int(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} cannot be negative")


def _require_sha256(value: str, field_name: str) -> None:
    _require_text(value, field_name)
    try:
        decoded = bytes.fromhex(value)
    except ValueError as error:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest") from error
    if len(decoded) != 32:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


class SourceFormat(StrEnum):
    CSV = "CSV"
    XLSX = "XLSX"
    UNKNOWN = "UNKNOWN"


class ValidationStage(StrEnum):
    FILE = "FILE"
    SCHEMA = "SCHEMA"
    SEMANTIC = "SEMANTIC"
    ACCOUNTING = "ACCOUNTING"
    CROSS_SOURCE = "CROSS_SOURCE"


class IssueSeverity(StrEnum):
    WARNING = "WARNING"
    ERROR = "ERROR"


class RowDispositionStatus(StrEnum):
    NORMALIZED = "NORMALIZED"
    QUARANTINED = "QUARANTINED"


@dataclass(frozen=True, slots=True)
class SourceDocument:
    """Immutable uploaded bytes plus integrity metadata; adapters never receive a path."""

    file_id: str
    original_name: str
    media_type: str
    sha256: str
    content: bytes

    def __post_init__(self) -> None:
        for value, field_name in (
            (self.file_id, "file_id"),
            (self.original_name, "original_name"),
            (self.media_type, "media_type"),
            (self.sha256, "sha256"),
        ):
            _require_text(value, field_name)
        if not isinstance(self.content, bytes):
            raise TypeError("content must be immutable bytes")
        actual_hash = hashlib.sha256(self.content).hexdigest()
        if actual_hash != self.sha256.lower():
            raise ValueError("sha256 does not match source content")

    @classmethod
    def from_bytes(
        cls,
        *,
        file_id: str,
        original_name: str,
        media_type: str,
        content: bytes,
    ) -> SourceDocument:
        return cls(
            file_id=file_id,
            original_name=original_name,
            media_type=media_type,
            sha256=hashlib.sha256(content).hexdigest(),
            content=content,
        )

    @property
    def extension(self) -> str:
        return PurePath(self.original_name).suffix.lower()


@dataclass(frozen=True, slots=True)
class MappingProfileRef:
    """Stable mapping identity propagated through validation, events, and run manifests."""

    profile_id: str
    version: str
    source_type: SourceType

    def __post_init__(self) -> None:
        _require_text(self.profile_id, "profile_id")
        _require_text(self.version, "version")
        if not isinstance(self.source_type, SourceType):
            raise TypeError("source_type must be a SourceType")

    @property
    def versioned_id(self) -> str:
        return f"{self.profile_id}@{self.version}"


@dataclass(frozen=True, slots=True)
class DetectionReason:
    code: str
    message: str
    weight_bps: int

    def __post_init__(self) -> None:
        _require_text(self.code, "code")
        _require_text(self.message, "message")
        if isinstance(self.weight_bps, bool) or not isinstance(self.weight_bps, int):
            raise TypeError("weight_bps must be an integer")
        if not -10_000 <= self.weight_bps <= 10_000:
            raise ValueError("weight_bps must be between -10_000 and 10_000")


@dataclass(frozen=True, slots=True)
class DetectionResult:
    adapter_id: str
    adapter_version: str
    source_type: SourceType
    source_format: SourceFormat
    confidence_bps: int
    reasons: tuple[DetectionReason, ...]
    candidate_profiles: tuple[MappingProfileRef, ...]

    def __post_init__(self) -> None:
        _require_text(self.adapter_id, "adapter_id")
        _require_text(self.adapter_version, "adapter_version")
        if not isinstance(self.source_type, SourceType):
            raise TypeError("source_type must be a SourceType")
        if not isinstance(self.source_format, SourceFormat):
            raise TypeError("source_format must be a SourceFormat")
        if isinstance(self.confidence_bps, bool) or not isinstance(self.confidence_bps, int):
            raise TypeError("confidence_bps must be an integer")
        if not 0 <= self.confidence_bps <= 10_000:
            raise ValueError("confidence_bps must be between 0 and 10_000")
        if not isinstance(self.reasons, tuple) or not isinstance(self.candidate_profiles, tuple):
            raise TypeError("reasons and candidate_profiles must be immutable tuples")
        if any(not isinstance(reason, DetectionReason) for reason in self.reasons):
            raise TypeError("reasons can contain only DetectionReason values")
        if any(not isinstance(profile, MappingProfileRef) for profile in self.candidate_profiles):
            raise TypeError("candidate_profiles can contain only MappingProfileRef values")
        if self.confidence_bps > 0 and not self.reasons:
            raise ValueError("a positive detection score must include reasons")
        if any(profile.source_type is not self.source_type for profile in self.candidate_profiles):
            raise ValueError("candidate mapping profiles must match detected source_type")


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    stage: ValidationStage
    severity: IssueSeverity
    code: str
    message: str
    file_id: str
    table_name: str | None
    row_number: int | None
    field_name: str | None
    supplied_value: RawScalar
    suggested_fix: str
    blocking: bool

    def __post_init__(self) -> None:
        for value, field_name in (
            (self.code, "code"),
            (self.message, "message"),
            (self.file_id, "file_id"),
            (self.suggested_fix, "suggested_fix"),
        ):
            _require_text(value, field_name)
        if not isinstance(self.stage, ValidationStage):
            raise TypeError("stage must be a ValidationStage")
        if not isinstance(self.severity, IssueSeverity):
            raise TypeError("severity must be an IssueSeverity")
        if not isinstance(self.blocking, bool):
            raise TypeError("blocking must be a boolean")
        if self.row_number is not None:
            if isinstance(self.row_number, bool) or not isinstance(self.row_number, int):
                raise TypeError("row_number must be an integer or None")
            if self.row_number < 1:
                raise ValueError("row_number must be >= 1")
        if self.blocking and self.severity is not IssueSeverity.ERROR:
            raise ValueError("only ERROR issues can be blocking")
        if self.table_name is not None:
            _require_text(self.table_name, "table_name")
        if self.field_name is not None:
            _require_text(self.field_name, "field_name")
        if isinstance(self.supplied_value, float):
            raise TypeError("supplied decimal values must be preserved as strings, not floats")


@dataclass(frozen=True, slots=True)
class ValidationReport:
    adapter_id: str
    adapter_version: str
    source_file_id: str
    mapping_profile: MappingProfileRef
    rows_seen: int
    issues: tuple[ValidationIssue, ...]

    def __post_init__(self) -> None:
        for value, field_name in (
            (self.adapter_id, "adapter_id"),
            (self.adapter_version, "adapter_version"),
            (self.source_file_id, "source_file_id"),
        ):
            _require_text(value, field_name)
        _require_non_negative_int(self.rows_seen, "rows_seen")
        if not isinstance(self.mapping_profile, MappingProfileRef):
            raise TypeError("mapping_profile must be a MappingProfileRef")
        if not isinstance(self.issues, tuple):
            raise TypeError("issues must be an immutable tuple")
        if any(not isinstance(issue, ValidationIssue) for issue in self.issues):
            raise TypeError("issues can contain only ValidationIssue values")
        if any(issue.file_id != self.source_file_id for issue in self.issues):
            raise ValueError("all validation issues must reference source_file_id")

    @property
    def is_valid(self) -> bool:
        return not any(issue.blocking for issue in self.issues)

    @property
    def can_normalize_valid_rows(self) -> bool:
        """File/schema blockers stop parsing; row blockers can be quarantined."""

        return not any(issue.blocking and issue.row_number is None for issue in self.issues)

    @property
    def quarantined_row_numbers(self) -> tuple[int, ...]:
        return tuple(
            sorted(
                {
                    issue.row_number
                    for issue in self.issues
                    if issue.blocking and issue.row_number is not None
                }
            )
        )


@dataclass(frozen=True, slots=True)
class NormalizationContext:
    run_id: str
    legal_entity_id: str
    currency: str = "INR"

    def __post_init__(self) -> None:
        _require_text(self.run_id, "run_id")
        _require_text(self.legal_entity_id, "legal_entity_id")
        normalized_currency = Money(0, self.currency).currency
        object.__setattr__(self, "currency", normalized_currency)


@dataclass(frozen=True, slots=True)
class RowDisposition:
    row_number: int
    status: RowDispositionStatus
    event_ids: tuple[str, ...]
    issue_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if isinstance(self.row_number, bool) or not isinstance(self.row_number, int):
            raise TypeError("row_number must be an integer")
        if self.row_number < 1:
            raise ValueError("row_number must be >= 1")
        if not isinstance(self.status, RowDispositionStatus):
            raise TypeError("status must be a RowDispositionStatus")
        if not isinstance(self.event_ids, tuple) or not isinstance(self.issue_codes, tuple):
            raise TypeError("event_ids and issue_codes must be immutable tuples")
        for event_id in self.event_ids:
            _require_text(event_id, "event_id")
        for issue_code in self.issue_codes:
            _require_text(issue_code, "issue_code")
        if len(set(self.event_ids)) != len(self.event_ids):
            raise ValueError("event IDs cannot be repeated within a row disposition")
        if len(set(self.issue_codes)) != len(self.issue_codes):
            raise ValueError("issue codes cannot be repeated within a row disposition")
        if self.status is RowDispositionStatus.NORMALIZED:
            if not self.event_ids or self.issue_codes:
                raise ValueError("NORMALIZED rows require event IDs and no issue codes")
        elif self.event_ids or not self.issue_codes:
            raise ValueError("QUARANTINED rows require issue codes and no event IDs")


@dataclass(frozen=True, slots=True)
class NormalizationResult:
    adapter_id: str
    adapter_version: str
    source_file_id: str
    source_file_sha256: str
    mapping_profile: MappingProfileRef
    rows_seen: int
    events: tuple[CanonicalEvent, ...]
    row_dispositions: tuple[RowDisposition, ...]
    issues: tuple[ValidationIssue, ...]

    def __post_init__(self) -> None:
        for value, field_name in (
            (self.adapter_id, "adapter_id"),
            (self.adapter_version, "adapter_version"),
            (self.source_file_id, "source_file_id"),
            (self.source_file_sha256, "source_file_sha256"),
        ):
            _require_text(value, field_name)
        _require_sha256(self.source_file_sha256, "source_file_sha256")
        _require_non_negative_int(self.rows_seen, "rows_seen")
        if not isinstance(self.mapping_profile, MappingProfileRef):
            raise TypeError("mapping_profile must be a MappingProfileRef")
        if not all(
            isinstance(value, tuple) for value in (self.events, self.row_dispositions, self.issues)
        ):
            raise TypeError("events, row_dispositions, and issues must be immutable tuples")
        if len(self.row_dispositions) != self.rows_seen:
            raise ValueError("every input row must have exactly one row disposition")
        if any(not isinstance(event, CanonicalEvent) for event in self.events):
            raise TypeError("events can contain only CanonicalEvent values")
        if any(not isinstance(item, RowDisposition) for item in self.row_dispositions):
            raise TypeError("row_dispositions can contain only RowDisposition values")
        if any(not isinstance(issue, ValidationIssue) for issue in self.issues):
            raise TypeError("issues can contain only ValidationIssue values")
        if any(issue.file_id != self.source_file_id for issue in self.issues):
            raise ValueError("all normalization issues must reference source_file_id")

        row_numbers = [item.row_number for item in self.row_dispositions]
        if len(set(row_numbers)) != len(row_numbers):
            raise ValueError("row dispositions must have unique row numbers")
        event_ids = [event.event_id for event in self.events]
        if len(set(event_ids)) != len(event_ids):
            raise ValueError("normalized event IDs must be unique")
        disposition_event_ids = [
            event_id for disposition in self.row_dispositions for event_id in disposition.event_ids
        ]
        if sorted(event_ids) != sorted(disposition_event_ids):
            raise ValueError("every normalized event must belong to one row disposition")

        if any(issue.blocking and issue.row_number is None for issue in self.issues):
            raise ValueError("file-level blockers must be fixed before normalization")
        row_issue_keys = {(issue.row_number, issue.code) for issue in self.issues if issue.blocking}
        cited_issue_keys = {
            (disposition.row_number, code)
            for disposition in self.row_dispositions
            for code in disposition.issue_codes
        }
        if cited_issue_keys != row_issue_keys:
            raise ValueError("every row blocker must have a matching quarantined disposition")
        for event in self.events:
            if event.lineage.source_file_id != self.source_file_id:
                raise ValueError("event lineage source_file_id does not match result")
            if event.lineage.file_sha256.lower() != self.source_file_sha256.lower():
                raise ValueError("event lineage file hash does not match result")
            if event.mapping_profile_version != self.mapping_profile.versioned_id:
                raise ValueError("event mapping version does not match normalization result")

    @property
    def normalized_row_count(self) -> int:
        return sum(
            disposition.status is RowDispositionStatus.NORMALIZED
            for disposition in self.row_dispositions
        )

    @property
    def quarantined_row_count(self) -> int:
        return self.rows_seen - self.normalized_row_count


@dataclass(frozen=True, slots=True)
class ControlTotal:
    component: str
    currency: str
    amount_minor: int
    record_count: int

    def __post_init__(self) -> None:
        _require_text(self.component, "component")
        _require_text(self.currency, "currency")
        _require_non_negative_int(self.amount_minor, "amount_minor")
        _require_non_negative_int(self.record_count, "record_count")


@dataclass(frozen=True, slots=True)
class ControlTotals:
    source_type: SourceType
    event_count: int
    components: tuple[ControlTotal, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.source_type, SourceType):
            raise TypeError("source_type must be a SourceType")
        _require_non_negative_int(self.event_count, "event_count")
        if not isinstance(self.components, tuple):
            raise TypeError("components must be an immutable tuple")
        names = [component.component for component in self.components]
        if len(set(names)) != len(names):
            raise ValueError("control-total component names must be unique")
