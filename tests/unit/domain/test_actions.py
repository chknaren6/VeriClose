from datetime import UTC, datetime

import pytest

from core.vericlose.domain.actions import (
    ActionReceipt,
    JournalLine,
    JournalProposal,
    ProposedAction,
    ReviewDecision,
)
from core.vericlose.domain.enums import (
    ActionState,
    ActionType,
    Direction,
    ReviewState,
)
from core.vericlose.domain.evidence import EvidenceLink
from core.vericlose.domain.money import Money


def _link() -> EvidenceLink:
    return EvidenceLink("evt-1", "file-1", "erp", 2, "a" * 64, "journal source")


def _line(direction: Direction, amount: int, currency: str = "INR") -> JournalLine:
    return JournalLine("1000", Money(amount, currency), direction, "Synthetic", (_link(),))


def test_journal_must_balance_in_one_currency() -> None:
    JournalProposal((_line(Direction.DEBIT, 100), _line(Direction.CREDIT, 100)))
    with pytest.raises(ValueError, match="unbalanced"):
        JournalProposal((_line(Direction.DEBIT, 100), _line(Direction.CREDIT, 99)))
    with pytest.raises(ValueError, match="same currency"):
        JournalProposal(
            (_line(Direction.DEBIT, 100, "INR"), _line(Direction.CREDIT, 100, "USD"))
        )


def test_journal_export_requires_balanced_proposal_and_evidence() -> None:
    with pytest.raises(ValueError, match="requires a balanced journal"):
        ProposedAction(
            "action-1",
            ActionType.JOURNAL_EXPORT,
            "case-1",
            ActionState.PROPOSED,
            None,
            (),
            (_link(),),
            datetime(2026, 4, 1, tzinfo=UTC),
        )


def test_review_and_receipt_require_identity_and_idempotency() -> None:
    review = ReviewDecision(
        "review-1",
        "action-1",
        ReviewState.APPROVED,
        "reviewer-1",
        datetime(2026, 4, 1, tzinfo=UTC),
    )
    assert review.reviewer_id == "reviewer-1"
    with pytest.raises(ValueError, match="idempotency_key"):
        ActionReceipt(
            "receipt-1",
            "action-1",
            " ",
            datetime(2026, 4, 1, tzinfo=UTC),
            (),
        )


def test_action_state_transition_is_immutable_and_bounded() -> None:
    action = ProposedAction(
        "action-1",
        ActionType.MANUAL_REVIEW,
        "case-1",
        ActionState.PROPOSED,
        None,
        (),
        (_link(),),
        datetime(2026, 4, 1, tzinfo=UTC),
    )
    approved = action.transition(ActionState.APPROVED)
    assert action.state is ActionState.PROPOSED
    assert approved.state is ActionState.APPROVED
    with pytest.raises(ValueError, match="invalid action transition"):
        action.transition(ActionState.EXPORTED)
