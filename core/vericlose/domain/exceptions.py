"""Honest unresolved cases produced when proof is unavailable or contradicted."""

from __future__ import annotations

from dataclasses import dataclass

from core.vericlose.domain.enums import ActionType, ExceptionCategory, ProofLevel, Severity
from core.vericlose.domain.events import _require_text
from core.vericlose.domain.evidence import EvidenceLink
from core.vericlose.domain.money import Money


@dataclass(frozen=True, slots=True)
class ExceptionCase:
    case_id: str
    reason_code: str
    category: ExceptionCategory
    severity: Severity
    amount_at_risk: Money
    proof_level: ProofLevel
    evidence_links: tuple[EvidenceLink, ...]
    rules_attempted: tuple[str, ...]
    requires_company_input: bool
    recommended_action: ActionType
    owner: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.case_id, "case_id")
        _require_text(self.reason_code, "reason_code")
        if not isinstance(self.category, ExceptionCategory):
            raise TypeError("category must be an ExceptionCategory")
        if not isinstance(self.severity, Severity):
            raise TypeError("severity must be a Severity")
        if not isinstance(self.amount_at_risk, Money):
            raise TypeError("amount_at_risk must be Money")
        if not isinstance(self.proof_level, ProofLevel):
            raise TypeError("proof_level must be a ProofLevel")
        if not isinstance(self.recommended_action, ActionType):
            raise TypeError("recommended_action must be an ActionType")
        if self.proof_level is ProofLevel.PROVED:
            raise ValueError("a PROVED decision is not an exception")
        if not isinstance(self.evidence_links, tuple) or not self.evidence_links:
            raise ValueError("an exception must cite at least one evidence row")
        if not isinstance(self.rules_attempted, tuple) or not self.rules_attempted:
            raise ValueError("rules_attempted must be an immutable non-empty tuple")
        if any(not isinstance(rule, str) or not rule.strip() for rule in self.rules_attempted):
            raise ValueError("rules_attempted must contain at least one non-blank rule ID")
        if not isinstance(self.requires_company_input, bool):
            raise TypeError("requires_company_input must be a boolean")
