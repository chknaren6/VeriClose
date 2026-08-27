"""Stable, policy-driven exception classification for every non-proved decision."""

from __future__ import annotations

from core.vericlose.domain.decisions import ReconciliationDecision
from core.vericlose.domain.enums import ProofLevel
from core.vericlose.domain.exceptions import ExceptionCase
from core.vericlose.domain.money import Money
from core.vericlose.reconciliation.policy import ReconciliationPolicy
from core.vericlose.reconciliation.proposals import CaseProposal, stable_id

_PRIORITY = (
    "ERP_JOURNAL_UNBALANCED",
    "DUPLICATE_ERP_POSTING",
    "DUPLICATE_IDENTIFIER",
    "BANK_RECEIPT_AMBIGUOUS",
    "SETTLEMENT_COMPONENT_MISMATCH",
    "BANK_AMOUNT_MISMATCH",
    "ERP_POSTING_MISMATCH",
    "REFERENCE_MISMATCH",
    "MISSING_BANK_RECEIPT",
    "MISSING_ERP_POSTING",
    "BANK_DATE_OUT_OF_RANGE",
    "ORPHAN_BANK_CREDIT",
    "ORPHAN_ERP_POSTING",
    "UNKNOWN_UNRESOLVED",
)


def create_exception(
    run_id: str,
    proposal: CaseProposal,
    decision: ReconciliationDecision,
    policy: ReconciliationPolicy,
) -> ExceptionCase | None:
    if decision.proof_level is ProofLevel.PROVED:
        return None
    reason = next(
        (code for code in _PRIORITY if code in proposal.reason_codes),
        "UNKNOWN_UNRESOLVED",
    )
    classification = policy.exception(reason)
    return ExceptionCase(
        case_id=stable_id("case", run_id, proposal.case_key, policy.versioned_id),
        reason_code=reason,
        category=classification.category,
        severity=classification.severity,
        amount_at_risk=Money(proposal.amount_at_risk_minor, policy.currency),
        proof_level=decision.proof_level,
        evidence_links=decision.evidence_links,
        rules_attempted=proposal.rules_attempted,
        requires_company_input=classification.requires_company_input,
        recommended_action=classification.action,
    )
