"""Adapter/profile detection with strict ambiguity handling."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass

from core.vericlose.adapters.base import TabularSourceAdapter
from core.vericlose.ingestion.contracts import DetectionResult, SourceDocument
from core.vericlose.ingestion.mappings import FileMappingProfile
from core.vericlose.ingestion.tabular import TabularReadError, detect_format, read_tabular


class DetectionError(ValueError):
    pass


class AmbiguousDetectionError(DetectionError):
    """The caller must explicitly confirm one adapter/profile pair."""


@dataclass(frozen=True, slots=True)
class DetectionCandidate:
    adapter_id: str
    profile_versioned_id: str
    confidence_bps: int
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DetectionSummary:
    candidates: tuple[DetectionCandidate, ...]
    requires_confirmation: bool


@dataclass(frozen=True, slots=True)
class SelectedAdapter:
    adapter: TabularSourceAdapter
    mapping_profile: FileMappingProfile
    detection: DetectionResult
    explicitly_confirmed: bool


class AdapterRegistry:
    def __init__(
        self,
        adapters: tuple[TabularSourceAdapter, ...],
        *,
        threshold_bps: int = 8_000,
        ambiguity_margin_bps: int = 500,
    ) -> None:
        if not adapters:
            raise ValueError("adapter registry cannot be empty")
        identifiers = [adapter.adapter_id for adapter in adapters]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("adapter IDs must be unique")
        self._adapters = adapters
        self._threshold_bps = threshold_bps
        self._ambiguity_margin_bps = ambiguity_margin_bps

    def detect(self, document: SourceDocument) -> DetectionSummary:
        candidates = self._candidates(document)
        if not candidates:
            return DetectionSummary((), True)
        top = candidates[0]
        close = tuple(
            candidate
            for candidate in candidates
            if top.confidence_bps - candidate.confidence_bps <= self._ambiguity_margin_bps
        )
        requires_confirmation = top.confidence_bps < self._threshold_bps or len(close) != 1
        return DetectionSummary(candidates, requires_confirmation)

    def select(
        self,
        document: SourceDocument,
        *,
        confirmed_adapter_id: str | None = None,
        confirmed_profile_versioned_id: str | None = None,
    ) -> SelectedAdapter:
        summary = self.detect(document)
        explicitly_confirmed = bool(confirmed_adapter_id and confirmed_profile_versioned_id)
        if explicitly_confirmed:
            adapter = self._adapter(confirmed_adapter_id)
            profile = next(
                (
                    item
                    for item in adapter.profiles
                    if item.ref.versioned_id == confirmed_profile_versioned_id
                ),
                None,
            )
            if profile is None or detect_format(document) not in profile.supported_formats:
                raise DetectionError("confirmed adapter/profile is not compatible with this file")
            detection = adapter.detect(document)
            with suppress(TabularReadError):
                profile = profile.bind(read_tabular(document).headers)
            # Validation owns precise malformed-file diagnostics. Confirmation is
            # sufficient to route an unreadable file to the intended adapter.
            return SelectedAdapter(adapter, profile, detection, True)
        else:
            if not summary.candidates:
                raise DetectionError("no adapter could recognize the uploaded file")
            if summary.requires_confirmation:
                raise AmbiguousDetectionError(
                    "adapter/profile detection is ambiguous; explicit confirmation is required"
                )
            candidate = summary.candidates[0]

        adapter = self._adapter(candidate.adapter_id)
        profile = next(
            profile
            for profile in adapter.profiles
            if profile.ref.versioned_id == candidate.profile_versioned_id
        )
        bound = profile.bind(read_tabular(document).headers)
        return SelectedAdapter(
            adapter,
            bound,
            adapter.detect(document),
            False,
        )

    def _candidates(self, document: SourceDocument) -> tuple[DetectionCandidate, ...]:
        candidates: list[DetectionCandidate] = []
        for adapter in self._adapters:
            result = adapter.detect(document)
            for profile in result.candidate_profiles:
                candidates.append(
                    DetectionCandidate(
                        adapter.adapter_id,
                        profile.versioned_id,
                        result.confidence_bps,
                        tuple(reason.code for reason in result.reasons),
                    )
                )
        return tuple(
            sorted(
                candidates,
                key=lambda candidate: (
                    -candidate.confidence_bps,
                    candidate.adapter_id,
                    candidate.profile_versioned_id,
                ),
            )
        )

    def _adapter(self, adapter_id: str) -> TabularSourceAdapter:
        try:
            return next(adapter for adapter in self._adapters if adapter.adapter_id == adapter_id)
        except StopIteration as error:
            raise KeyError(adapter_id) from error
