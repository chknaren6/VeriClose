import pytest

from core.vericlose.domain.enums import (
    ActionType,
    ExceptionCategory,
    ProofLevel,
    Severity,
)
from core.vericlose.domain.evidence import EvidenceLink
from core.vericlose.domain.exceptions import ExceptionCase
from core.vericlose.domain.money import Money


def _link() -> EvidenceLink:
    return EvidenceLink("evt-1", "file-1", "bank", 2, "a" * 64, "missing receipt")


def test_exception_requires_evidence_rules_and_non_proved_disposition() -> None:
    case = ExceptionCase(
        case_id="case-1",
        reason_code="BANK_RECEIPT_MISSING",
        category=ExceptionCategory.MISSING_SOURCE,
        severity=Severity.HIGH,
        amount_at_risk=Money(10_000),
        proof_level=ProofLevel.SUPPORTED,
        evidence_links=(_link(),),
        rules_attempted=("bank-receipt-v1",),
        requires_company_input=True,
        recommended_action=ActionType.CLARIFICATION_REQUEST,
    )
    assert case.recommended_action is ActionType.CLARIFICATION_REQUEST

    with pytest.raises(ValueError, match="not an exception"):
        ExceptionCase(
            case_id="case-2",
            reason_code="NONE",
            category=ExceptionCategory.UNKNOWN,
            severity=Severity.LOW,
            amount_at_risk=Money(0),
            proof_level=ProofLevel.PROVED,
            evidence_links=(_link(),),
            rules_attempted=("exact-v1",),
            requires_company_input=False,
            recommended_action=ActionType.NO_ACTION,
        )
