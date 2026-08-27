"""The only component allowed to turn rule proposals into final dispositions."""

from __future__ import annotations

from core.vericlose.domain.decisions import ReconciliationDecision
from core.vericlose.domain.enums import DecisionState, ProofLevel
from core.vericlose.reconciliation.policy import ReconciliationPolicy
from core.vericlose.reconciliation.proposals import CaseProposal, stable_id

_HARD_CONTRADICTIONS = frozenset(
    {
        "DUPLICATE_IDENTIFIER",
        "DUPLICATE_ERP_POSTING",
        "SETTLEMENT_COMPONENT_MISMATCH",
        "BANK_AMOUNT_MISMATCH",
        "ERP_POSTING_MISMATCH",
    }
)


def decide(
    run_id: str,
    proposal: CaseProposal,
    policy: ReconciliationPolicy,
) -> ReconciliationDecision:
    checks = {check.check_code: check for check in proposal.proof_checks}
    required_present = policy.auto_clear_required_checks <= checks.keys()
    required_passed = required_present and all(
        checks[code].passed for code in policy.auto_clear_required_checks
    )
    contradiction = next(
        (code for code in proposal.reason_codes if code in _HARD_CONTRADICTIONS), None
    )
    if proposal.invalid_input:
        proof_level = ProofLevel.INVALID_INPUT
        state = DecisionState.EXCEPTION
        contradiction_reason = None
    elif proposal.ambiguous:
        proof_level = ProofLevel.AMBIGUOUS
        state = DecisionState.REVIEW_REQUIRED
        contradiction_reason = None
    elif contradiction:
        proof_level = ProofLevel.CONTRADICTED
        state = DecisionState.EXCEPTION
        contradiction_reason = contradiction
    elif required_passed and proposal.uniqueness_passed:
        proof_level = ProofLevel.PROVED
        state = DecisionState.AUTO_CLEARED if policy.auto_clear_enabled else DecisionState.PROPOSED
        contradiction_reason = None
    else:
        proof_level = ProofLevel.SUPPORTED
        state = DecisionState.REVIEW_REQUIRED
        contradiction_reason = None
    policy_allows = (
        proof_level is ProofLevel.PROVED
        and policy.auto_clear_enabled
        and required_passed
        and proposal.uniqueness_passed
    )
    return ReconciliationDecision(
        decision_id=stable_id("decision", run_id, proposal.case_key, policy.versioned_id),
        state=state,
        event_ids=proposal.event_ids,
        proof_level=proof_level,
        proof_checks=proposal.proof_checks,
        evidence_links=proposal.evidence_links,
        uniqueness_passed=proposal.uniqueness_passed,
        contradiction_reason=contradiction_reason,
        policy_allows_auto_clear=policy_allows,
        related_proposal_ids=(proposal.proposal_id,),
    )
