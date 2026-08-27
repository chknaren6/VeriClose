import pytest

from core.vericlose.domain.evidence import EvidenceLink, MatchGroup, ProofCheck


def _link(event_id: str | None = "evt-1") -> EvidenceLink:
    return EvidenceLink(event_id, "file-1", "payments", 2, "a" * 64, "amount")


def test_evidence_can_point_to_invalid_raw_row_without_event() -> None:
    assert _link(event_id=None).event_id is None


def test_required_check_needs_evidence() -> None:
    with pytest.raises(ValueError, match="must cite evidence"):
        ProofCheck("AMOUNT_EQUAL", 100, 100, 0, True, True, ())


def test_optional_check_may_have_no_evidence() -> None:
    check = ProofCheck("NARRATION_HINT", None, None, None, False, False, ())
    assert not check.required


def test_match_group_rejects_duplicate_or_blank_ids() -> None:
    with pytest.raises(ValueError, match="unique"):
        MatchGroup("group-1", ("evt-1", "evt-1"))
    with pytest.raises(ValueError, match="blank"):
        MatchGroup("group-1", ("",))
