"""Human-approved action, export, and audit workflow."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from hashlib import sha256

from core.vericlose.application.review_cases import CaseView, ReviewQueryService
from core.vericlose.audit.events import AuditEvent
from core.vericlose.domain.actions import (
    ActionReceipt,
    JournalLine,
    JournalProposal,
    ProposedAction,
    ReviewDecision,
)
from core.vericlose.domain.enums import (
    ActionState,
    ActionType,
    Direction,
    EventType,
    ReviewState,
    SourceType,
)
from core.vericlose.domain.events import CanonicalEvent
from core.vericlose.domain.money import Money
from core.vericlose.ports.action_exporter import ActionExporter, ExportedArtifact
from core.vericlose.ports.repositories import PersistenceUnitOfWork
from core.vericlose.reconciliation.policy import ReconciliationPolicy

_EDITABLE_PAYLOAD_FIELDS = frozenset({"rationale", "clarification_text"})


class ActionNotFoundError(LookupError):
    pass


@dataclass(frozen=True, slots=True)
class ActionView:
    run_id: str
    action: ProposedAction
    reviews: tuple[ReviewDecision, ...]
    receipts: tuple[ActionReceipt, ...]


@dataclass(frozen=True, slots=True)
class ActionDownload:
    filename: str
    media_type: str
    content: bytes
    receipt: ActionReceipt


class ActionQueryService:
    def __init__(self, unit_of_work: Callable[[], PersistenceUnitOfWork]) -> None:
        self._unit_of_work = unit_of_work

    def list_for_run(self, run_id: str) -> tuple[ActionView, ...]:
        with self._unit_of_work() as repositories:
            actions = repositories.actions.list_for_run(run_id)
            reviews = repositories.reviews.list_for_run(run_id)
            receipts = repositories.actions.list_receipts(run_id)
        return tuple(
            ActionView(
                run_id,
                action,
                tuple(review for review in reviews if review.action_id == action.action_id),
                tuple(receipt for receipt in receipts if receipt.action_id == action.action_id),
            )
            for action in actions
        )

    def get(self, action_id: str) -> ActionView:
        with self._unit_of_work() as repositories:
            run_ids = repositories.runs.list_ids()
        for run_id in run_ids:
            match = next(
                (item for item in self.list_for_run(run_id) if item.action.action_id == action_id),
                None,
            )
            if match is not None:
                return match
        raise ActionNotFoundError(action_id)


class ActionService:
    def __init__(
        self,
        cases: ReviewQueryService,
        actions: ActionQueryService,
        policy: ReconciliationPolicy,
        exporter: ActionExporter,
        unit_of_work: Callable[[], PersistenceUnitOfWork],
    ) -> None:
        self._cases = cases
        self._actions = actions
        self._policy = policy
        self._exporter = exporter
        self._unit_of_work = unit_of_work

    def propose(self, case_id: str, *, proposed_at: datetime | None = None) -> ProposedAction:
        case = self._cases.get_case(case_id)
        if case.exception is None:
            raise ValueError("proved cases do not require a proposed action")
        existing = next(
            (
                item.action
                for item in self._actions.list_for_run(case.run_id)
                if item.action.case_id == case_id
            ),
            None,
        )
        if existing is not None:
            return existing
        timestamp = proposed_at or datetime.now(UTC)
        requested_type = case.exception.recommended_action
        journal = None
        action_type = requested_type
        if requested_type is ActionType.JOURNAL_EXPORT:
            journal = self._journal_for(case)
            if journal is None:
                action_type = ActionType.MANUAL_REVIEW
        reference = self._reference(case.events)
        posting_date = next(
            (
                event.value_date.isoformat()
                for event in case.events
                if event.source_type is SourceType.BANK and event.value_date is not None
            ),
            timestamp.date().isoformat(),
        )
        action_id = f"action_{_digest(case.run_id, case_id, action_type.value)[:20]}"
        rationale = self._rationale(case, action_type)
        payload = (
            ("reason_code", case.exception.reason_code),
            ("policy_version", self._policy.versioned_id),
            ("reference", reference or "not-available"),
            ("posting_date", posting_date),
            ("rationale", rationale),
            ("clarification_text", self._clarification(case)),
            ("idempotency_key", f"export:{action_id}"),
        )
        proposal = ProposedAction(
            action_id,
            action_type,
            case_id,
            ActionState.PROPOSED,
            journal,
            payload,
            case.exception.evidence_links,
            timestamp,
        )
        with self._unit_of_work() as repositories:
            repositories.actions.append_action(case.run_id, proposal)
            repositories.audit.append(
                AuditEvent(
                    f"audit_{action_id}_proposed",
                    case.run_id,
                    "ACTION_PROPOSED",
                    timestamp,
                    (
                        ("case_id", case_id),
                        ("action_id", action_id),
                        ("action_type", action_type.value),
                    ),
                )
            )
        return proposal

    def review(
        self,
        action_id: str,
        *,
        state: ReviewState,
        reviewer_id: str,
        comment: str | None,
        edits: Mapping[str, str] | None = None,
        reviewed_at: datetime | None = None,
    ) -> ActionView:
        view = self._actions.get(action_id)
        timestamp = reviewed_at or datetime.now(UTC)
        requested_edits = dict(edits or {})
        unknown = set(requested_edits) - _EDITABLE_PAYLOAD_FIELDS
        if unknown:
            raise ValueError(f"action fields cannot be edited: {', '.join(sorted(unknown))}")
        action = view.action
        if requested_edits:
            if action.state is not ActionState.PROPOSED:
                raise ValueError("only a proposed action can be edited")
            payload = dict(action.payload)
            for field, value in requested_edits.items():
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(f"{field} cannot be blank")
                payload[field] = value.strip()
            action = replace(action, payload=tuple(sorted(payload.items())))

        next_state = {
            ReviewState.APPROVED: ActionState.APPROVED,
            ReviewState.REJECTED: ActionState.REJECTED,
        }.get(state)
        if next_state is not None:
            if action.state is next_state:
                return view
            action = action.transition(next_state)
        identity = _digest(view.run_id, action_id, reviewer_id, state.value, timestamp.isoformat())
        review = ReviewDecision(
            f"review_{identity[:20]}",
            action_id,
            state,
            reviewer_id,
            timestamp,
            comment,
        )
        with self._unit_of_work() as repositories:
            if requested_edits or next_state is not None:
                repositories.actions.append_action(view.run_id, action)
            repositories.reviews.append(view.run_id, review)
            repositories.audit.append(
                AuditEvent(
                    f"audit_{identity[:20]}",
                    view.run_id,
                    "ACTION_REVIEW_RECORDED",
                    timestamp,
                    (
                        ("action_id", action_id),
                        ("state", state.value),
                        ("reviewer_id", reviewer_id),
                        ("edited", str(bool(requested_edits)).lower()),
                    ),
                )
            )
        return self._actions.get(action_id)

    def export(self, action_id: str, *, exported_at: datetime | None = None) -> ActionReceipt:
        view = self._actions.get(action_id)
        key = dict(view.action.payload)["idempotency_key"]
        with self._unit_of_work() as repositories:
            existing = repositories.actions.find_receipt(view.run_id, key)
        if existing is not None:
            return existing
        if view.action.state is not ActionState.APPROVED:
            raise ValueError("an action must be explicitly approved before export")
        artifact = self._exporter.export(view.run_id, view.action)
        timestamp = exported_at or datetime.now(UTC)
        receipt_id = f"receipt_{_digest(view.run_id, action_id, key)[:20]}"
        receipt = ActionReceipt(
            receipt_id,
            action_id,
            key,
            timestamp,
            (
                ("relative_path", artifact.relative_path),
                ("media_type", artifact.media_type),
                ("sha256", artifact.sha256),
                ("size_bytes", str(artifact.size_bytes)),
            ),
        )
        exported = view.action.transition(ActionState.EXPORTED)
        with self._unit_of_work() as repositories:
            repositories.actions.append_action(view.run_id, exported)
            repositories.actions.append_receipt(view.run_id, receipt)
            repositories.audit.append(
                AuditEvent(
                    f"audit_{receipt_id}",
                    view.run_id,
                    "ACTION_EXPORTED",
                    timestamp,
                    (
                        ("action_id", action_id),
                        ("receipt_id", receipt_id),
                        ("sha256", artifact.sha256),
                    ),
                )
            )
        return receipt

    def download(self, action_id: str) -> ActionDownload:
        view = self._actions.get(action_id)
        receipt = next(
            (
                item
                for item in reversed(view.receipts)
                if item.idempotency_key.startswith("export:")
            ),
            None,
        )
        if receipt is None:
            raise LookupError(f"action {action_id} has no exported artifact")
        payload = dict(receipt.result_payload)
        artifact = ExportedArtifact(
            payload["relative_path"],
            payload["media_type"],
            payload["sha256"],
            int(payload["size_bytes"]),
        )
        return ActionDownload(
            artifact.relative_path.rsplit("/", 1)[-1],
            artifact.media_type,
            self._exporter.read(artifact),
            receipt,
        )

    def _journal_for(self, case: CaseView) -> JournalProposal | None:
        assert case.exception is not None
        if case.exception.reason_code == "MISSING_ERP_POSTING":
            return self._missing_erp_journal(case)
        if case.exception.reason_code == "DUPLICATE_ERP_POSTING":
            return self._duplicate_reversal(case)
        return None

    def _missing_erp_journal(self, case: CaseView) -> JournalProposal:
        gateway = tuple(event for event in case.events if event.source_type is SourceType.GATEWAY)
        bank = tuple(
            event
            for event in case.events
            if event.source_type is SourceType.BANK and event.direction is Direction.CREDIT
        )
        if len(bank) != 1:
            raise ValueError("missing-ERP journal requires one proved bank receipt")
        component = {
            kind: sum(event.money.amount_minor for event in gateway if event.event_type is kind)
            for kind in (EventType.FEE, EventType.TAX)
        }
        lines: list[JournalLine] = [
            self._line(
                "bank", bank[0].money.amount_minor, Direction.DEBIT, "Bank receipt", (bank[0],)
            )
        ]
        if component[EventType.FEE]:
            fee_events = tuple(event for event in gateway if event.event_type is EventType.FEE)
            lines.append(
                self._line(
                    "fee",
                    component[EventType.FEE],
                    Direction.DEBIT,
                    "Gateway fee expense",
                    fee_events,
                )
            )
        if component[EventType.TAX]:
            tax_events = tuple(event for event in gateway if event.event_type is EventType.TAX)
            lines.append(
                self._line(
                    "tax",
                    component[EventType.TAX],
                    Direction.DEBIT,
                    "Input GST on gateway fee",
                    tax_events,
                )
            )
        debit_total = sum(line.money.amount_minor for line in lines)
        clearing_events = tuple(
            event
            for event in gateway
            if event.event_type
            in {EventType.PAYMENT, EventType.REFUND, EventType.ADJUSTMENT, EventType.SETTLEMENT}
        )
        lines.append(
            self._line(
                "clearing",
                debit_total,
                Direction.CREDIT,
                "Gateway clearing",
                clearing_events,
            )
        )
        return JournalProposal(tuple(lines))

    def _duplicate_reversal(self, case: CaseView) -> JournalProposal:
        journals: dict[str, list[CanonicalEvent]] = defaultdict(list)
        for event in case.events:
            if event.source_type is SourceType.ERP:
                journals[event.source_record_id.rsplit(":", 1)[0]].append(event)
        if len(journals) < 2:
            raise ValueError("duplicate reversal requires at least two ERP journals")
        duplicate_id = next(
            (journal_id for journal_id in sorted(journals) if "duplicate" in journal_id.lower()),
            sorted(journals)[-1],
        )
        lines = tuple(
            JournalLine(
                event.account_code or "UNMAPPED",
                event.money,
                Direction.CREDIT if event.direction is Direction.DEBIT else Direction.DEBIT,
                f"Reverse duplicate posting {duplicate_id}",
                (self._event_evidence(event),),
            )
            for event in journals[duplicate_id]
        )
        return JournalProposal(lines)

    def _line(
        self,
        role: str,
        amount_minor: int,
        direction: Direction,
        narration: str,
        events: tuple[CanonicalEvent, ...],
    ) -> JournalLine:
        configured = self._policy.role(role)
        if configured.direction is not direction:
            raise ValueError(f"policy direction for {role} does not match journal design")
        return JournalLine(
            sorted(configured.account_codes)[0],
            Money(amount_minor, self._policy.currency),
            direction,
            narration,
            tuple(self._event_evidence(event) for event in events),
        )

    @staticmethod
    def _event_evidence(event: CanonicalEvent):
        from core.vericlose.domain.evidence import EvidenceLink

        return EvidenceLink(
            event.event_id,
            event.lineage.source_file_id,
            event.lineage.table_name,
            event.lineage.row_number,
            event.lineage.raw_row_hash,
            "Deterministic journal source",
        )

    @staticmethod
    def _reference(events: tuple[CanonicalEvent, ...]) -> str | None:
        gateway_settlement = next(
            (
                event.settlement_reference
                for event in events
                if event.source_type is SourceType.GATEWAY and event.settlement_reference
            ),
            None,
        )
        return gateway_settlement or next(
            (
                reference
                for event in events
                for reference in (
                    event.settlement_reference,
                    event.external_reference,
                    event.bank_utr,
                )
                if reference
            ),
            None,
        )

    @staticmethod
    def _rationale(case: CaseView, action_type: ActionType) -> str:
        assert case.exception is not None
        if action_type is ActionType.MANUAL_REVIEW:
            return (
                f"{case.exception.reason_code} has no deterministic posting template; "
                "retain for manual review."
            )
        return (
            f"Policy routes {case.exception.reason_code} to {action_type.value}; "
            "source evidence remains authoritative."
        )

    @staticmethod
    def _clarification(case: CaseView) -> str:
        assert case.exception is not None
        return (
            f"Please provide evidence that resolves {case.exception.reason_code} for the cited "
            f"settlement. Current amount at risk is {case.exception.amount_at_risk.amount_minor} "
            "paise; no explanation has been assumed."
        )


def _digest(*parts: str) -> str:
    return sha256("|".join(parts).encode()).hexdigest()
