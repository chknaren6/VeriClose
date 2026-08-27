import pytest

from core.vericlose.domain.enums import (
    ActionType,
    Direction,
    EventType,
    ExceptionCategory,
    ProofLevel,
    SourceType,
)


@pytest.mark.parametrize(
    ("enum_class", "expected_values"),
    [
        (SourceType, {"GATEWAY", "BANK", "ERP"}),
        (Direction, {"DEBIT", "CREDIT"}),
        (
            ProofLevel,
            {"PROVED", "SUPPORTED", "AMBIGUOUS", "CONTRADICTED", "INVALID_INPUT"},
        ),
        (
            ExceptionCategory,
            {
                "DATA_QUALITY",
                "REFERENCE",
                "TIMING",
                "AMOUNT",
                "DUPLICATE",
                "MISSING_SOURCE",
                "ACCOUNTING",
                "POLICY",
                "AMBIGUOUS",
                "UNKNOWN",
            },
        ),
    ],
)
def test_enum_wire_values_are_stable(enum_class: type, expected_values: set[str]) -> None:
    assert {member.value for member in enum_class} == expected_values
    assert all(isinstance(member, str) for member in enum_class)


def test_event_types_cover_all_mvp_components() -> None:
    assert {event.value for event in EventType} >= {
        "PAYMENT",
        "REFUND",
        "FEE",
        "TAX",
        "ADJUSTMENT",
        "SETTLEMENT",
        "BANK_CREDIT",
        "ERP_JOURNAL_LINE",
    }


def test_action_types_are_finance_workflow_actions() -> None:
    assert ActionType.JOURNAL_EXPORT.value == "JOURNAL_EXPORT"
    assert ActionType.CLARIFICATION_REQUEST.value == "CLARIFICATION_REQUEST"


def test_invalid_wire_value_is_rejected() -> None:
    with pytest.raises(ValueError):
        ProofLevel("CONTRADICATED")
