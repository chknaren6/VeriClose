"""Internal rule proposal with complete evidence and interpretable support features."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from core.vericlose.domain.events import CanonicalEvent
from core.vericlose.domain.evidence import EvidenceLink, ProofCheck


@dataclass(frozen=True, slots=True)
class SupportFeature:
    name: str
    score_bps: int
    observed: str


@dataclass(frozen=True, slots=True)
class CaseProposal:
    proposal_id: str
    case_key: str
    event_ids: tuple[str, ...]
    proof_checks: tuple[ProofCheck, ...]
    evidence_links: tuple[EvidenceLink, ...]
    reason_codes: tuple[str, ...]
    rules_attempted: tuple[str, ...]
    support_features: tuple[SupportFeature, ...]
    support_score_bps: int
    amount_at_risk_minor: int
    uniqueness_passed: bool
    ambiguous: bool = False
    invalid_input: bool = False


def stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:20]
    return f"{prefix}_{digest}"


def evidence(event: CanonicalEvent, purpose: str) -> EvidenceLink:
    return EvidenceLink(
        event.event_id,
        event.lineage.source_file_id,
        event.lineage.table_name,
        event.lineage.row_number,
        event.lineage.raw_row_hash,
        purpose,
    )


def unique_evidence(links: tuple[EvidenceLink, ...]) -> tuple[EvidenceLink, ...]:
    seen: set[tuple[str | None, str]] = set()
    result: list[EvidenceLink] = []
    for link in links:
        key = (link.event_id, link.purpose)
        if key not in seen:
            result.append(link)
            seen.add(key)
    return tuple(result)
