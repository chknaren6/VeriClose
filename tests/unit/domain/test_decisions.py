import pytest

from core.vericlose.domain.decisions import MatchProposal, ReconciliationDecision
from core.vericlose.domain.enums import DecisionState, ProofLevel
from core.vericlose.domain.evidence import EvidenceLink, MatchGroup, ProofCheck


def _link() -> EvidenceLink:
    return EvidenceLink("evt-1", "file-1", "rows", 1, "a" * 64, "amount")


def _check(*, passed: bool = True, required: bool = True) -> ProofCheck:
    return ProofCheck("AMOUNT_EQUAL", 100, 100, 0, passed, required, (_link(),))


def test_match_proposal_is_advisory_and_score_is_bounded() -> None:
    proposal = MatchProposal(
        proposal_id="proposal-1",
        rule_id="exact-reference",
        rule_version="v1",
        match_group=MatchGroup("group-1", ("evt-1",)),
        proposed_proof_level=ProofLevel.SUPPORTED,
        support_score_bps=8_500,
        proof_checks=(_check(),),
        evidence_links=(_link(),),
    )
    assert proposal.proposed_proof_level is ProofLevel.SUPPORTED
    with pytest.raises(ValueError, match="10_000"):
        MatchProposal(
            proposal_id="proposal-2",
            rule_id="candidate",
            rule_version="v1",
            match_group=MatchGroup("group-2", ("evt-2",)),
            proposed_proof_level=ProofLevel.AMBIGUOUS,
            support_score_bps=10_001,
            proof_checks=(),
            evidence_links=(),
        )


def test_proved_requires_required_checks_uniqueness_and_evidence() -> None:
    decision = ReconciliationDecision(
        decision_id="decision-1",
        state=DecisionState.AUTO_CLEARED,
        event_ids=("evt-1",),
        proof_level=ProofLevel.PROVED,
        proof_checks=(_check(),),
        evidence_links=(_link(),),
        uniqueness_passed=True,
        policy_allows_auto_clear=True,
    )
    assert decision.proof_level is ProofLevel.PROVED

    with pytest.raises(ValueError, match="required proof check"):
        ReconciliationDecision(
            decision_id="decision-2",
            state=DecisionState.REVIEW_REQUIRED,
            event_ids=("evt-1",),
            proof_level=ProofLevel.PROVED,
            proof_checks=(_check(required=False),),
            evidence_links=(_link(),),
            uniqueness_passed=True,
        )


def test_non_proved_decision_cannot_auto_clear() -> None:
    with pytest.raises(ValueError, match="only a PROVED"):
        ReconciliationDecision(
            decision_id="decision-1",
            state=DecisionState.REVIEW_REQUIRED,
            event_ids=("evt-1",),
            proof_level=ProofLevel.SUPPORTED,
            proof_checks=(),
            evidence_links=(),
            uniqueness_passed=False,
            policy_allows_auto_clear=True,
        )


def test_contradicted_decision_requires_reason() -> None:
    with pytest.raises(ValueError, match="contradiction_reason"):
        ReconciliationDecision(
            decision_id="decision-1",
            state=DecisionState.EXCEPTION,
            event_ids=("evt-1",),
            proof_level=ProofLevel.CONTRADICTED,
            proof_checks=(),
            evidence_links=(_link(),),
            uniqueness_passed=True,
        )
