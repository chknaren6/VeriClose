"""Settlement-to-bank-to-ERP proof construction."""

from __future__ import annotations

from core.vericlose.domain.enums import Direction, EventType, SourceType
from core.vericlose.domain.events import CanonicalEvent
from core.vericlose.domain.evidence import EvidenceLink, ProofCheck
from core.vericlose.reconciliation.context import ReconciliationContext
from core.vericlose.reconciliation.proposals import (
    CaseProposal,
    evidence,
    stable_id,
    unique_evidence,
)
from core.vericlose.reconciliation.rules.grouping import amount_groups
from core.vericlose.reconciliation.rules.support import score_bank_group

RULE_VERSION = "segment4-v1"
RULES = (
    "exact_identifier_v1",
    "settlement_component_v1",
    "bank_receipt_v1",
    "erp_posting_v1",
    "bounded_grouping_v1",
    "candidate_support_v1",
)


def analyze_settlement(
    context: ReconciliationContext,
    settlement_reference: str,
    consumed_bank_ids: frozenset[str] = frozenset(),
) -> CaseProposal:
    gateway = context.gateway_settlement(settlement_reference)
    gateway_links = tuple(evidence(event, "gateway settlement component") for event in gateway)
    settlement_rows = tuple(event for event in gateway if event.event_type is EventType.SETTLEMENT)
    checks: list[ProofCheck] = []
    reasons: list[str] = []
    ambiguous = False
    invalid_input = False

    checks.append(
        _check(
            "GATEWAY_SETTLEMENT_UNIQUE",
            1,
            len(settlement_rows),
            len(settlement_rows) == 1,
            gateway_links,
        )
    )
    if len(settlement_rows) != 1:
        reasons.append("DUPLICATE_IDENTIFIER" if settlement_rows else "UNKNOWN_UNRESOLVED")
    anchor = settlement_rows[0] if settlement_rows else gateway[0]
    expected_net = sum(
        event.money.amount_minor * context.policy.component_sign(event.event_type, event.direction)
        for event in gateway
        if event.event_type is not EventType.SETTLEMENT
    )
    clearing_expected = sum(
        event.money.amount_minor * context.policy.component_sign(event.event_type, event.direction)
        for event in gateway
        if event.event_type in {EventType.PAYMENT, EventType.REFUND, EventType.ADJUSTMENT}
    )
    observed_net = settlement_rows[0].money.amount_minor if settlement_rows else 0
    component_tolerance = context.policy.tolerance("settlement_components")
    component_passed = abs(expected_net - observed_net) <= component_tolerance
    checks.append(
        _check(
            "SETTLEMENT_COMPONENT_INVARIANT",
            expected_net,
            observed_net,
            component_passed,
            gateway_links,
            component_tolerance,
        )
    )
    checks.append(
        ProofCheck(
            "SETTLEMENT_COMPONENT_VARIANCE",
            0,
            observed_net - expected_net,
            component_tolerance,
            component_passed,
            False,
            gateway_links,
        )
    )
    if not component_passed:
        reasons.append("SETTLEMENT_COMPONENT_MISMATCH")

    expected_utr = settlement_rows[0].external_reference if settlement_rows else None
    bank_group, bank_candidates, bank_ambiguous, bank_bounded = _select_bank_group(
        context,
        anchor,
        observed_net,
        consumed_bank_ids,
    )
    exact_utr_candidates = tuple(
        event
        for event in context.indexes.by_utr.get(expected_utr or "", ())
        if event.source_type is SourceType.BANK
        and event.event_id not in consumed_bank_ids
        and event.legal_entity_id == context.legal_entity_id
        and event.money.currency == context.policy.currency
    )
    identifier_conflict = (
        len(exact_utr_candidates) > 1
        and sum(event.money.amount_minor for event in exact_utr_candidates) != observed_net
    )
    if identifier_conflict:
        bank_group = exact_utr_candidates
        bank_candidates = exact_utr_candidates
        bank_ambiguous = False
        reasons.append("DUPLICATE_IDENTIFIER")
    all_bank_links = tuple(evidence(event, "bank receipt candidate") for event in bank_candidates)
    cited_bank = all_bank_links or gateway_links
    bank_present = bool(bank_group)
    checks.append(_check("BANK_RECEIPT_PRESENT", True, bank_present, bank_present, cited_bank))
    if not bank_present:
        reasons.append("MISSING_BANK_RECEIPT")
    bank_amount = sum(event.money.amount_minor for event in bank_group)
    amount_passed = bank_present and abs(bank_amount - observed_net) <= context.policy.tolerance(
        "bank_receipt"
    )
    checks.append(
        _check(
            "BANK_RECEIPT_AMOUNT",
            observed_net,
            bank_amount,
            amount_passed,
            cited_bank,
            context.policy.tolerance("bank_receipt"),
        )
    )
    if bank_present and not amount_passed:
        reasons.append("BANK_AMOUNT_MISMATCH")
    direction_passed = bank_present and all(
        event.direction is Direction.CREDIT for event in bank_group
    )
    checks.append(
        _check(
            "BANK_RECEIPT_DIRECTION",
            Direction.CREDIT.value,
            _directions(bank_group),
            direction_passed,
            cited_bank,
        )
    )
    reference_passed = (
        bank_present
        and bool(expected_utr)
        and all(event.bank_utr == expected_utr for event in bank_group)
    )
    checks.append(
        _check(
            "BANK_RECEIPT_REFERENCE",
            expected_utr,
            ",".join(sorted({event.bank_utr or "" for event in bank_group})),
            reference_passed,
            cited_bank,
        )
    )
    if bank_present and amount_passed and not reference_passed:
        reasons.append("REFERENCE_MISMATCH")
    date_passed = bank_present and all(
        event.value_date is not None
        and context.policy.dates.settlement_to_bank_min_days
        <= (event.value_date - anchor.event_at.date()).days
        <= context.policy.dates.settlement_to_bank_max_days
        for event in bank_group
    )
    checks.append(
        _check(
            "BANK_RECEIPT_DATE",
            f"{context.policy.dates.settlement_to_bank_min_days}.."
            f"{context.policy.dates.settlement_to_bank_max_days}",
            ",".join(
                str((event.value_date - anchor.event_at.date()).days)
                for event in bank_group
                if event.value_date
            ),
            date_passed,
            cited_bank,
        )
    )
    if bank_present and not date_passed:
        reasons.append("BANK_DATE_OUT_OF_RANGE")
    bank_unique = bank_present and not bank_ambiguous and not bank_bounded
    checks.append(_check("BANK_RECEIPT_UNIQUE", True, bank_unique, bank_unique, cited_bank))
    if bank_ambiguous or bank_bounded:
        ambiguous = True
        reasons.append("BANK_RECEIPT_AMBIGUOUS")

    erp_journals = context.erp_journals(settlement_reference)
    erp_events = tuple(event for journal in erp_journals for event in journal)
    erp_links = tuple(evidence(event, "ERP posting candidate") for event in erp_events)
    cited_erp = erp_links or gateway_links
    checks.append(
        _check("ERP_JOURNAL_PRESENT", True, bool(erp_journals), bool(erp_journals), cited_erp)
    )
    if not erp_journals:
        reasons.append("MISSING_ERP_POSTING")
    erp_unique = len(erp_journals) == 1
    checks.append(_check("ERP_JOURNAL_UNIQUE", 1, len(erp_journals), erp_unique, cited_erp))
    if len(erp_journals) > 1:
        reasons.append("DUPLICATE_ERP_POSTING")
    journal = erp_journals[0] if len(erp_journals) == 1 else ()
    debit_total = sum(
        event.money.amount_minor for event in journal if event.direction is Direction.DEBIT
    )
    credit_total = sum(
        event.money.amount_minor for event in journal if event.direction is Direction.CREDIT
    )
    balanced = bool(journal) and debit_total == credit_total
    checks.append(_check("ERP_JOURNAL_BALANCED", debit_total, credit_total, balanced, cited_erp))
    if journal and not balanced:
        invalid_input = True
        reasons.append("ERP_JOURNAL_UNBALANCED")

    fees = sum(event.money.amount_minor for event in gateway if event.event_type is EventType.FEE)
    taxes = sum(event.money.amount_minor for event in gateway if event.event_type is EventType.TAX)
    for check_code, role, expected in (
        ("ERP_BANK_POSTING", "bank", observed_net),
        ("ERP_CLEARING_POSTING", "clearing", clearing_expected),
        ("ERP_FEE_POSTING", "fee", fees),
        ("ERP_TAX_POSTING", "tax", taxes),
    ):
        role_policy = context.policy.role(role)
        observed = sum(
            event.money.amount_minor
            for event in journal
            if event.account_code in role_policy.account_codes
            and event.direction is role_policy.direction
        )
        passed = bool(journal) and abs(observed - expected) <= context.policy.tolerance(
            "erp_posting"
        )
        checks.append(
            _check(
                check_code,
                expected,
                observed,
                passed,
                cited_erp,
                context.policy.tolerance("erp_posting"),
            )
        )
        if journal and balanced and not passed and "ERP_POSTING_MISMATCH" not in reasons:
            reasons.append("ERP_POSTING_MISMATCH")

    hard_unique = len(settlement_rows) == 1 and bank_unique and erp_unique
    check_by_code = {check.check_code: check for check in checks}
    proof_checks_passed = context.policy.auto_clear_required_checks <= check_by_code.keys() and all(
        check_by_code[code].passed for code in context.policy.auto_clear_required_checks
    )
    if proof_checks_passed and hard_unique:
        score, features = 0, ()
    else:
        score, features = score_bank_group(
            bank_group,
            expected_minor=observed_net,
            settlement_reference=settlement_reference,
            expected_utr=expected_utr,
            settlement_date=anchor.event_at.date(),
            policy=context.policy,
        )
    support_links = cited_bank
    for feature in features:
        checks.append(
            ProofCheck(
                f"SUPPORT_{feature.name.upper()}",
                context.policy.support_scoring_bps[feature.name],
                feature.score_bps,
                None,
                feature.score_bps == context.policy.support_scoring_bps[feature.name],
                False,
                support_links,
            )
        )
    selected_events = tuple(
        sorted((*gateway, *bank_candidates, *erp_events), key=lambda event: event.event_id)
    )
    links = unique_evidence((*gateway_links, *all_bank_links, *erp_links))
    return CaseProposal(
        stable_id("proposal", context.run_id, settlement_reference, context.policy.versioned_id),
        settlement_reference,
        tuple(event.event_id for event in selected_events),
        tuple(checks),
        links,
        tuple(dict.fromkeys(reasons)),
        RULES,
        features,
        score,
        max(observed_net, expected_net, 0),
        hard_unique,
        ambiguous,
        invalid_input,
    )


def _select_bank_group(
    context: ReconciliationContext,
    anchor: CanonicalEvent,
    expected_minor: int,
    consumed_ids: frozenset[str],
) -> tuple[
    tuple[CanonicalEvent, ...],
    tuple[CanonicalEvent, ...],
    bool,
    bool,
]:
    candidates = context.bank_candidates(
        settlement_date=anchor.event_at.date(), consumed_event_ids=consumed_ids
    )
    grouping = amount_groups(candidates, expected_minor, context.policy.grouping)
    if len(grouping.groups) == 1:
        return grouping.groups[0], grouping.groups[0], False, grouping.bounded_out
    if len(grouping.groups) > 1:
        considered = tuple(
            sorted(
                {event.event_id: event for group in grouping.groups for event in group}.values(),
                key=lambda event: event.event_id,
            )
        )
        return grouping.groups[0], considered, True, grouping.bounded_out
    expected_utr = anchor.external_reference
    exact = tuple(
        event
        for event in context.indexes.by_utr.get(expected_utr or "", ())
        if event.source_type is SourceType.BANK
        and event.event_id not in consumed_ids
        and event.legal_entity_id == context.legal_entity_id
        and event.money.currency == context.policy.currency
    )
    if len(exact) == 1:
        return exact, exact, False, grouping.bounded_out
    if len(exact) > 1:
        return exact[:1], exact, True, grouping.bounded_out
    return (), (), False, grouping.bounded_out


def _check(
    code: str,
    expected,
    observed,
    passed: bool,
    links: tuple[EvidenceLink, ...],
    tolerance_minor: int | None = None,
) -> ProofCheck:
    return ProofCheck(code, expected, observed, tolerance_minor, passed, True, links)


def _directions(events: tuple[CanonicalEvent, ...]) -> str:
    return ",".join(sorted({event.direction.value for event in events}))
