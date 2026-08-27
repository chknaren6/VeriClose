"""Human-reviewed finance actions; this module validates but never executes them."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

from core.vericlose.domain.enums import (
    ActionState,
    ActionType,
    Direction,
    ReviewState,
)
from core.vericlose.domain.events import _require_text
from core.vericlose.domain.evidence import EvidenceLink
from core.vericlose.domain.money import Money

StringPairs = tuple[tuple[str, str], ...]

ACTION_TRANSITIONS: dict[ActionState, frozenset[ActionState]] = {
    ActionState.PROPOSED: frozenset(
        {ActionState.APPROVED, ActionState.REJECTED, ActionState.CANCELLED}
    ),
    ActionState.APPROVED: frozenset(
        {ActionState.EXPORTED, ActionState.FAILED, ActionState.CANCELLED}
    ),
    ActionState.FAILED: frozenset({ActionState.APPROVED, ActionState.CANCELLED}),
    ActionState.REJECTED: frozenset(),
    ActionState.EXPORTED: frozenset(),
    ActionState.CANCELLED: frozenset(),
}


def _require_string_pairs(value: StringPairs, field_name: str) -> None:
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be an immutable tuple of string pairs")
    if any(
        not isinstance(pair, tuple)
        or len(pair) != 2
        or not all(isinstance(item, str) for item in pair)
        for pair in value
    ):
        raise TypeError(f"{field_name} must contain only (str, str) pairs")


@dataclass(frozen=True, slots=True)
class JournalLine:
    account_code: str
    money: Money
    direction: Direction
    narration: str
    evidence_links: tuple[EvidenceLink, ...]

    def __post_init__(self) -> None:
        _require_text(self.account_code, "account_code")
        _require_text(self.narration, "narration")
        if not isinstance(self.money, Money):
            raise TypeError("money must be Money")
        if not isinstance(self.direction, Direction):
            raise TypeError("direction must be a Direction")
        if self.money.amount_minor == 0:
            raise ValueError("journal lines cannot have a zero amount")
        if not isinstance(self.evidence_links, tuple) or not self.evidence_links:
            raise ValueError("journal lines must cite source evidence")


@dataclass(frozen=True, slots=True)
class JournalProposal:
    """A structurally balanced journal suggestion; never a posting instruction."""

    lines: tuple[JournalLine, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.lines, tuple):
            raise TypeError("lines must be an immutable tuple")
        if len(self.lines) < 2:
            raise ValueError("JournalProposal must contain at least two lines")
        currencies = {line.money.currency for line in self.lines}
        if len(currencies) != 1:
            raise ValueError("all journal lines must use the same currency")
        debit_total = sum(
            line.money.amount_minor
            for line in self.lines
            if line.direction is Direction.DEBIT
        )
        credit_total = sum(
            line.money.amount_minor
            for line in self.lines
            if line.direction is Direction.CREDIT
        )
        if debit_total != credit_total:
            raise ValueError(f"Journal is unbalanced: debits={debit_total} credits={credit_total}")


@dataclass(frozen=True, slots=True)
class ProposedAction:
    action_id: str
    action_type: ActionType
    case_id: str
    state: ActionState
    journal: JournalProposal | None
    payload: StringPairs
    evidence_links: tuple[EvidenceLink, ...]
    created_at: datetime

    def __post_init__(self) -> None:
        _require_text(self.action_id, "action_id")
        _require_text(self.case_id, "case_id")
        if not isinstance(self.action_type, ActionType):
            raise TypeError("action_type must be an ActionType")
        if not isinstance(self.state, ActionState):
            raise TypeError("state must be an ActionState")
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        if not self.evidence_links:
            raise ValueError("a proposed action must cite evidence")
        _require_string_pairs(self.payload, "payload")
        if self.action_type is ActionType.JOURNAL_EXPORT and self.journal is None:
            raise ValueError("JOURNAL_EXPORT requires a balanced journal proposal")
        if self.action_type is not ActionType.JOURNAL_EXPORT and self.journal is not None:
            raise ValueError("only JOURNAL_EXPORT can carry a journal proposal")

    def transition(self, next_state: ActionState) -> ProposedAction:
        """Return a new lifecycle snapshot; application code persists it append-only."""

        allowed = ACTION_TRANSITIONS[self.state]
        if next_state not in allowed:
            raise ValueError(
                f"invalid action transition: {self.state.value} -> {next_state.value}"
            )
        return replace(self, state=next_state)


@dataclass(frozen=True, slots=True)
class ReviewDecision:
    review_id: str
    action_id: str
    state: ReviewState
    reviewer_id: str
    reviewed_at: datetime
    comment: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.review_id, "review_id")
        _require_text(self.action_id, "action_id")
        _require_text(self.reviewer_id, "reviewer_id")
        if not isinstance(self.state, ReviewState):
            raise TypeError("state must be a ReviewState")
        if self.reviewed_at.tzinfo is None or self.reviewed_at.utcoffset() is None:
            raise ValueError("reviewed_at must be timezone-aware")


@dataclass(frozen=True, slots=True)
class ActionReceipt:
    """Append-only receipt for an exported/executed action and its idempotency key."""

    receipt_id: str
    action_id: str
    idempotency_key: str
    executed_at: datetime
    result_payload: StringPairs

    def __post_init__(self) -> None:
        _require_text(self.receipt_id, "receipt_id")
        _require_text(self.action_id, "action_id")
        _require_text(self.idempotency_key, "idempotency_key")
        if self.executed_at.tzinfo is None or self.executed_at.utcoffset() is None:
            raise ValueError("executed_at must be timezone-aware")
        _require_string_pairs(self.result_payload, "result_payload")
