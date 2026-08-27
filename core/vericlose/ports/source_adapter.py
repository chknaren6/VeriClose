"""Port contracts implemented by every source-file adapter.

Adapters own source-specific knowledge: file shape, column names, and transforms.
The rest of VeriClose consumes only canonical events and typed reports.
"""

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from core.vericlose.domain.enums import SourceType
from core.vericlose.domain.events import CanonicalEvent
from core.vericlose.ingestion.contracts import (
    ControlTotals,
    DetectionResult,
    MappingProfileRef,
    NormalizationContext,
    NormalizationResult,
    SourceDocument,
    SourceFormat,
    ValidationReport,
)


@runtime_checkable
class MappingProfile(Protocol):
    """Versioned instructions for mapping one source layout to canonical fields.

    The concrete profile schema belongs to S3.5. Keeping this as a small port
    lets S3.1 define version propagation without prematurely choosing YAML,
    JSON, or database-backed configuration.
    """

    @property
    def ref(self) -> MappingProfileRef:
        """Return the immutable identity and version of this mapping."""
        ...

    def source_column_for(self, canonical_field: str) -> str | None:
        """Return the source column mapped to a canonical field, if configured."""
        ...

    def transform_for(self, canonical_field: str) -> str | None:
        """Return the named transform configured for a canonical field."""
        ...


@runtime_checkable
class SourceAdapter(Protocol):
    """Boundary between variable source files and VeriClose's canonical model."""

    @property
    def adapter_id(self) -> str:
        """Return a stable adapter identifier used in audit evidence."""
        ...

    @property
    def adapter_version(self) -> str:
        """Return the implementation version used for this decision."""
        ...

    @property
    def source_type(self) -> SourceType:
        """Return the source type emitted by this adapter."""
        ...

    @property
    def supported_formats(self) -> frozenset[SourceFormat]:
        """Return formats this adapter can inspect and normalize."""
        ...

    def detect(self, document: SourceDocument) -> DetectionResult:
        """Score whether this adapter and its profiles can read the document."""
        ...

    def validate(
        self,
        document: SourceDocument,
        mapping_profile: MappingProfile,
    ) -> ValidationReport:
        """Validate file, schema, semantic, and accounting constraints."""
        ...

    def normalize(
        self,
        document: SourceDocument,
        mapping_profile: MappingProfile,
        context: NormalizationContext,
    ) -> NormalizationResult:
        """Normalize valid rows and quarantine every invalid row explicitly."""
        ...

    def control_totals(self, events: Sequence[CanonicalEvent]) -> ControlTotals:
        """Compute source-specific totals used to prove normalization completeness."""
        ...
