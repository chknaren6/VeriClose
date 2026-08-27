from pathlib import Path

import pytest

from core.vericlose.adapters import AdapterRegistry, BankAdapter, ErpGlAdapter, GatewayAdapter
from core.vericlose.adapters.registry import AmbiguousDetectionError
from core.vericlose.domain.enums import SourceType
from core.vericlose.ingestion.contracts import SourceDocument
from core.vericlose.ingestion.mappings import (
    FieldMapping,
    MappingCatalog,
    MappingConfigurationError,
    parse_decimal_minor,
)


@pytest.fixture(scope="module")
def catalog() -> MappingCatalog:
    return MappingCatalog.from_directory(Path("config/mappings"))


@pytest.fixture
def registry(catalog: MappingCatalog) -> AdapterRegistry:
    return AdapterRegistry(
        (
            GatewayAdapter(catalog.for_source(SourceType.GATEWAY)),
            BankAdapter(catalog.for_source(SourceType.BANK)),
            ErpGlAdapter(catalog.for_source(SourceType.ERP)),
        )
    )


def _document(content: str) -> SourceDocument:
    return SourceDocument.from_bytes(
        file_id="detect-file",
        original_name="input.csv",
        media_type="text/csv",
        content=content.encode(),
    )


def test_catalog_loads_versioned_profiles_and_safe_transforms(catalog: MappingCatalog) -> None:
    assert catalog.get("gateway_standard@1.0.0").ref.source_type is SourceType.GATEWAY
    assert len(catalog.for_source(SourceType.BANK)) == 3

    with pytest.raises(MappingConfigurationError, match="unsafe transform"):
        FieldMapping("amount_minor", ("amount",), True, "eval")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("121.05", 12_105), ("-25.00", -2_500), ("1,200.10", 120_010)],
)
def test_decimal_money_is_exact(raw: str, expected: int) -> None:
    assert parse_decimal_minor(raw) == expected


@pytest.mark.parametrize("raw", ["100.001", "NaN", "Infinity", "not-money"])
def test_decimal_money_rejects_unsafe_values(raw: str) -> None:
    with pytest.raises(ValueError):
        parse_decimal_minor(raw)


def test_registry_auto_selects_unique_layout(registry: AdapterRegistry) -> None:
    document = _document(
        "gateway_event_id,event_type,transaction_id,settlement_id,amount_minor,currency,"
        "event_at,status,reference,narration\n"
        "g1,PAYMENT,p1,s1,100,INR,2026-04-01T00:00:00+00:00,captured,o1,payment\n"
    )
    selected = registry.select(document)
    assert selected.adapter.source_type is SourceType.GATEWAY
    assert selected.mapping_profile.ref.versioned_id == "gateway_standard@1.0.0"
    assert not selected.explicitly_confirmed


def test_registry_requires_confirmation_when_two_profiles_fit(
    registry: AdapterRegistry,
) -> None:
    document = _document(
        "bank_record_id,value_date,booking_date,credit_amount,debit_amount,signed_amount,"
        "utr,narration,currency,account_reference\n"
        "b1,2026-04-01,2026-04-01,100.00,0.00,100.00,U1,Credit,INR,main\n"
    )
    assert registry.detect(document).requires_confirmation
    with pytest.raises(AmbiguousDetectionError):
        registry.select(document)

    selected = registry.select(
        document,
        confirmed_adapter_id="generic-bank-statement",
        confirmed_profile_versioned_id="bank_debit_credit@1.0.0",
    )
    assert selected.explicitly_confirmed
