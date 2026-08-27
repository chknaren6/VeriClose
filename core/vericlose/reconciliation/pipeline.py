"""Deterministic whole-batch reconciliation pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter_ns

from core.vericlose.domain.decisions import ReconciliationDecision
from core.vericlose.domain.enums import SourceType
from core.vericlose.domain.events import CanonicalEvent
from core.vericlose.domain.evidence import ProofCheck
from core.vericlose.domain.exceptions import ExceptionCase
from core.vericlose.reconciliation.context import ReconciliationContext
from core.vericlose.reconciliation.exception_factory import create_exception
from core.vericlose.reconciliation.policy import ReconciliationPolicy
from core.vericlose.reconciliation.proposals import CaseProposal, evidence, stable_id
from core.vericlose.reconciliation.risk_gate import decide
from core.vericlose.reconciliation.rules.settlement import RULES, analyze_settlement


@dataclass(frozen=True, slots=True)
class StageTiming:
    stage: str
    duration_ms: int
    input_count: int
    output_count: int


@dataclass(frozen=True, slots=True)
class KernelResult:
    proposals: tuple[CaseProposal, ...]
    decisions: tuple[ReconciliationDecision, ...]
    exceptions: tuple[ExceptionCase, ...]
    timings: tuple[StageTiming, ...]

    @property
    def auto_cleared_count(self) -> int:
        return sum(decision.policy_allows_auto_clear for decision in self.decisions)


def reconcile(
    events: tuple[CanonicalEvent, ...], policy: ReconciliationPolicy
) -> KernelResult:
    started = perf_counter_ns()
    context = ReconciliationContext.build(events, policy)
    event_by_id = {event.event_id: event for event in context.events}
    context_timing = _timing("context_and_indexes", started, len(events), len(context.events))

    matching_started = perf_counter_ns()
    proposals: list[CaseProposal] = []
    consumed_bank: set[str] = set()
    consumed_erp: set[str] = set()
    for reference in context.settlement_references:
        proposal = analyze_settlement(context, reference, frozenset(consumed_bank))
        proposals.append(proposal)
        for event_id in proposal.event_ids:
            event = event_by_id[event_id]
            if event.source_type is SourceType.BANK:
                consumed_bank.add(event_id)
            elif event.source_type is SourceType.ERP:
                consumed_erp.add(event_id)

    proposals.extend(_orphan_proposals(context, consumed_bank, consumed_erp))
    matching_timing = _timing("deterministic_rules", matching_started, len(events), len(proposals))

    gate_started = perf_counter_ns()
    decisions = tuple(decide(context.run_id, proposal, policy) for proposal in proposals)
    exceptions = tuple(
        exception
        for proposal, decision in zip(proposals, decisions, strict=True)
        if (exception := create_exception(context.run_id, proposal, decision, policy)) is not None
    )
    gate_timing = _timing("risk_gate", gate_started, len(proposals), len(decisions))
    return KernelResult(
        tuple(proposals),
        decisions,
        exceptions,
        (context_timing, matching_timing, gate_timing),
    )


def _orphan_proposals(
    context: ReconciliationContext,
    consumed_bank: set[str],
    consumed_erp: set[str],
) -> tuple[CaseProposal, ...]:
    proposals: list[CaseProposal] = []
    orphan_bank = tuple(
        event
        for event in context.events
        if event.source_type is SourceType.BANK and event.event_id not in consumed_bank
    )
    for event in orphan_bank:
        proposals.append(_orphan(context, event, "ORPHAN_BANK_CREDIT"))
    orphan_erp = tuple(
        event
        for event in context.events
        if event.source_type is SourceType.ERP and event.event_id not in consumed_erp
    )
    grouped: dict[str, list[CanonicalEvent]] = {}
    for event in orphan_erp:
        grouped.setdefault(event.source_record_id.rsplit(":", 1)[0], []).append(event)
    for journal_id, events in sorted(grouped.items()):
        proposals.append(_orphan(context, tuple(events), "ORPHAN_ERP_POSTING", journal_id))
    return tuple(proposals)


def _orphan(
    context: ReconciliationContext,
    value: CanonicalEvent | tuple[CanonicalEvent, ...],
    reason: str,
    key: str | None = None,
) -> CaseProposal:
    events = (value,) if isinstance(value, CanonicalEvent) else value
    case_key = key or events[0].source_record_id
    links = tuple(evidence(event, "unconsumed source evidence") for event in events)
    amount = max(event.money.amount_minor for event in events)
    return CaseProposal(
        stable_id("proposal", context.run_id, case_key, context.policy.versioned_id),
        case_key,
        tuple(event.event_id for event in events),
        (
            ProofCheck(
                "SOURCE_EVIDENCE_MATCHED",
                True,
                False,
                None,
                False,
                True,
                links,
            ),
        ),
        links,
        (reason,),
        RULES,
        (),
        0,
        amount,
        False,
        ambiguous=True,
    )


def _timing(stage: str, started_ns: int, inputs: int, outputs: int) -> StageTiming:
    duration_ms = max(0, (perf_counter_ns() - started_ns) // 1_000_000)
    return StageTiming(stage, duration_ms, inputs, outputs)
