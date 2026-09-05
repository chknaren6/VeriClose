"""Generate reproducible, public-only manufacturing demo packs for VeriClose."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from synthetic.base_case import SyntheticConfig, generate_clean_batch
from synthetic.generate import BANK_FIELDS, ERP_FIELDS, GATEWAY_FIELDS
from synthetic.models import GeneratedBatch
from synthetic.scenarios.injectors import (
    inject_duplicate_erp_posting,
    inject_incorrect_fee_or_tax,
    inject_missing_bank_credit,
    inject_orphan_bank_credit,
    inject_partial_settlement,
    inject_refund_in_later_settlement,
    inject_unbalanced_erp_journal,
    inject_working_day_shift,
    mark_many_payments_one_settlement,
)

Transform = Callable[[GeneratedBatch], GeneratedBatch]


@dataclass(frozen=True, slots=True)
class ManufacturingDemoProfile:
    slug: str
    legal_entity_name: str
    legal_entity_id: str
    seed: int
    payments: int
    settlements: int
    exception_profile: tuple[str, ...]
    transform: Transform


def _aether(batch: GeneratedBatch) -> GeneratedBatch:
    case_ids = [item.case_id for item in batch.cases]
    for case_id in case_ids[:3]:
        batch = mark_many_payments_one_settlement(batch, case_id)
    for case_id in case_ids[3:6]:
        batch = inject_incorrect_fee_or_tax(batch, case_id)
    return batch


def _nexus(batch: GeneratedBatch) -> GeneratedBatch:
    case_ids = [item.case_id for item in batch.cases]
    for case_id in case_ids[:2]:
        batch = inject_partial_settlement(batch, case_id)
    for case_id in case_ids[2:4]:
        batch = inject_working_day_shift(batch, case_id)
    for case_id in case_ids[4:7]:
        batch = inject_missing_bank_credit(batch, case_id)
    return batch


def _vanguard(batch: GeneratedBatch) -> GeneratedBatch:
    case_ids = [item.case_id for item in batch.cases]
    for case_id in case_ids[:2]:
        batch = inject_refund_in_later_settlement(batch, case_id)
    for case_id in case_ids[2:4]:
        batch = inject_duplicate_erp_posting(batch, case_id)
    batch = inject_unbalanced_erp_journal(batch, case_ids[4])
    return inject_orphan_bank_credit(batch, ordinal=1)


PROFILES = (
    ManufacturingDemoProfile(
        slug="aether-precision-components",
        legal_entity_name="Aether Precision Components Private Limited",
        legal_entity_id="le_aether_precision_in",
        seed=1042,
        payments=60,
        settlements=14,
        exception_profile=(
            "fee and GST component mismatches",
            "many gateway payments aggregated into one settlement",
        ),
        transform=_aether,
    ),
    ManufacturingDemoProfile(
        slug="nexus-industrial-tools",
        legal_entity_name="Nexus Industrial Tools Private Limited",
        legal_entity_id="le_nexus_tools_in",
        seed=2042,
        payments=62,
        settlements=14,
        exception_profile=(
            "partial settlement receipts",
            "valid working-day timing differences",
            "missing bank receipts",
        ),
        transform=_nexus,
    ),
    ManufacturingDemoProfile(
        slug="vanguard-specialty-chemicals",
        legal_entity_name="Vanguard Specialty Chemicals Private Limited",
        legal_entity_id="le_vanguard_chemicals_in",
        seed=3042,
        payments=58,
        settlements=14,
        exception_profile=(
            "refunds deducted in later settlements",
            "duplicate ERP postings",
            "one unbalanced ERP journal",
            "one orphan bank credit",
        ),
        transform=_vanguard,
    ),
)


def build_profile(profile: ManufacturingDemoProfile) -> GeneratedBatch:
    config = SyntheticConfig(
        seed=profile.seed,
        payments=profile.payments,
        settlements=profile.settlements,
        exception_rate=0,
    )
    return profile.transform(generate_clean_batch(config))


def write_profile(
    profile: ManufacturingDemoProfile,
    batch: GeneratedBatch,
    output_root: Path,
) -> dict[str, object]:
    target = output_root / profile.slug
    input_dir = target / "inputs"
    input_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "gateway": input_dir / "gateway.csv",
        "bank": input_dir / "bank.csv",
        "erp_gl": input_dir / "erp_gl.csv",
    }
    _write_csv(paths["gateway"], GATEWAY_FIELDS, [row.to_csv_row() for row in batch.gateway_rows])
    _write_csv(paths["bank"], BANK_FIELDS, [row.to_csv_row() for row in batch.bank_rows])
    _write_csv(paths["erp_gl"], ERP_FIELDS, [row.to_csv_row() for row in batch.erp_rows])

    scenario_counts = Counter(item.scenario for item in batch.truth.case_labels)
    manifest: dict[str, object] = {
        "schema_version": "1.0",
        "dataset_kind": "synthetic_manufacturing_demo",
        "synthetic_data_only": True,
        "legal_entity": {
            "name": profile.legal_entity_name,
            "legal_entity_id": profile.legal_entity_id,
            "currency": "INR",
        },
        "generator": {
            "seed": profile.seed,
            "payments": profile.payments,
            "settlements": profile.settlements,
        },
        "exception_profile": list(profile.exception_profile),
        "scenario_counts": dict(sorted(scenario_counts.items())),
        "row_counts": {
            "gateway": len(batch.gateway_rows),
            "bank": len(batch.bank_rows),
            "erp_gl": len(batch.erp_rows),
            "total": len(batch.gateway_rows) + len(batch.bank_rows) + len(batch.erp_rows),
        },
        "files": {
            name: {
                "path": path.relative_to(target).as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "size_bytes": path.stat().st_size,
            }
            for name, path in paths.items()
        },
        "usage": {
            "upload_order": ["gateway", "bank", "erp_gl"],
            "restore_demo_fixture_dir": input_dir.as_posix(),
            "contains_hidden_truth": False,
        },
    }
    (target / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def generate_all(output_root: Path = Path("demo/manufacturing")) -> list[dict[str, object]]:
    return [write_profile(profile, build_profile(profile), output_root) for profile in PROFILES]


def _write_csv(
    path: Path,
    fieldnames: tuple[str, ...],
    rows: list[dict[str, str | int]],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    manifests = generate_all()
    print(
        json.dumps(
            [
                {
                    "legal_entity": item["legal_entity"],
                    "row_counts": item["row_counts"],
                    "scenario_counts": item["scenario_counts"],
                }
                for item in manifests
            ],
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
