"""Import gateway, bank, and ERP source files through the complete M1 pipeline."""

from __future__ import annotations

import argparse
import json
import mimetypes
from functools import partial
from pathlib import Path
from uuid import uuid4

from core.vericlose.adapters import AdapterRegistry, BankAdapter, ErpGlAdapter, GatewayAdapter
from core.vericlose.domain.enums import SourceType
from core.vericlose.infrastructure.duckdb import DuckDBUnitOfWork
from core.vericlose.infrastructure.local_file_store import LocalFileStore
from core.vericlose.ingestion.contracts import NormalizationContext, SourceDocument
from core.vericlose.ingestion.mappings import MappingCatalog
from core.vericlose.ingestion.service import ImportBatchService


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gateway", type=Path, required=True)
    parser.add_argument("--bank", type=Path, required=True)
    parser.add_argument("--erp", type=Path, required=True)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--legal-entity", default="demo-merchant-in")
    parser.add_argument("--data-dir", type=Path, default=Path(".data/imports"))
    parser.add_argument("--database", type=Path, default=Path(".data/vericlose.duckdb"))
    parser.add_argument("--mapping-dir", type=Path, default=Path("config/mappings"))
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    run_id = args.run_id or f"run-{uuid4().hex}"
    catalog = MappingCatalog.from_directory(args.mapping_dir)
    registry = AdapterRegistry(
        (
            GatewayAdapter(catalog.for_source(SourceType.GATEWAY)),
            BankAdapter(catalog.for_source(SourceType.BANK)),
            ErpGlAdapter(catalog.for_source(SourceType.ERP)),
        )
    )
    service = ImportBatchService(
        registry,
        LocalFileStore(args.data_dir),
        partial(DuckDBUnitOfWork, args.database),
    )
    documents = tuple(
        _document(file_id, path)
        for file_id, path in (
            ("gateway", args.gateway),
            ("bank", args.bank),
            ("erp", args.erp),
        )
    )
    result = service.import_batch(
        run_id=run_id,
        documents=documents,
        context=NormalizationContext(run_id, args.legal_entity),
        policy_version="razorpay_inr_v1@1.0.0",
        rule_version="segment4-v1",
    )
    payload = {
        "run_id": result.manifest.run_id,
        "state": result.manifest.state.value,
        "event_count": len(result.events),
        "mapping_versions": dict(result.manifest.mapping_versions),
        "files": [
            {
                "file_id": item.document.file_id,
                "source_type": item.selected.adapter.source_type.value,
                "rows_seen": item.validation.rows_seen,
                "normalized_rows": (
                    item.normalization.normalized_row_count if item.normalization else 0
                ),
                "quarantined_rows": (
                    item.normalization.quarantined_row_count if item.normalization else 0
                ),
                "issue_count": len(item.validation.issues),
                "issues": sorted({issue.code for issue in item.validation.issues}),
            }
            for item in result.files
        ],
        "cross_source_issues": [issue.code for issue in result.cross_source.issues],
    }
    print(json.dumps(payload, sort_keys=True))
    return 0 if result.is_ready else 2


def _document(file_id: str, path: Path) -> SourceDocument:
    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return SourceDocument.from_bytes(
        file_id=file_id,
        original_name=path.name,
        media_type=media_type,
        content=path.read_bytes(),
    )


if __name__ == "__main__":
    raise SystemExit(main())
