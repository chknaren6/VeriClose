"""Rule proposals and risk-gate-owned reconciliation decisions."""

from __future__ import annotations

from dataclasses import dataclass

from core.vericlose.domain.enums import DecisionState, ProofLevel
from core.vericlose.domain.events import _require_text
from core.vericlose.domain.evidence import EvidenceLink, MatchGroup, ProofCheck


@dataclass(frozen=True, slots=True)
class MatchProposal:
    """Side-effect-free output from one rule; never an authoritative clear."""

    proposal_id: str
    rule_id: str
    rule_version: str
    match_group: MatchGroup
    proposed_proof_level: ProofLevel
    support_score_bps: int
    proof_checks: tuple[ProofCheck, ...]
    evidence_links: tuple[EvidenceLink, ...]
    reason_codes: tuple[str, ...] = ()
    notes: str | None = None

    def __post_init__(self) -> None:
        for value, field_name in (
            (self.proposal_id, "proposal_id"),
            (self.rule_id, "rule_id"),
            (self.rule_version, "rule_version"),
        ):
            _require_text(value, field_name)
        if not isinstance(self.proposed_proof_level, ProofLevel):
            raise TypeError("proposed_proof_level must be a ProofLevel")
        if isinstance(self.support_score_bps, bool) or not isinstance(self.support_score_bps, int):
            raise TypeError("support_score_bps must be an integer")
        if not 0 <= self.support_score_bps <= 10_000:
            raise ValueError("support_score_bps must be between 0 and 10_000")
        if not isinstance(self.proof_checks, tuple):
            raise TypeError("proof_checks must be a tuple")
        if not isinstance(self.evidence_links, tuple):
            raise TypeError("evidence_links must be a tuple")
        if not isinstance(self.reason_codes, tuple):
            raise TypeError("reason_codes must be a tuple")
        if any(not isinstance(code, str) or not code.strip() for code in self.reason_codes):
            raise ValueError("reason_codes cannot contain blank values")


@dataclass(frozen=True, slots=True)
class ReconciliationDecision:
    """Final proof disposition emitted only by the future deterministic risk gate."""

    decision_id: str
    state: DecisionState
    event_ids: tuple[str, ...]
    proof_level: ProofLevel
    proof_checks: tuple[ProofCheck, ...]
    evidence_links: tuple[EvidenceLink, ...]
    uniqueness_passed: bool
    contradiction_reason: str | None = None
    policy_allows_auto_clear: bool = False
    related_proposal_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.decision_id, "decision_id")
        if not isinstance(self.state, DecisionState):
            raise TypeError("state must be a DecisionState")
        if not isinstance(self.proof_level, ProofLevel):
            raise TypeError("proof_level must be a ProofLevel")
        if not self.event_ids:
            raise ValueError("event_ids cannot be empty")
        if len(set(self.event_ids)) != len(self.event_ids):
            raise ValueError("event_ids must be unique")
        if not isinstance(self.uniqueness_passed, bool):
            raise TypeError("uniqueness_passed must be a boolean")
        if not isinstance(self.proof_checks, tuple):
            raise TypeError("proof_checks must be a tuple")
        if not isinstance(self.evidence_links, tuple):
            raise TypeError("evidence_links must be a tuple")
        if not isinstance(self.related_proposal_ids, tuple):
            raise TypeError("related_proposal_ids must be a tuple")

        required_checks = tuple(check for check in self.proof_checks if check.required)
        if self.proof_level is ProofLevel.PROVED:
            if not required_checks:
                raise ValueError("PROVED decision requires at least one required proof check")
            if not all(check.passed for check in required_checks):
                raise ValueError("PROVED decision requires every required proof check to pass")
            if not self.uniqueness_passed:
                raise ValueError("PROVED decision requires uniqueness_passed=True")
            if not self.evidence_links:
                raise ValueError("PROVED decision requires non-empty evidence")
            if self.contradiction_reason:
                raise ValueError("PROVED decision cannot have a contradiction_reason")
        if self.proof_level is ProofLevel.CONTRADICTED and not self.contradiction_reason:
            raise ValueError("CONTRADICTED decision requires a contradiction_reason")
        if self.policy_allows_auto_clear and self.proof_level is not ProofLevel.PROVED:
            raise ValueError("only a PROVED decision may allow auto-clear")
        if self.state is DecisionState.AUTO_CLEARED and (
            self.proof_level is not ProofLevel.PROVED or not self.policy_allows_auto_clear
        ):
            raise ValueError("AUTO_CLEARED requires a policy-permitted PROVED decision")
