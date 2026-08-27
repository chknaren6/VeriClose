"""CLI for a reproducible gateway → bank → ERP batch and isolated truth labels."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from synthetic.base_case import SyntheticConfig, generate_clean_batch, seeded_rng
from synthetic.models import GeneratedBatch
from synthetic.scenarios.injectors import (
    ANOMALY_INJECTORS,
    inject_orphan_bank_credit,
    inject_partial_settlement,
    inject_refund_in_later_settlement,
    inject_working_day_shift,
    mark_many_payments_one_settlement,
)

GATEWAY_FIELDS = (
    "gateway_event_id",
    "event_type",
    "transaction_id",
    "settlement_id",
    "amount_minor",
    "currency",
    "event_at",
    "status",
    "reference",
    "narration",
)
BANK_FIELDS = (
    "bank_record_id",
    "value_date",
    "booking_date",
    "credit_amount",
    "debit_amount",
    "utr",
    "narration",
    "currency",
    "account_reference",
)
ERP_FIELDS = (
    "journal_id",
    "line_number",
    "posting_date",
    "account_code",
    "debit_amount",
    "credit_amount",
    "currency",
    "external_reference",
    "narration",
)


def build_synthetic_batch(config: SyntheticConfig) -> GeneratedBatch:
    """Create a clean world, then apply isolated valid and anomalous scenarios."""

    batch = generate_clean_batch(config)
    target_ids = [context.case_id for context in batch.cases]

    # Valid complexity belongs in the truth set too; these must not be labelled errors.
    batch = mark_many_payments_one_settlement(batch, target_ids[0])
    batch = inject_partial_settlement(batch, target_ids[1])
    batch = inject_refund_in_later_settlement(batch, target_ids[2])
    batch = inject_working_day_shift(batch, target_ids[3])

    anomaly_count = min(
        round(config.settlements * config.exception_rate),
        config.settlements - 4,
    )
    if anomaly_count == 0:
        return batch

    # The orphan has no original settlement target; count it as one anomalous case.
    batch = inject_orphan_bank_credit(batch, ordinal=1)
    remaining_count = anomaly_count - 1
    available_targets = target_ids[4:]
    placement_rng = seeded_rng(config.seed, "scenario-placement")
    placement_rng.shuffle(available_targets)
    injectors = list(ANOMALY_INJECTORS)
    placement_rng.shuffle(injectors)

    for index in range(remaining_count):
        injector = injectors[index % len(injectors)]
        batch = injector(batch, available_targets[index])
    return batch


def write_batch(batch: GeneratedBatch, config: SyntheticConfig, output_dir: Path) -> dict[str, Any]:
    """Write only fixed, run-scoped filenames; no source path is ever accepted from data."""

    input_dir = output_dir / "inputs"
    private_dir = output_dir / "private"
    input_dir.mkdir(parents=True, exist_ok=True)
    private_dir.mkdir(parents=True, exist_ok=True)

    gateway_path = input_dir / "gateway.csv"
    bank_path = input_dir / "bank.csv"
    erp_path = input_dir / "erp_gl.csv"
    truth_path = private_dir / "ground_truth.json"
    manifest_path = output_dir / "manifest.json"

    _write_csv(gateway_path, GATEWAY_FIELDS, [row.to_csv_row() for row in batch.gateway_rows])
    _write_csv(bank_path, BANK_FIELDS, [row.to_csv_row() for row in batch.bank_rows])
    _write_csv(erp_path, ERP_FIELDS, [row.to_csv_row() for row in batch.erp_rows])
    _write_json(truth_path, batch.truth.to_dict())

    scenario_counts = Counter(case.scenario for case in batch.truth.case_labels)
    manifest: dict[str, Any] = {
        "schema_version": "1.0",
        "generator_version": "segment-2-v1",
        "seed": config.seed,
        "parameters": {
            "payments": config.payments,
            "settlements": config.settlements,
            "exception_rate": config.exception_rate,
        },
        "scenario_counts": dict(sorted(scenario_counts.items())),
        "control_totals": batch.control_totals(),
        "files": {
            "gateway": _file_manifest(gateway_path, output_dir),
            "bank": _file_manifest(bank_path, output_dir),
            "erp_gl": _file_manifest(erp_path, output_dir),
            "ground_truth": _file_manifest(truth_path, output_dir),
        },
        "truth_is_private": True,
    }
    _write_json(manifest_path, manifest)
    return manifest


def generate(config: SyntheticConfig, output_dir: Path) -> dict[str, Any]:
    batch = build_synthetic_batch(config)
    return write_batch(batch, config, output_dir)


def _write_csv(
    path: Path,
    fieldnames: tuple[str, ...],
    rows: list[dict[str, str | int]],
) -> None:
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _file_manifest(path: Path, root: Path) -> dict[str, str | int]:
    content = path.read_bytes()
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": hashlib.sha256(content).hexdigest(),
        "size_bytes": len(content),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--payments", type=int, default=120)
    parser.add_argument("--settlements", type=int, default=24)
    parser.add_argument("--exception-rate", type=float, default=0.40)
    parser.add_argument("--output", type=Path, default=Path(".data/synthetic/seed-42"))
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    config = SyntheticConfig(
        seed=args.seed,
        payments=args.payments,
        settlements=args.settlements,
        exception_rate=args.exception_rate,
    )
    manifest = generate(config, args.output)
    summary = {
        "status": "generated",
        "output": str(args.output),
        "seed": config.seed,
        "row_counts": manifest["control_totals"]["row_counts"],
        "scenario_counts": manifest["scenario_counts"],
    }
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
