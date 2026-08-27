from datetime import date
from io import BytesIO
from pathlib import Path

import pytest
from openpyxl import Workbook

from core.vericlose.adapters import BankAdapter, ErpGlAdapter, GatewayAdapter
from core.vericlose.domain.enums import Direction, EventType, SourceType
from core.vericlose.domain.events import CanonicalEvent
from core.vericlose.ingestion.contracts import NormalizationContext, SourceDocument, ValidationStage
from core.vericlose.ingestion.mappings import MappingCatalog

CATALOG = MappingCatalog.from_directory(Path("config/mappings"))
CONTEXT = NormalizationContext("run-unit", "merchant-in")
FIXTURES = Path("tests/fixtures/schema")


def _fixture(name: str) -> SourceDocument:
    return SourceDocument.from_bytes(
        file_id=name.removesuffix(".csv"),
        original_name=name,
        media_type="text/csv",
        content=(FIXTURES / name).read_bytes(),
    )


def test_gateway_normalizes_supported_types_and_quarantines_unknown() -> None:
    profile = CATALOG.get("gateway_standard@1.0.0")
    adapter = GatewayAdapter((profile,))
    valid = adapter.normalize(_fixture("gateway_valid.csv"), profile, CONTEXT)
    invalid = adapter.normalize(_fixture("gateway_invalid.csv"), profile, CONTEXT)

    assert {event.event_type for event in valid.events} == {
        EventType.PAYMENT,
        EventType.SETTLEMENT,
    }
    assert invalid.quarantined_row_count == 1
    assert "GATEWAY_EVENT_TYPE_UNKNOWN" in invalid.row_dispositions[0].issue_codes


def test_gateway_preserves_raw_sign_and_maps_direction() -> None:
    profile = CATALOG.get("gateway_standard@1.0.0")
    adapter = GatewayAdapter((profile,))
    document = _csv(
        "gateway-sign.csv",
        "gateway_event_id,event_type,transaction_id,settlement_id,amount_minor,currency,"
        "event_at,status,reference,narration\n"
        "g1,REFUND,p1,s1,-500,INR,2026-04-01T00:00:00+00:00,processed,r1,reversal\n",
    )
    event = adapter.normalize(document, profile, CONTEXT).events[0]
    assert event.money.amount_minor == 500
    assert event.direction is Direction.CREDIT
    assert dict((field.name, field.value) for field in event.raw_fields)["amount_minor"] == "-500"


def test_bank_signed_and_debit_credit_layouts_are_equivalent() -> None:
    debit_credit = CATALOG.get("bank_debit_credit@1.0.0")
    signed = CATALOG.get("bank_signed@1.0.0")
    adapter = BankAdapter((debit_credit, signed))
    credit_event = adapter.normalize(
        _csv(
            "bank-dc.csv",
            "bank_record_id,value_date,booking_date,credit_amount,debit_amount,utr,narration,"
            "currency,account_reference\n"
            "b1,2026-04-02,2026-04-02,121.05,0.00,U1,Settlement,INR,main\n",
        ),
        debit_credit,
        CONTEXT,
    ).events[0]
    signed_event = adapter.normalize(
        _csv(
            "bank-signed.csv",
            "bank_record_id,value_date,booking_date,signed_amount,utr,narration,currency,"
            "account_reference\n"
            "b1,2026-04-02,2026-04-02,121.05,U1,Settlement,INR,main\n",
        ),
        signed,
        CONTEXT,
    ).events[0]
    assert credit_event.money == signed_event.money
    assert credit_event.direction is signed_event.direction is Direction.CREDIT
    assert credit_event.value_date == signed_event.value_date


def test_invalid_bank_row_has_precise_semantic_diagnostic() -> None:
    profile = CATALOG.get("bank_debit_credit@1.0.0")
    report = BankAdapter((profile,)).validate(_fixture("bank_invalid.csv"), profile)
    issue = report.issues[0]
    assert issue.stage is ValidationStage.SEMANTIC
    assert issue.file_id == "bank_invalid"
    assert issue.table_name == "rows"
    assert issue.row_number == 2
    assert issue.field_name == "value_date"
    assert issue.supplied_value == "not-a-date"
    assert issue.code == "VALUE_DATE_INVALID"
    assert issue.suggested_fix


def test_erp_unbalanced_journal_is_retained_as_accounting_exception() -> None:
    profile = CATALOG.get("erp_gl_standard@1.0.0")
    adapter = ErpGlAdapter((profile,))
    document = _csv(
        "erp-unbalanced.csv",
        "journal_id,line_number,posting_date,account_code,debit_amount,credit_amount,"
        "currency,external_reference,narration\n"
        "j1,1,2026-04-02,bank,100.00,0.00,INR,s1,debit\n"
        "j1,2,2026-04-02,clearing,0.00,90.00,INR,s1,credit\n",
    )
    result = adapter.normalize(document, profile, CONTEXT)
    assert len(result.events) == 2
    assert result.quarantined_row_count == 0
    assert all(not row.issue_codes for row in result.row_dispositions)
    assert all(issue.stage is ValidationStage.ACCOUNTING for issue in result.issues)
    assert all(not issue.blocking for issue in result.issues)
    totals = {
        item.component: item.amount_minor
        for item in adapter.control_totals(result.events).components
    }
    assert totals == {"DEBIT": 10_000, "CREDIT": 9_000}


def test_xlsx_gateway_is_supported_without_losing_numeric_amount() -> None:
    profile = CATALOG.get("gateway_standard@1.0.0")
    adapter = GatewayAdapter((profile,))
    headers = [field.aliases[0] for field in profile.fields]
    row = [
        "g-xlsx",
        "PAYMENT",
        "p-xlsx",
        "s-xlsx",
        12500,
        "INR",
        "2026-04-01T10:00:00+00:00",
        "captured",
        "order-xlsx",
        "Payment",
    ]
    document = _xlsx("gateway-xlsx", headers, row)
    result = adapter.normalize(document, profile, CONTEXT)
    assert result.events[0].money.amount_minor == 12_500
    assert result.events[0].lineage.table_name == "Sheet"


def test_xlsx_bank_decimal_and_excel_dates_are_parsed_exactly() -> None:
    profile = CATALOG.get("bank_debit_credit@1.0.0")
    adapter = BankAdapter((profile,))
    headers = [field.aliases[0] for field in profile.fields]
    row = [
        "bank-xlsx",
        date(2026, 4, 2),
        date(2026, 4, 2),
        121.05,
        0,
        "UTR-XLSX",
        "Settlement",
        "INR",
        "main",
    ]
    event = adapter.normalize(_xlsx("bank-xlsx", headers, row), profile, CONTEXT).events[0]
    assert event.money.amount_minor == 12_105
    assert event.value_date == date(2026, 4, 2)


@pytest.mark.parametrize(
    ("source_type", "alternate_profile_id", "alternate_header", "alternate_rows"),
    [
        (
            SourceType.GATEWAY,
            "gateway_payments_alt@1.0.0",
            "payment_event_key,record_type,payment_id,settlement_ref,value_paise,"
            "currency_code,created_at,payment_status,merchant_reference,description",
            "g1,PAYMENT,p1,s1,10000,INR,2026-04-01T00:00:00+00:00,captured,o1,payment",
        ),
        (
            SourceType.GATEWAY,
            "gateway_payments_alt@1.0.0",
            "event_key,type,transaction_ref,settlement_key,amount_paise,ccy,occurred_at,"
            "state,order_ref,notes",
            "g1,PAYMENT,p1,s1,10000,INR,2026-04-01T00:00:00+00:00,captured,o1,payment",
        ),
        (
            SourceType.BANK,
            "bank_signed@1.0.0",
            "record_id,transaction_date,posted_date,transaction_amount,bank_reference,"
            "description,ccy,account_id",
            "b1,2026-04-02,2026-04-02,100.00,U1,settlement,INR,main",
        ),
        (
            SourceType.BANK,
            "bank_dr_cr_alt@1.0.0",
            "statement_line_id,effective_date,ledger_date,credit,debit,reference_number,"
            "memo,currency_code,bank_account",
            "b1,2026-04-02,2026-04-02,100.00,0.00,U1,settlement,INR,main",
        ),
        (
            SourceType.ERP,
            "erp_gl_alt@1.0.0",
            "document_number,document_line,document_date,gl_account,debit_value,credit_value,"
            "currency_code,reference,description",
            "j1,1,2026-04-02,bank,100.00,0.00,INR,s1,debit\n"
            "j1,2,2026-04-02,clearing,0.00,100.00,INR,s1,credit",
        ),
        (
            SourceType.ERP,
            "erp_gl_alt@1.0.0",
            "voucher_id,sequence,gl_date,ledger_account,dr_amount,cr_amount,ccy,"
            "settlement_ref,memo",
            "j1,1,2026-04-02,bank,100.00,0.00,INR,s1,debit\n"
            "j1,2,2026-04-02,clearing,0.00,100.00,INR,s1,credit",
        ),
    ],
)
def test_alternate_layouts_produce_equivalent_canonical_finance_values(
    source_type: SourceType,
    alternate_profile_id: str,
    alternate_header: str,
    alternate_rows: str,
) -> None:
    standard_profile_id, standard_header, standard_rows = _standard_layout(source_type)
    standard_profile = CATALOG.get(standard_profile_id)
    alternate_profile = CATALOG.get(alternate_profile_id)
    adapter_type = {
        SourceType.GATEWAY: GatewayAdapter,
        SourceType.BANK: BankAdapter,
        SourceType.ERP: ErpGlAdapter,
    }[source_type]
    adapter = adapter_type((standard_profile, alternate_profile))
    standard = adapter.normalize(
        _csv("standard.csv", f"{standard_header}\n{standard_rows}\n"),
        standard_profile,
        CONTEXT,
    )
    alternate = adapter.normalize(
        _csv("alternate.csv", f"{alternate_header}\n{alternate_rows}\n"),
        alternate_profile,
        CONTEXT,
    )
    assert tuple(_finance_projection(event) for event in standard.events) == tuple(
        _finance_projection(event) for event in alternate.events
    )


def _standard_layout(source_type: SourceType) -> tuple[str, str, str]:
    if source_type is SourceType.GATEWAY:
        return (
            "gateway_standard@1.0.0",
            "gateway_event_id,event_type,transaction_id,settlement_id,amount_minor,currency,"
            "event_at,status,reference,narration",
            "g1,PAYMENT,p1,s1,10000,INR,2026-04-01T00:00:00+00:00,captured,o1,payment",
        )
    if source_type is SourceType.BANK:
        return (
            "bank_debit_credit@1.0.0",
            "bank_record_id,value_date,booking_date,credit_amount,debit_amount,utr,narration,"
            "currency,account_reference",
            "b1,2026-04-02,2026-04-02,100.00,0.00,U1,settlement,INR,main",
        )
    return (
        "erp_gl_standard@1.0.0",
        "journal_id,line_number,posting_date,account_code,debit_amount,credit_amount,currency,"
        "external_reference,narration",
        "j1,1,2026-04-02,bank,100.00,0.00,INR,s1,debit\n"
        "j1,2,2026-04-02,clearing,0.00,100.00,INR,s1,credit",
    )


def _finance_projection(event: CanonicalEvent) -> tuple[object, ...]:
    return (
        event.source_record_id,
        event.source_type,
        event.event_type,
        event.money,
        event.direction,
        event.event_at,
        event.value_date,
        event.external_reference,
        event.settlement_reference,
        event.payment_reference,
        event.bank_utr,
        event.account_code,
        event.narration,
    )


def _csv(name: str, content: str) -> SourceDocument:
    return SourceDocument.from_bytes(
        file_id=name.removesuffix(".csv"),
        original_name=name,
        media_type="text/csv",
        content=content.encode(),
    )


def _xlsx(file_id: str, headers: list[str], row: list[object]) -> SourceDocument:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(headers)
    worksheet.append(row)
    buffer = BytesIO()
    workbook.save(buffer)
    workbook.close()
    return SourceDocument.from_bytes(
        file_id=file_id,
        original_name=f"{file_id}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        content=buffer.getvalue(),
    )
