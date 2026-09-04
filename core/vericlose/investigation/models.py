"""Validated advisory records; none of these types can alter accounting truth."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from core.vericlose.domain.enums import ActionType, Direction
from core.vericlose.domain.events import _require_text


class InvestigationStatus(StrEnum):
    MODEL_VALIDATED = "MODEL_VALIDATED"
    DETERMINISTIC_FALLBACK = "DETERMINISTIC_FALLBACK"


@dataclass(frozen=True, slots=True)
class AdvisoryJournalLine:
    account_code: str
    direction: Direction
    amount_minor: int
    evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.account_code, "account_code")
        if not isinstance(self.direction, Direction):
            raise TypeError("direction must be a Direction")
        if isinstance(self.amount_minor, bool) or not isinstance(self.amount_minor, int):
            raise TypeError("amount_minor must be an integer")
        if self.amount_minor <= 0:
            raise ValueError("amount_minor must be positive")
        if not self.evidence_ids or len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("journal line evidence IDs must be non-empty and unique")


@dataclass(frozen=True, slots=True)
class AdvisoryJournal:
    lines: tuple[AdvisoryJournalLine, ...]

    def __post_init__(self) -> None:
        if len(self.lines) < 2:
            raise ValueError("advisory journal requires at least two lines")
        debits = sum(line.amount_minor for line in self.lines if line.direction is Direction.DEBIT)
        credits = sum(
            line.amount_minor for line in self.lines if line.direction is Direction.CREDIT
        )
        if debits != credits:
            raise ValueError(f"advisory journal is unbalanced: debits={debits} credits={credits}")


@dataclass(frozen=True, slots=True)
class InvestigationResult:
    investigation_id: str
    run_id: str
    case_id: str
    status: InvestigationStatus
    hypothesis: str
    explanation: str
    evidence_ids: tuple[str, ...]
    confidence_bps: int
    recommended_action: ActionType
    requires_human_approval: bool
    advisory_journal: AdvisoryJournal | None
    prompt_version: str
    model_version: str | None
    latency_ms: int
    failure_code: str | None
    created_at: datetime

    def __post_init__(self) -> None:
        for value, name in (
            (self.investigation_id, "investigation_id"),
            (self.run_id, "run_id"),
            (self.case_id, "case_id"),
            (self.hypothesis, "hypothesis"),
            (self.explanation, "explanation"),
            (self.prompt_version, "prompt_version"),
        ):
            _require_text(value, name)
        if not isinstance(self.status, InvestigationStatus):
            raise TypeError("status must be an InvestigationStatus")
        if not isinstance(self.recommended_action, ActionType):
            raise TypeError("recommended_action must be an ActionType")
        if not isinstance(self.requires_human_approval, bool):
            raise TypeError("requires_human_approval must be a boolean")
        if not self.requires_human_approval:
            raise ValueError("investigator advice always requires human approval")
        if not 0 <= self.confidence_bps <= 10_000:
            raise ValueError("confidence_bps must be between 0 and 10000")
        if self.latency_ms < 0:
            raise ValueError("latency_ms cannot be negative")
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        if len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("evidence_ids must be unique")
        if self.status is InvestigationStatus.MODEL_VALIDATED:
            if not self.model_version:
                raise ValueError("validated model output requires model_version")
            if self.failure_code is not None:
                raise ValueError("validated model output cannot have a failure code")
        else:
            if self.model_version is not None:
                raise ValueError("fallback output cannot claim a model version")
            if not self.failure_code:
                raise ValueError("fallback output requires a failure code")
