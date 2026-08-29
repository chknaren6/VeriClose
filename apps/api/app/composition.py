from dataclasses import dataclass
from functools import partial
from pathlib import Path

from apps.api.app.settings import AppSettings, get_settings
from core.vericlose.adapters.bank import BankAdapter
from core.vericlose.adapters.erp_gl import ErpGlAdapter
from core.vericlose.adapters.gateway import GatewayAdapter
from core.vericlose.adapters.registry import AdapterRegistry
from core.vericlose.application.review_cases import PreliminaryReviewService, ReviewQueryService
from core.vericlose.application.run_reconciliation import RunReconciliationService
from core.vericlose.domain.enums import SourceType
from core.vericlose.infrastructure.duckdb import DuckDBUnitOfWork
from core.vericlose.infrastructure.local_file_store import LocalFileStore
from core.vericlose.ingestion.mappings import MappingCatalog
from core.vericlose.ingestion.service import ImportBatchService
from core.vericlose.reconciliation.policy import ReconciliationPolicy, load_policy


@dataclass(frozen=True, slots=True)
class AppContainer:
    """Single composition root for runtime dependencies."""

    settings: AppSettings
    mapping_catalog: MappingCatalog
    adapter_registry: AdapterRegistry
    reconciliation_policy: ReconciliationPolicy
    import_batch: ImportBatchService
    run_reconciliation: RunReconciliationService
    review_query: ReviewQueryService
    preliminary_review: PreliminaryReviewService


def build_container(settings: AppSettings | None = None) -> AppContainer:
    resolved = settings or get_settings()
    catalog = MappingCatalog.from_directory(Path("config/mappings"))
    policy = load_policy(resolved.policy_path)
    if resolved.policy_version != policy.versioned_id:
        raise ValueError(
            f"configured policy version {resolved.policy_version} does not match "
            f"{policy.versioned_id}"
        )
    registry = AdapterRegistry(
        (
            GatewayAdapter(catalog.for_source(SourceType.GATEWAY)),
            BankAdapter(catalog.for_source(SourceType.BANK)),
            ErpGlAdapter(catalog.for_source(SourceType.ERP)),
        )
    )
    file_store = LocalFileStore(resolved.data_dir)
    unit_of_work = partial(DuckDBUnitOfWork, resolved.database_path)
    import_service = ImportBatchService(
        registry,
        file_store,
        unit_of_work,
    )
    reconciliation_service = RunReconciliationService(policy, unit_of_work)
    review_query = ReviewQueryService(unit_of_work)
    preliminary_review = PreliminaryReviewService(review_query, unit_of_work)
    return AppContainer(
        resolved,
        catalog,
        registry,
        policy,
        import_service,
        reconciliation_service,
        review_query,
        preliminary_review,
    )
