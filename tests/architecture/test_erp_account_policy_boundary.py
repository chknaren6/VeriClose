"""ERP ingestion preserves account codes but never assigns business roles itself."""

from pathlib import Path


def test_erp_adapter_contains_no_demo_or_client_account_code_roles() -> None:
    source = Path("core/vericlose/adapters/erp_gl.py").read_text(encoding="utf-8")
    hardcoded_demo_accounts = {"110000", "120000", "140000", "510000"}
    assert not hardcoded_demo_accounts.intersection(source.split())
