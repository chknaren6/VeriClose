"""Proof objects that make every reconciliation decision auditable."""

from __future__ import annotations

from dataclasses import dataclass

from core.vericlose.domain.events import _require_sha256, _require_text

ProofScalar = str | int | bool | None


@dataclass(frozen=True, slots=True)
class EvidenceLink:
    """Precise pointer to a raw row, optionally through a canonical event."""

    event_id: str | None
    source_file_id: str
    table_name: str
    row_number: int
    raw_row_hash: str
    purpose: str

    def __post_init__(self) -> None:
        if self.event_id is not None:
            _require_text(self.event_id, "event_id")
        _require_text(self.source_file_id, "source_file_id")
        _require_text(self.table_name, "table_name")
        _require_text(self.purpose, "purpose")
        if isinstance(self.row_number, bool) or not isinstance(self.row_number, int):
            raise TypeError("row_number must be an integer")
        if self.row_number < 1:
            raise ValueError("row_number must be >= 1")
        _require_sha256(self.raw_row_hash, "raw_row_hash")


@dataclass(frozen=True, slots=True)
class ProofCheck:
    """One deterministic assertion and the evidence used to calculate it."""

    check_code: str
    expected: ProofScalar
    observed: ProofScalar
    tolerance_minor: int | None
    passed: bool
    required: bool
    evidence_links: tuple[EvidenceLink, ...]

    def __post_init__(self) -> None:
        _require_text(self.check_code, "check_code")
        if not isinstance(self.passed, bool) or not isinstance(self.required, bool):
            raise TypeError("passed and required must be booleans")
        if self.tolerance_minor is not None:
            if isinstance(self.tolerance_minor, bool) or not isinstance(
                self.tolerance_minor, int
            ):
                raise TypeError("tolerance_minor must be an integer or None")
            if self.tolerance_minor < 0:
                raise ValueError("tolerance_minor cannot be negative")
        if not isinstance(self.evidence_links, tuple):
            raise TypeError("evidence_links must be a tuple")
        if any(not isinstance(link, EvidenceLink) for link in self.evidence_links):
            raise TypeError("evidence_links can contain only EvidenceLink values")
        if self.required and not self.evidence_links:
            raise ValueError("a required proof check must cite evidence")


@dataclass(frozen=True, slots=True)
class MatchGroup:
    """Canonical events a rule proposes as one economic movement."""

    group_id: str
    event_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.group_id, "group_id")
        if not self.event_ids:
            raise ValueError("event_ids cannot be empty")
        if any(
            not isinstance(event_id, str) or not event_id.strip()
            for event_id in self.event_ids
        ):
            raise ValueError("event_ids cannot contain blank values")
        if len(set(self.event_ids)) != len(self.event_ids):
            raise ValueError("event_ids must be unique")
