from pathlib import Path

from scripts.generate_manufacturing_demos import PROFILES, build_profile, write_profile


def test_manufacturing_demo_profiles_are_distinct_complete_and_public(tmp_path: Path) -> None:
    expected_scenarios = {
        "aether-precision-components": {
            "many_payments_one_settlement",
            "incorrect_fee_or_tax",
        },
        "nexus-industrial-tools": {
            "partial_settlement",
            "working_day_shift",
            "missing_bank_credit",
        },
        "vanguard-specialty-chemicals": {
            "refund_later_settlement",
            "duplicate_erp_posting",
            "unbalanced_erp_journal",
            "orphan_bank_credit",
        },
    }
    assert len({profile.legal_entity_id for profile in PROFILES}) == 3
    assert len({profile.seed for profile in PROFILES}) == 3

    for profile in PROFILES:
        batch = build_profile(profile)
        manifest = write_profile(profile, batch, tmp_path)
        row_counts = manifest["row_counts"]
        assert isinstance(row_counts, dict)
        assert 80 <= row_counts["gateway"] <= 120
        assert row_counts["bank"] > 0
        assert row_counts["erp_gl"] > 0
        assert expected_scenarios[profile.slug] <= set(manifest["scenario_counts"])
        assert manifest["usage"]["contains_hidden_truth"] is False
        target = tmp_path / profile.slug
        assert not (target / "private").exists()
        assert (target / "inputs" / "gateway.csv").is_file()
        assert (target / "inputs" / "bank.csv").is_file()
        assert (target / "inputs" / "erp_gl.csv").is_file()
