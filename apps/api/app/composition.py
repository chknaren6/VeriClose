from dataclasses import dataclass
from functools import partial
from pathlib import Path

from apps.api.app.settings import AppSettings, get_settings
from core.vericlose.adapters.bank import BankAdapter
from core.vericlose.adapters.erp_gl import ErpGlAdapter
from core.vericlose.adapters.gateway import GatewayAdapter
from core.vericlose.adapters.registry import AdapterRegistry
from core.vericlose.domain.enums import SourceType
from core.vericlose.infrastructure.duckdb import DuckDBUnitOfWork
from core.vericlose.infrastructure.local_file_store import LocalFileStore
from core.vericlose.ingestion.mappings import MappingCatalog
from core.vericlose.ingestion.service import ImportBatchService


@dataclass(frozen=True, slots=True)
class AppContainer:
    """Single composition root for runtime dependencies."""

    settings: AppSettings
    mapping_catalog: MappingCatalog
    adapter_registry: AdapterRegistry
    import_batch: ImportBatchService


def build_container(settings: AppSettings | None = None) -> AppContainer:
    resolved = settings or get_settings()
    catalog = MappingCatalog.from_directory(Path("config/mappings"))
    registry = AdapterRegistry(
        (
            GatewayAdapter(catalog.for_source(SourceType.GATEWAY)),
            BankAdapter(catalog.for_source(SourceType.BANK)),
            ErpGlAdapter(catalog.for_source(SourceType.ERP)),
        )
    )
    file_store = LocalFileStore(resolved.data_dir)
    import_service = ImportBatchService(
        registry,
        file_store,
        partial(DuckDBUnitOfWork, resolved.database_path),
    )
    return AppContainer(resolved, catalog, registry, import_service)
