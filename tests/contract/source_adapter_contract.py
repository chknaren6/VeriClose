"""Reusable behavioral contract for every concrete source adapter.

Concrete adapter test classes inherit this mixin and provide the five fixtures.
That keeps gateway, bank, and ERP adapters aligned as their parsers evolve.
"""

import pytest

from core.vericlose.ingestion.contracts import (
    MappingProfileRef,
    NormalizationContext,
    SourceDocument,
)
from core.vericlose.ports.source_adapter import MappingProfile, SourceAdapter


class SourceAdapterContract:
    """Assertions all source adapters must pass before they can be registered."""

    @pytest.fixture
    def adapter(self) -> SourceAdapter:
        raise NotImplementedError

    @pytest.fixture
    def mapping_profile(self) -> MappingProfile:
        raise NotImplementedError

    @pytest.fixture
    def valid_document(self) -> SourceDocument:
        raise NotImplementedError

    @pytest.fixture
    def mixed_document(self) -> SourceDocument:
        """Return a document containing at least one valid and one invalid row."""
        raise NotImplementedError

    @pytest.fixture
    def normalization_context(self) -> NormalizationContext:
        raise NotImplementedError

    def test_implements_runtime_ports(
        self,
        adapter: SourceAdapter,
        mapping_profile: MappingProfile,
    ) -> None:
        assert isinstance(adapter, SourceAdapter)
        assert isinstance(mapping_profile, MappingProfile)

    def test_detection_is_typed_and_auditable(
        self,
        adapter: SourceAdapter,
        mapping_profile: MappingProfile,
        valid_document: SourceDocument,
    ) -> None:
        result = adapter.detect(valid_document)

        assert result.adapter_id == adapter.adapter_id
        assert result.adapter_version == adapter.adapter_version
        assert result.source_type is adapter.source_type
        assert result.source_format in adapter.supported_formats
        assert result.confidence_bps > 0
        assert result.reasons
        assert mapping_profile.ref in result.candidate_profiles

    def test_valid_document_normalizes_every_row(
        self,
        adapter: SourceAdapter,
        mapping_profile: MappingProfile,
        valid_document: SourceDocument,
        normalization_context: NormalizationContext,
    ) -> None:
        report = adapter.validate(valid_document, mapping_profile)
        result = adapter.normalize(valid_document, mapping_profile, normalization_context)

        assert report.is_valid
        assert result.rows_seen == report.rows_seen
        assert result.normalized_row_count == report.rows_seen
        assert result.quarantined_row_count == 0
        assert all(
            event.mapping_profile_version == mapping_profile.ref.versioned_id
            for event in result.events
        )

    def test_invalid_rows_are_quarantined_instead_of_silently_dropped(
        self,
        adapter: SourceAdapter,
        mapping_profile: MappingProfile,
        mixed_document: SourceDocument,
        normalization_context: NormalizationContext,
    ) -> None:
        report = adapter.validate(mixed_document, mapping_profile)
        result = adapter.normalize(mixed_document, mapping_profile, normalization_context)

        assert report.can_normalize_valid_rows
        assert result.rows_seen == report.rows_seen
        assert result.normalized_row_count > 0
        assert result.quarantined_row_count > 0
        assert result.normalized_row_count + result.quarantined_row_count == result.rows_seen
        assert set(report.quarantined_row_numbers) == {
            row.row_number for row in result.row_dispositions if row.issue_codes
        }

    def test_control_totals_cover_normalized_events(
        self,
        adapter: SourceAdapter,
        mapping_profile: MappingProfile,
        valid_document: SourceDocument,
        normalization_context: NormalizationContext,
    ) -> None:
        result = adapter.normalize(valid_document, mapping_profile, normalization_context)
        totals = adapter.control_totals(result.events)

        assert totals.source_type is adapter.source_type
        assert totals.event_count == len(result.events)
        assert sum(component.record_count for component in totals.components) == len(result.events)


def assert_profile_identity(ref: MappingProfileRef, profile_id: str, version: str) -> None:
    """Small shared assertion useful in concrete mapping-profile tests."""

    assert ref.profile_id == profile_id
    assert ref.version == version
    assert ref.versioned_id == f"{profile_id}@{version}"
