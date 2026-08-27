"""Shared mechanics for exact-lineage tabular source adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass

from core.vericlose.domain.enums import SourceType
from core.vericlose.domain.events import CanonicalEvent, RawField, RawRowRef
from core.vericlose.ingestion.contracts import (
    ControlTotals,
    DetectionReason,
    DetectionResult,
    IssueSeverity,
    NormalizationContext,
    NormalizationResult,
    RowDisposition,
    RowDispositionStatus,
    SourceDocument,
    SourceFormat,
    ValidationIssue,
    ValidationReport,
    ValidationStage,
)
from core.vericlose.ingestion.mappings import FileMappingProfile, apply_transform
from core.vericlose.ingestion.tabular import (
    TabularData,
    TabularReadError,
    TabularRow,
    detect_format,
    read_tabular,
)
from core.vericlose.ports.source_adapter import MappingProfile


@dataclass(frozen=True, slots=True)
class RowProblem(Exception):
    code: str
    message: str
    canonical_field: str | None
    suggested_fix: str
    stage: ValidationStage = ValidationStage.SEMANTIC


class NormalizationBlockedError(ValueError):
    """Raised when file/schema validation means rows cannot safely be interpreted."""

    def __init__(self, report: ValidationReport) -> None:
        super().__init__("normalization blocked by file or schema validation")
        self.report = report


class TabularSourceAdapter(ABC):
    adapter_version = "1.0.0"
    supported_formats = frozenset({SourceFormat.CSV, SourceFormat.XLSX})

    def __init__(self, profiles: Sequence[FileMappingProfile]) -> None:
        self._profiles = tuple(profiles)
        if not self._profiles:
            raise ValueError("an adapter requires at least one mapping profile")
        if any(profile.ref.source_type is not self.source_type for profile in self._profiles):
            raise ValueError("all mapping profiles must match adapter source_type")

    @property
    def profiles(self) -> tuple[FileMappingProfile, ...]:
        return self._profiles

    @property
    @abstractmethod
    def adapter_id(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def source_type(self) -> SourceType:
        raise NotImplementedError

    def detect(self, document: SourceDocument) -> DetectionResult:
        source_format = detect_format(document)
        if source_format not in self.supported_formats:
            return self._detection(source_format, 0, (), ())
        try:
            data = read_tabular(document)
        except TabularReadError:
            return self._detection(source_format, 0, (), ())
        scored = sorted(
            (
                (profile.match_score_bps(data.headers), profile)
                for profile in self._profiles
                if source_format in profile.supported_formats
            ),
            key=lambda item: (-item[0], item[1].ref.versioned_id),
        )
        candidates = tuple(profile.ref for score, profile in scored if score > 0)
        confidence = scored[0][0] if scored else 0
        reasons = (
            (
                DetectionReason(
                    code="REQUIRED_HEADERS_MATCH",
                    message=f"Required {self.source_type.value} fields resolved from the header",
                    weight_bps=confidence,
                ),
            )
            if confidence
            else ()
        )
        return self._detection(source_format, confidence, reasons, candidates)

    def validate(
        self,
        document: SourceDocument,
        mapping_profile: MappingProfile,
    ) -> ValidationReport:
        try:
            profile = self._profile(mapping_profile)
        except ValueError as error:
            issue = self._issue(
                document,
                None,
                "MAPPING_PROFILE_INVALID",
                str(error),
                None,
                None,
                "Choose a mapping profile for this source and file format",
                ValidationStage.SCHEMA,
            )
            return self._report(document, mapping_profile.ref, 0, (issue,))
        try:
            data = read_tabular(document)
        except TabularReadError as error:
            issue = self._issue(
                document,
                None,
                error.code,
                str(error),
                None,
                None,
                "Upload a valid UTF-8 CSV or XLSX workbook",
                ValidationStage.FILE,
            )
            return self._report(document, profile.ref, 0, (issue,))

        bound = profile.bind(data.headers)
        missing = tuple(
            field for field in bound.required_fields if bound.source_column_for(field) is None
        )
        if missing:
            issue = self._issue(
                document,
                None,
                "REQUIRED_MAPPING_MISSING",
                f"Required canonical fields are unresolved: {', '.join(missing)}",
                None,
                None,
                "Select a compatible profile or map every required field",
                ValidationStage.SCHEMA,
                table_name=data.table_name,
            )
            return self._report(document, bound.ref, len(data.rows), (issue,))

        issues: list[ValidationIssue] = []
        for row in data.rows:
            try:
                self._parse_row(row, bound)
            except RowProblem as problem:
                source_column = (
                    bound.source_column_for(problem.canonical_field)
                    if problem.canonical_field
                    else None
                )
                issues.append(
                    self._issue(
                        document,
                        row.row_number,
                        problem.code,
                        problem.message,
                        source_column,
                        row.get(source_column) if source_column else None,
                        problem.suggested_fix,
                        problem.stage,
                        table_name=row.table_name,
                    )
                )
        issues.extend(self._batch_issues(document, data, bound, tuple(issues)))
        return self._report(document, bound.ref, len(data.rows), tuple(issues))

    def normalize(
        self,
        document: SourceDocument,
        mapping_profile: MappingProfile,
        context: NormalizationContext,
    ) -> NormalizationResult:
        profile = self._profile(mapping_profile)
        data = read_tabular(document)
        bound = profile.bind(data.headers)
        report = self.validate(document, bound)
        if not report.can_normalize_valid_rows:
            raise NormalizationBlockedError(report)

        issues = list(report.issues)
        issues_by_row = self._issues_by_row(issues)
        events: list[CanonicalEvent] = []
        dispositions: list[RowDisposition] = []
        for row in data.rows:
            if row.row_number not in issues_by_row:
                try:
                    parsed = self._parse_row(row, bound)
                    event = self._build_event(document, row, bound, context, parsed)
                except (RowProblem, TypeError, ValueError) as error:
                    problem = (
                        error
                        if isinstance(error, RowProblem)
                        else RowProblem(
                            "NORMALIZATION_FAILED",
                            str(error),
                            None,
                            "Correct this row and import it again",
                        )
                    )
                    source_column = (
                        bound.source_column_for(problem.canonical_field)
                        if problem.canonical_field
                        else None
                    )
                    issue = self._issue(
                        document,
                        row.row_number,
                        problem.code,
                        problem.message,
                        source_column,
                        row.get(source_column) if source_column else None,
                        problem.suggested_fix,
                        problem.stage,
                        table_name=row.table_name,
                    )
                    issues.append(issue)
                    issues_by_row.setdefault(row.row_number, []).append(issue)
                else:
                    events.append(event)
                    dispositions.append(
                        RowDisposition(
                            row.row_number,
                            RowDispositionStatus.NORMALIZED,
                            (event.event_id,),
                            (),
                        )
                    )
                    continue
            row_issues = issues_by_row[row.row_number]
            dispositions.append(
                RowDisposition(
                    row.row_number,
                    RowDispositionStatus.QUARANTINED,
                    (),
                    tuple(dict.fromkeys(issue.code for issue in row_issues if issue.blocking)),
                )
            )
        return NormalizationResult(
            adapter_id=self.adapter_id,
            adapter_version=self.adapter_version,
            source_file_id=document.file_id,
            source_file_sha256=document.sha256,
            mapping_profile=bound.ref,
            rows_seen=len(data.rows),
            events=tuple(events),
            row_dispositions=tuple(dispositions),
            issues=tuple(issues),
        )

    @abstractmethod
    def control_totals(self, events: Sequence[CanonicalEvent]) -> ControlTotals:
        raise NotImplementedError

    @abstractmethod
    def _parse_row(self, row: TabularRow, profile: FileMappingProfile) -> object:
        raise NotImplementedError

    @abstractmethod
    def _build_event(
        self,
        document: SourceDocument,
        row: TabularRow,
        profile: FileMappingProfile,
        context: NormalizationContext,
        parsed: object,
    ) -> CanonicalEvent:
        raise NotImplementedError

    def _batch_issues(
        self,
        document: SourceDocument,
        data: TabularData,
        profile: FileMappingProfile,
        row_issues: tuple[ValidationIssue, ...],
    ) -> tuple[ValidationIssue, ...]:
        del document, data, profile, row_issues
        return ()

    def _profile(self, mapping_profile: MappingProfile) -> FileMappingProfile:
        if not isinstance(mapping_profile, FileMappingProfile):
            raise ValueError("adapter requires a validated FileMappingProfile")
        if mapping_profile.ref.source_type is not self.source_type:
            raise ValueError("mapping profile belongs to another source type")
        return mapping_profile

    def _mapped(self, row: TabularRow, profile: FileMappingProfile, field: str) -> object:
        source_column = profile.source_column_for(field)
        if source_column is None:
            return ""
        transform = profile.transform_for(field) or "strip"
        try:
            return apply_transform(transform, row.get(source_column))
        except (TypeError, ValueError) as error:
            raise RowProblem(
                code=f"{field.upper()}_INVALID",
                message=f"{field} could not be parsed: {error}",
                canonical_field=field,
                suggested_fix=f"Supply a value accepted by the {transform} transform",
            ) from error

    def _lineage(self, document: SourceDocument, row: TabularRow) -> RawRowRef:
        return RawRowRef(
            document.file_id,
            document.sha256,
            row.table_name,
            row.row_number,
            row.raw_row_hash,
        )

    @staticmethod
    def _raw_fields(row: TabularRow) -> tuple[RawField, ...]:
        return tuple(RawField(name, value) for name, value in row.values)

    def _event_id(self, context: NormalizationContext, source_record_id: str) -> str:
        return f"{context.run_id}:{self.source_type.value}:{source_record_id}"

    def _detection(
        self,
        source_format: SourceFormat,
        confidence_bps: int,
        reasons: tuple[DetectionReason, ...],
        profiles: tuple,
    ) -> DetectionResult:
        return DetectionResult(
            self.adapter_id,
            self.adapter_version,
            self.source_type,
            source_format,
            confidence_bps,
            reasons,
            profiles,
        )

    def _report(
        self,
        document: SourceDocument,
        profile_ref,
        rows_seen: int,
        issues: tuple[ValidationIssue, ...],
    ) -> ValidationReport:
        return ValidationReport(
            self.adapter_id,
            self.adapter_version,
            document.file_id,
            profile_ref,
            rows_seen,
            issues,
        )

    @staticmethod
    def _issues_by_row(
        issues: list[ValidationIssue],
    ) -> dict[int, list[ValidationIssue]]:
        grouped: dict[int, list[ValidationIssue]] = {}
        for issue in issues:
            if issue.blocking and issue.row_number is not None:
                grouped.setdefault(issue.row_number, []).append(issue)
        return grouped

    def _issue(
        self,
        document: SourceDocument,
        row_number: int | None,
        code: str,
        message: str,
        field_name: str | None,
        supplied_value: str | None,
        suggested_fix: str,
        stage: ValidationStage,
        *,
        table_name: str | None = None,
        blocking: bool = True,
    ) -> ValidationIssue:
        return ValidationIssue(
            stage=stage,
            severity=IssueSeverity.ERROR,
            code=code,
            message=message,
            file_id=document.file_id,
            table_name=table_name,
            row_number=row_number,
            field_name=field_name,
            supplied_value=supplied_value,
            suggested_fix=suggested_fix,
            blocking=blocking,
        )
