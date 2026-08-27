from __future__ import annotations

from pathlib import Path

import pytest

from core.vericlose.domain.decisions import ReconciliationDecision
from core.vericlose.domain.enums import DecisionState, ProofLevel
from core.vericlose.domain.evidence import EvidenceLink, ProofCheck
from core.vericlose.reconciliation.policy import load_policy
from core.vericlose.reconciliation.proposals import CaseProposal
from core.vericlose.reconciliation.risk_gate import decide


def _link() -> EvidenceLink:
    return EvidenceLink("event-1", "file-1", "rows", 2, "a" * 64, "test evidence")


def _proposal(
    *,
    failed_code: str | None = None,
    reason: str | None = None,
    ambiguous: bool = False,
    invalid: bool = False,
) -> CaseProposal:
    policy = load_policy(Path("config/policies/razorpay_inr_v1.yaml"))
    checks = tuple(
        ProofCheck(code, True, code != failed_code, None, code != failed_code, True, (_link(),))
        for code in sorted(policy.auto_clear_required_checks)
    )
    return CaseProposal(
        "proposal-1",
        "case-1",
        ("event-1",),
        checks,
        (_link(),),
        (reason,) if reason else (),
        ("rule-1",),
        (),
        0,
        100,
        not ambiguous,
        ambiguous,
        invalid,
    )


@pytest.mark.parametrize(
    ("proposal", "level", "state"),
    [
        (_proposal(), ProofLevel.PROVED, DecisionState.AUTO_CLEARED),
        (
            _proposal(failed_code="BANK_RECEIPT_REFERENCE", reason="REFERENCE_MISMATCH"),
            ProofLevel.SUPPORTED,
            DecisionState.REVIEW_REQUIRED,
        ),
        (
            _proposal(ambiguous=True, reason="BANK_RECEIPT_AMBIGUOUS"),
            ProofLevel.AMBIGUOUS,
            DecisionState.REVIEW_REQUIRED,
        ),
        (
            _proposal(
                failed_code="BANK_RECEIPT_AMOUNT", reason="BANK_AMOUNT_MISMATCH"
            ),
            ProofLevel.CONTRADICTED,
            DecisionState.EXCEPTION,
        ),
        (
            _proposal(invalid=True, reason="ERP_JOURNAL_UNBALANCED"),
            ProofLevel.INVALID_INPUT,
            DecisionState.EXCEPTION,
        ),
    ],
)
def test_risk_gate_covers_every_proof_transition(
    proposal: CaseProposal,
    level: ProofLevel,
    state: DecisionState,
) -> None:
    policy = load_policy(Path("config/policies/razorpay_inr_v1.yaml"))
    decision: ReconciliationDecision = decide("run-1", proposal, policy)
    assert decision.proof_level is level
    assert decision.state is state
    assert decision.policy_allows_auto_clear is (level is ProofLevel.PROVED)
