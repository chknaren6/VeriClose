"""Seeded construction of an internally consistent synthetic merchant ledger."""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

from core.vericlose.domain.enums import ActionType, EventType, ProofLevel
from synthetic.models import BankRow, CaseContext, ErpRow, GatewayRow, GeneratedBatch
from synthetic.truth.models import CaseTruth, EventTruth, TruthDataset


@dataclass(frozen=True, slots=True)
class SyntheticConfig:
    seed: int = 42
    payments: int = 120
    settlements: int = 24
    exception_rate: float = 0.40

    def __post_init__(self) -> None:
        if isinstance(self.seed, bool) or not isinstance(self.seed, int) or self.seed < 0:
            raise ValueError("seed must be a non-negative integer")
        if isinstance(self.payments, bool) or not isinstance(self.payments, int):
            raise TypeError("payments must be an integer")
        if isinstance(self.settlements, bool) or not isinstance(self.settlements, int):
            raise TypeError("settlements must be an integer")
        if isinstance(self.exception_rate, bool) or not isinstance(
            self.exception_rate, (int, float)
        ):
            raise TypeError("exception_rate must be numeric")
        if self.payments < 50:
            raise ValueError("payments must be at least 50 for a credible batch")
        if self.settlements < 14:
            raise ValueError("settlements must be at least 14 to exercise the scenario suite")
        if self.settlements >= self.payments:
            raise ValueError("settlements must be smaller than payments")
        if not 0 <= self.exception_rate <= 1:
            raise ValueError("exception_rate must be between 0 and 1")


def seeded_rng(seed: int, namespace: str) -> random.Random:
    """Use a stable digest instead of Python's process-randomized `hash()`."""

    digest = hashlib.sha256(f"{seed}:{namespace}".encode()).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def generate_clean_batch(config: SyntheticConfig) -> GeneratedBatch:
    amount_rng = seeded_rng(config.seed, "amounts")
    base_date = date(2026, 4, 1)
    counts = _payments_per_settlement(config.payments, config.settlements)

    gateway_rows: list[GatewayRow] = []
    bank_rows: list[BankRow] = []
    erp_rows: list[ErpRow] = []
    contexts: list[CaseContext] = []
    event_truth: list[EventTruth] = []
    case_truth: list[CaseTruth] = []
    payment_number = 1

    for index, payment_count in enumerate(counts, start=1):
        case_id = f"case_{index:04d}"
        settlement_id = f"set_{config.seed:04d}_{index:04d}"
        utr = f"UTR{config.seed:04d}{index:08d}"
        settlement_day = base_date + timedelta(days=index - 1)
        event_at = datetime.combine(settlement_day, time(10), tzinfo=UTC)
        case_gateway: list[GatewayRow] = []

        for _ in range(payment_count):
            amount_minor = amount_rng.randrange(5_000, 200_001, 100)
            payment_id = f"pay_{config.seed:04d}_{payment_number:06d}"
            row = GatewayRow(
                case_id=case_id,
                gateway_event_id=f"gwe_{config.seed:04d}_{payment_number:06d}",
                event_type=EventType.PAYMENT,
                transaction_id=payment_id,
                settlement_id=settlement_id,
                amount_minor=amount_minor,
                currency="INR",
                event_at=event_at,
                status="captured",
                reference=f"order_{config.seed:04d}_{payment_number:06d}",
                narration="Synthetic captured payment",
            )
            case_gateway.append(row)
            payment_number += 1

        gross_minor = sum(row.amount_minor for row in case_gateway)
        fee_minor = max(100, gross_minor * amount_rng.randint(180, 260) // 10_000)
        tax_minor = fee_minor * 18 // 100
        net_minor = gross_minor - fee_minor - tax_minor
        if net_minor <= 0:
            raise AssertionError("generator produced a non-positive settlement")

        component_rows = (
            GatewayRow(
                case_id,
                f"gwe_fee_{config.seed:04d}_{index:04d}",
                EventType.FEE,
                "",
                settlement_id,
                fee_minor,
                "INR",
                event_at,
                "processed",
                settlement_id,
                "Synthetic gateway fee",
            ),
            GatewayRow(
                case_id,
                f"gwe_tax_{config.seed:04d}_{index:04d}",
                EventType.TAX,
                "",
                settlement_id,
                tax_minor,
                "INR",
                event_at,
                "processed",
                settlement_id,
                "Synthetic GST on gateway fee",
            ),
            GatewayRow(
                case_id,
                f"gwe_set_{config.seed:04d}_{index:04d}",
                EventType.SETTLEMENT,
                "",
                settlement_id,
                net_minor,
                "INR",
                event_at,
                "settled",
                utr,
                "Synthetic net settlement",
            ),
        )
        case_gateway.extend(component_rows)
        gateway_rows.extend(case_gateway)

        bank = BankRow(
            case_id,
            f"bnk_{config.seed:04d}_{index:04d}",
            settlement_day + timedelta(days=1),
            settlement_day + timedelta(days=1),
            net_minor,
            0,
            utr,
            f"Synthetic settlement {settlement_id}",
            "INR",
            "acct_demo_01",
        )
        bank_rows.append(bank)

        journal_id = f"jrn_{config.seed:04d}_{index:04d}"
        case_erp = _balanced_erp_rows(
            case_id=case_id,
            journal_id=journal_id,
            posting_date=bank.value_date,
            settlement_id=settlement_id,
            net_minor=net_minor,
            fee_minor=fee_minor,
            tax_minor=tax_minor,
            clearing_minor=gross_minor,
        )
        erp_rows.extend(case_erp)

        context = CaseContext(
            case_id,
            settlement_id,
            utr,
            gross_minor,
            fee_minor,
            tax_minor,
            0,
            net_minor,
        )
        contexts.append(context)
        case_rows = (*case_gateway, bank, *case_erp)
        labels = tuple(
            EventTruth(row.source_type, row.source_record_id, case_id, _role(row))
            for row in case_rows
        )
        event_truth.extend(labels)
        case_truth.append(
            CaseTruth(
                case_id=case_id,
                scenario="clean_exact",
                expected_member_keys=tuple(label.key for label in labels),
                expected_proof_level=ProofLevel.PROVED,
                expected_exception_category=None,
                expected_severity=None,
                expected_next_action=ActionType.NO_ACTION,
                valid_timing_difference=False,
                description="All gateway, bank, and ERP evidence agrees exactly.",
            )
        )

    return GeneratedBatch(
        seed=config.seed,
        gateway_rows=tuple(gateway_rows),
        bank_rows=tuple(bank_rows),
        erp_rows=tuple(erp_rows),
        cases=tuple(contexts),
        truth=TruthDataset("1.0", config.seed, tuple(event_truth), tuple(case_truth)),
    )


def _payments_per_settlement(payments: int, settlements: int) -> tuple[int, ...]:
    base, remainder = divmod(payments, settlements)
    return tuple(base + (1 if index < remainder else 0) for index in range(settlements))


def _balanced_erp_rows(
    *,
    case_id: str,
    journal_id: str,
    posting_date: date,
    settlement_id: str,
    net_minor: int,
    fee_minor: int,
    tax_minor: int,
    clearing_minor: int,
) -> tuple[ErpRow, ...]:
    lines = (
        ("110000", net_minor, 0, "Synthetic bank receipt"),
        ("510000", fee_minor, 0, "Synthetic gateway fee expense"),
        ("140000", tax_minor, 0, "Synthetic input GST"),
        ("120000", 0, clearing_minor, "Synthetic clearing credit"),
    )
    return tuple(
        ErpRow(
            case_id=case_id,
            erp_record_id=f"{journal_id}_line_{line_number}",
            journal_id=journal_id,
            line_number=line_number,
            posting_date=posting_date,
            account_code=account_code,
            debit_minor=debit_minor,
            credit_minor=credit_minor,
            currency="INR",
            external_reference=settlement_id,
            narration=narration,
        )
        for line_number, (account_code, debit_minor, credit_minor, narration) in enumerate(
            lines, start=1
        )
    )


def _role(row: GatewayRow | BankRow | ErpRow) -> str:
    if isinstance(row, GatewayRow):
        return f"GATEWAY_{row.event_type.value}"
    if isinstance(row, BankRow):
        return "BANK_RECEIPT"
    return "ERP_DEBIT" if row.debit_minor else "ERP_CREDIT"
