"""Every production source adapter must pass the shared S3.1 contract."""

from pathlib import Path

import pytest

from core.vericlose.adapters import BankAdapter, ErpGlAdapter, GatewayAdapter
from core.vericlose.ingestion.contracts import NormalizationContext, SourceDocument
from core.vericlose.ingestion.mappings import FileMappingProfile, MappingCatalog
from tests.contract.source_adapter_contract import SourceAdapterContract

MAPPINGS = MappingCatalog.from_directory(Path("config/mappings"))


def _profile(versioned_id: str) -> FileMappingProfile:
    return MAPPINGS.get(versioned_id)


def _document(file_id: str, content: str) -> SourceDocument:
    return SourceDocument.from_bytes(
        file_id=file_id,
        original_name=f"{file_id}.csv",
        media_type="text/csv",
        content=content.encode(),
    )


class _ContextFixture:
    @pytest.fixture
    def normalization_context(self) -> NormalizationContext:
        return NormalizationContext("run-adapter-contract", "merchant-in")


class TestGatewayAdapter(_ContextFixture, SourceAdapterContract):
    @pytest.fixture
    def mapping_profile(self) -> FileMappingProfile:
        return _profile("gateway_standard@1.0.0")

    @pytest.fixture
    def adapter(self, mapping_profile: FileMappingProfile) -> GatewayAdapter:
        return GatewayAdapter((mapping_profile,))

    @pytest.fixture
    def valid_document(self) -> SourceDocument:
        return _document(
            "gateway-contract-valid",
            "gateway_event_id,event_type,transaction_id,settlement_id,amount_minor,currency,"
            "event_at,status,reference,narration\n"
            "gwe-1,PAYMENT,pay-1,set-1,10000,INR,2026-04-01T10:00:00+00:00,"
            "captured,order-1,Payment\n"
            "gwe-2,FEE,,set-1,200,INR,2026-04-01T10:00:00+00:00,processed,set-1,Fee\n",
        )

    @pytest.fixture
    def mixed_document(self) -> SourceDocument:
        return _document(
            "gateway-contract-mixed",
            "gateway_event_id,event_type,transaction_id,settlement_id,amount_minor,currency,"
            "event_at,status,reference,narration\n"
            "gwe-1,PAYMENT,pay-1,set-1,10000,INR,2026-04-01T10:00:00+00:00,"
            "captured,order-1,Payment\n"
            "gwe-2,UNKNOWN,,set-1,200,INR,2026-04-01T10:00:00+00:00,"
            "processed,set-1,Unknown\n",
        )


class TestBankAdapter(_ContextFixture, SourceAdapterContract):
    @pytest.fixture
    def mapping_profile(self) -> FileMappingProfile:
        return _profile("bank_debit_credit@1.0.0")

    @pytest.fixture
    def adapter(self, mapping_profile: FileMappingProfile) -> BankAdapter:
        return BankAdapter((mapping_profile,))

    @pytest.fixture
    def valid_document(self) -> SourceDocument:
        return _document(
            "bank-contract-valid",
            "bank_record_id,value_date,booking_date,credit_amount,debit_amount,utr,narration,"
            "currency,account_reference\n"
            "bank-1,2026-04-02,2026-04-02,100.00,0.00,UTR1,Credit,INR,bank-main\n"
            "bank-2,2026-04-03,2026-04-03,0.00,5.25,UTR2,Debit,INR,bank-main\n",
        )

    @pytest.fixture
    def mixed_document(self) -> SourceDocument:
        return _document(
            "bank-contract-mixed",
            "bank_record_id,value_date,booking_date,credit_amount,debit_amount,utr,narration,"
            "currency,account_reference\n"
            "bank-1,2026-04-02,2026-04-02,100.00,0.00,UTR1,Credit,INR,bank-main\n"
            "bank-2,2026-04-03,2026-04-03,5.00,5.00,UTR2,Both sides,INR,bank-main\n",
        )


class TestErpGlAdapter(_ContextFixture, SourceAdapterContract):
    @pytest.fixture
    def mapping_profile(self) -> FileMappingProfile:
        return _profile("erp_gl_standard@1.0.0")

    @pytest.fixture
    def adapter(self, mapping_profile: FileMappingProfile) -> ErpGlAdapter:
        return ErpGlAdapter((mapping_profile,))

    @pytest.fixture
    def valid_document(self) -> SourceDocument:
        return _document(
            "erp-contract-valid",
            "journal_id,line_number,posting_date,account_code,debit_amount,credit_amount,"
            "currency,external_reference,narration\n"
            "jrn-1,1,2026-04-02,bank,100.00,0.00,INR,set-1,Debit\n"
            "jrn-1,2,2026-04-02,clearing,0.00,100.00,INR,set-1,Credit\n",
        )

    @pytest.fixture
    def mixed_document(self) -> SourceDocument:
        return _document(
            "erp-contract-mixed",
            "journal_id,line_number,posting_date,account_code,debit_amount,credit_amount,"
            "currency,external_reference,narration\n"
            "jrn-1,1,2026-04-02,bank,100.00,0.00,INR,set-1,Debit\n"
            "jrn-1,2,2026-04-02,clearing,0.00,100.00,INR,set-1,Credit\n"
            "jrn-bad,1,2026-04-03,bank,50.00,10.00,INR,set-bad,Both sides\n",
        )
