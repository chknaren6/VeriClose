"""Import and deterministically reconcile one complete synthetic finance batch."""

from __future__ import annotations

import argparse
import json
import mimetypes
from dataclasses import asdict
from functools import partial
from pathlib import Path
from uuid import uuid4

from core.vericlose.adapters import AdapterRegistry, BankAdapter, ErpGlAdapter, GatewayAdapter
from core.vericlose.application.run_reconciliation import RunReconciliationService
from core.vericlose.domain.enums import SourceType
from core.vericlose.infrastructure.duckdb import DuckDBUnitOfWork
from core.vericlose.infrastructure.local_file_store import LocalFileStore
from core.vericlose.ingestion.contracts import NormalizationContext, SourceDocument
from core.vericlose.ingestion.mappings import MappingCatalog
from core.vericlose.ingestion.service import ImportBatchService
from core.vericlose.reconciliation.policy import load_policy
from core.vericlose.reconciliation.rules.settlement import RULE_VERSION
from synthetic.base_case import SyntheticConfig
from synthetic.generate import generate


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gateway", type=Path)
    parser.add_argument("--bank", type=Path)
    parser.add_argument("--erp", type=Path)
    parser.add_argument(
        "--generate-demo",
        action="store_true",
        help="Generate the seeded synthetic inputs inside data-dir before closing them",
    )
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--legal-entity", default="demo-merchant-in")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--payments", type=int, default=120)
    parser.add_argument("--settlements", type=int, default=24)
    parser.add_argument("--exception-rate", type=float, default=0.40)
    parser.add_argument("--data-dir", type=Path, default=Path(".data/imports"))
    parser.add_argument("--database", type=Path, default=Path(".data/vericlose.duckdb"))
    parser.add_argument("--mapping-dir", type=Path, default=Path("config/mappings"))
    parser.add_argument(
        "--policy", type=Path, default=Path("config/policies/razorpay_inr_v1.yaml")
    )
    parser.add_argument(
        "--exceptions-output", type=Path, default=Path(".data/exceptions.json")
    )
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    run_id = args.run_id or f"run-{uuid4().hex}"
    gateway_path, bank_path, erp_path = _source_paths(args, run_id)
    policy = load_policy(args.policy)
    catalog = MappingCatalog.from_directory(args.mapping_dir)
    registry = AdapterRegistry(
        (
            GatewayAdapter(catalog.for_source(SourceType.GATEWAY)),
            BankAdapter(catalog.for_source(SourceType.BANK)),
            ErpGlAdapter(catalog.for_source(SourceType.ERP)),
        )
    )
    unit_of_work = partial(DuckDBUnitOfWork, args.database)
    importer = ImportBatchService(registry, LocalFileStore(args.data_dir), unit_of_work)
    imported = importer.import_batch(
        run_id=run_id,
        documents=tuple(
            _document(file_id, path)
            for file_id, path in (
                ("gateway", gateway_path),
                ("bank", bank_path),
                ("erp", erp_path),
            )
        ),
        context=NormalizationContext(run_id, args.legal_entity),
        policy_version=policy.versioned_id,
        rule_version=RULE_VERSION,
        seed=args.seed,
    )
    if not imported.is_ready:
        print(json.dumps({"run_id": run_id, "state": imported.manifest.state.value}))
        return 2
    result = RunReconciliationService(policy, unit_of_work).run(run_id)
    exception_payload = [asdict(item) for item in result.kernel.exceptions]
    args.exceptions_output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.exceptions_output.with_suffix(f"{args.exceptions_output.suffix}.tmp")
    temporary.write_text(
        json.dumps(exception_payload, default=_json_default, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(args.exceptions_output)
    summary = {
        "run_id": run_id,
        "state": result.manifest.state.value,
        "source_event_count": len(imported.events),
        "decision_count": result.summary.decision_count,
        "auto_cleared_count": result.summary.auto_cleared_count,
        "operational_verification_rate_bps": (
            result.summary.auto_cleared_count * 10_000 // result.summary.decision_count
        ),
        "exception_count": result.summary.exception_count,
        "amount_at_risk_minor": result.summary.amount_at_risk_minor,
        "proof_levels": {
            level: sum(decision.proof_level.value == level for decision in result.kernel.decisions)
            for level in ("PROVED", "SUPPORTED", "AMBIGUOUS", "CONTRADICTED", "INVALID_INPUT")
        },
        "exception_file": str(args.exceptions_output),
        "stage_timings": [asdict(item) for item in result.kernel.timings],
    }
    print(json.dumps(summary, sort_keys=True))
    return 0


def _document(file_id: str, path: Path) -> SourceDocument:
    return SourceDocument.from_bytes(
        file_id=file_id,
        original_name=path.name,
        media_type=mimetypes.guess_type(path.name)[0] or "application/octet-stream",
        content=path.read_bytes(),
    )


def _source_paths(args: argparse.Namespace, run_id: str) -> tuple[Path, Path, Path]:
    supplied = (args.gateway, args.bank, args.erp)
    if args.generate_demo:
        if any(path is not None for path in supplied):
            raise ValueError("--generate-demo cannot be combined with source-file arguments")
        generated = args.data_dir / "synthetic" / run_id
        generate(
            SyntheticConfig(
                seed=args.seed,
                payments=args.payments,
                settlements=args.settlements,
                exception_rate=args.exception_rate,
            ),
            generated,
        )
        inputs = generated / "inputs"
        return inputs / "gateway.csv", inputs / "bank.csv", inputs / "erp_gl.csv"
    if any(path is None for path in supplied):
        raise ValueError("--gateway, --bank, and --erp are required without --generate-demo")
    return supplied


def _json_default(value: object) -> object:
    return value.value if hasattr(value, "value") else str(value)


if __name__ == "__main__":
    raise SystemExit(main())
