"""Multi-seed synthetic benchmark with safety-threshold enforcement."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from enum import Enum
from functools import partial
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter_ns

import yaml

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
from evaluation.evaluate import EvaluationReport, evaluate_stored_run
from evaluation.metrics import EvaluationMetrics, MetricCounts
from synthetic.base_case import SyntheticConfig
from synthetic.generate import generate


@dataclass(frozen=True, slots=True)
class DatasetConfig:
    payments: int
    settlements: int
    exception_rate_bps: int


@dataclass(frozen=True, slots=True)
class SafetyThresholds:
    minimum_auto_clear_precision_bps: int
    minimum_exception_recall_bps: int
    maximum_false_clear_count: int
    maximum_false_clear_rate_bps: int


@dataclass(frozen=True, slots=True)
class BenchmarkConfig:
    profile_id: str
    development_seeds: tuple[int, ...]
    submission_seeds: tuple[int, ...]
    dataset: DatasetConfig
    thresholds: SafetyThresholds


@dataclass(frozen=True, slots=True)
class SeedBenchmark:
    seed: int
    source_event_count: int
    decision_count: int
    scenario_mix: tuple[tuple[str, int], ...]
    end_to_end_runtime_ms: int
    reconciliation_runtime_ms: int
    throughput_events_per_second: int
    evaluation: EvaluationReport


@dataclass(frozen=True, slots=True)
class BenchmarkReport:
    profile_id: str
    generated_at: datetime
    seeds: tuple[int, ...]
    dataset: DatasetConfig
    thresholds: SafetyThresholds
    aggregate_metrics: EvaluationMetrics
    seed_results: tuple[SeedBenchmark, ...]
    runtime_p50_ms: int
    runtime_p95_ms: int
    throughput_p50_events_per_second: int
    throughput_p95_events_per_second: int
    threshold_passed: bool
    threshold_violations: tuple[str, ...]


def load_benchmark_config(path: Path) -> BenchmarkConfig:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != "1.0":
        raise ValueError("benchmark config requires schema_version 1.0")
    dataset = _integer_mapping(payload.get("dataset"), "dataset")
    thresholds = _integer_mapping(payload.get("thresholds"), "thresholds")
    development = _seeds(payload.get("development_seeds"), "development_seeds", minimum=5)
    submission = _seeds(payload.get("submission_seeds"), "submission_seeds", minimum=10)
    return BenchmarkConfig(
        str(payload["profile_id"]),
        development,
        submission,
        DatasetConfig(
            dataset["payments"],
            dataset["settlements"],
            dataset["exception_rate_bps"],
        ),
        SafetyThresholds(
            thresholds["minimum_auto_clear_precision_bps"],
            thresholds["minimum_exception_recall_bps"],
            thresholds["maximum_false_clear_count"],
            thresholds["maximum_false_clear_rate_bps"],
        ),
    )


def run_benchmark(
    config: BenchmarkConfig,
    *,
    seeds: tuple[int, ...] | None = None,
    generated_at: datetime | None = None,
) -> BenchmarkReport:
    selected_seeds = seeds or config.development_seeds
    if not selected_seeds or len(set(selected_seeds)) != len(selected_seeds):
        raise ValueError("benchmark seeds must be non-empty and unique")
    seed_results = tuple(_run_seed(seed, config.dataset) for seed in selected_seeds)
    counts = sum(
        (item.evaluation.metrics.counts for item in seed_results),
        start=MetricCounts(),
    )
    metrics = EvaluationMetrics.from_counts(counts)
    violations = evaluate_thresholds(metrics, config.thresholds)
    runtimes = tuple(item.end_to_end_runtime_ms for item in seed_results)
    throughputs = tuple(item.throughput_events_per_second for item in seed_results)
    return BenchmarkReport(
        config.profile_id,
        generated_at or datetime.now(UTC),
        selected_seeds,
        config.dataset,
        config.thresholds,
        metrics,
        seed_results,
        _percentile(runtimes, 50),
        _percentile(runtimes, 95),
        _percentile(throughputs, 50),
        _percentile(throughputs, 95),
        not violations,
        violations,
    )


def evaluate_thresholds(
    metrics: EvaluationMetrics, thresholds: SafetyThresholds
) -> tuple[str, ...]:
    violations: list[str] = []
    if metrics.auto_clear_precision_bps < thresholds.minimum_auto_clear_precision_bps:
        violations.append(
            "AUTO_CLEAR_PRECISION_BELOW_MINIMUM: "
            f"observed={metrics.auto_clear_precision_bps}, "
            f"required={thresholds.minimum_auto_clear_precision_bps}"
        )
    if metrics.exception_recall_bps < thresholds.minimum_exception_recall_bps:
        violations.append(
            "EXCEPTION_RECALL_BELOW_MINIMUM: "
            f"observed={metrics.exception_recall_bps}, "
            f"required={thresholds.minimum_exception_recall_bps}"
        )
    if metrics.counts.false_clear_count > thresholds.maximum_false_clear_count:
        violations.append(
            "FALSE_CLEAR_COUNT_ABOVE_MAXIMUM: "
            f"observed={metrics.counts.false_clear_count}, "
            f"allowed={thresholds.maximum_false_clear_count}"
        )
    if metrics.false_clear_rate_bps > thresholds.maximum_false_clear_rate_bps:
        violations.append(
            "FALSE_CLEAR_RATE_ABOVE_MAXIMUM: "
            f"observed={metrics.false_clear_rate_bps}, "
            f"allowed={thresholds.maximum_false_clear_rate_bps}"
        )
    return tuple(violations)


def write_reports(report: BenchmarkReport, output_prefix: Path) -> tuple[Path, Path]:
    json_path = output_prefix.with_suffix(".json")
    markdown_path = output_prefix.with_suffix(".md")
    json_payload = (
        json.dumps(asdict(report), default=_json_default, indent=2, sort_keys=True) + "\n"
    )
    markdown_payload = _markdown(report)
    for path, content in ((json_path, json_payload), (markdown_path, markdown_payload)):
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(f"{path.suffix}.tmp")
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(path)
    return json_path, markdown_path


def _run_seed(seed: int, dataset: DatasetConfig) -> SeedBenchmark:
    with TemporaryDirectory(prefix=f"vericlose-benchmark-{seed}-") as raw_root:
        root = Path(raw_root)
        generated = root / "generated"
        started = perf_counter_ns()
        generate(
            SyntheticConfig(
                seed=seed,
                payments=dataset.payments,
                settlements=dataset.settlements,
                exception_rate=dataset.exception_rate_bps / 10_000,
            ),
            generated,
        )
        database = root / "benchmark.duckdb"
        unit_of_work = partial(DuckDBUnitOfWork, database)
        policy = load_policy(Path("config/policies/razorpay_inr_v1.yaml"))
        importer = ImportBatchService(_registry(), LocalFileStore(root / "files"), unit_of_work)
        run_id = f"benchmark-seed-{seed}"
        imported = importer.import_batch(
            run_id=run_id,
            documents=_documents(generated / "inputs"),
            context=NormalizationContext(run_id, "demo-merchant-in"),
            policy_version=policy.versioned_id,
            rule_version=RULE_VERSION,
            seed=seed,
        )
        reconciled = RunReconciliationService(policy, unit_of_work).run(run_id)
        end_to_end_ms = max(1, (perf_counter_ns() - started) // 1_000_000)
        evaluation = evaluate_stored_run(
            database, run_id, generated / "private" / "ground_truth.json"
        )
        scenario_mix = tuple(
            sorted(Counter(item.scenario for item in evaluation.case_results).items())
        )
        reconciliation_ms = sum(item.duration_ms for item in reconciled.kernel.timings)
        event_count = len(imported.events)
        return SeedBenchmark(
            seed,
            event_count,
            len(reconciled.kernel.decisions),
            scenario_mix,
            end_to_end_ms,
            reconciliation_ms,
            event_count * 1_000 // end_to_end_ms,
            evaluation,
        )


def _registry() -> AdapterRegistry:
    catalog = MappingCatalog.from_directory(Path("config/mappings"))
    return AdapterRegistry(
        (
            GatewayAdapter(catalog.for_source(SourceType.GATEWAY)),
            BankAdapter(catalog.for_source(SourceType.BANK)),
            ErpGlAdapter(catalog.for_source(SourceType.ERP)),
        )
    )


def _documents(input_dir: Path) -> tuple[SourceDocument, ...]:
    return tuple(
        SourceDocument.from_bytes(
            file_id=file_id,
            original_name=filename,
            media_type="text/csv",
            content=(input_dir / filename).read_bytes(),
        )
        for file_id, filename in (
            ("gateway", "gateway.csv"),
            ("bank", "bank.csv"),
            ("erp", "erp_gl.csv"),
        )
    )


def _percentile(values: tuple[int, ...], percentile: int) -> int:
    if not values or not 0 < percentile <= 100:
        raise ValueError("percentile requires values and a percentile in 1..100")
    ordered = sorted(values)
    return ordered[math.ceil(percentile * len(ordered) / 100) - 1]


def _markdown(report: BenchmarkReport) -> str:
    status = "PASS" if report.threshold_passed else "FAIL"
    counts = report.aggregate_metrics.counts
    metrics = report.aggregate_metrics
    lines = [
        "# VeriClose benchmark report",
        "",
        f"- Status: **{status}**",
        f"- Profile: `{report.profile_id}`",
        f"- Seeds: `{', '.join(str(seed) for seed in report.seeds)}`",
        f"- Generated: `{report.generated_at.isoformat()}`",
        "",
        "## Aggregate safety metrics",
        "",
        "| Metric | Result | Denominator |",
        "|---|---:|---:|",
        f"| Event accuracy | {metrics.event_accuracy_bps / 100:.2f}% | "
        f"{counts.truth_event_count} |",
        f"| Case accuracy | {metrics.case_accuracy_bps / 100:.2f}% | "
        f"{counts.truth_case_count} |",
        f"| Auto-clear precision | {metrics.auto_clear_precision_bps / 100:.2f}% | "
        f"{counts.predicted_auto_clear_count} auto-clears |",
        f"| Exception recall | {metrics.exception_recall_bps / 100:.2f}% | "
        f"{counts.expected_exception_count} expected exceptions |",
        f"| False-clear rate | {metrics.false_clear_rate_bps / 100:.2f}% | "
        f"{counts.predicted_auto_clear_count} auto-clears |",
        f"| False-clear count | {counts.false_clear_count} | — |",
        f"| Wrong exception classification | {counts.wrong_exception_classification_count} | — |",
        "",
        "## Runtime",
        "",
        f"- End-to-end runtime p50/p95: {report.runtime_p50_ms} ms / {report.runtime_p95_ms} ms",
        "- Throughput p50/p95: "
        f"{report.throughput_p50_events_per_second} / "
        f"{report.throughput_p95_events_per_second} events/s",
        "",
        "## Per-seed results",
        "",
        "| Seed | Events | Cases | Case accuracy | False clears | Runtime ms | Events/s |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for seed in report.seed_results:
        metrics = seed.evaluation.metrics
        lines.append(
            f"| {seed.seed} | {seed.source_event_count} | {seed.decision_count} | "
            f"{metrics.case_accuracy_bps / 100:.2f}% | {metrics.counts.false_clear_count} | "
            f"{seed.end_to_end_runtime_ms} | {seed.throughput_events_per_second} |"
        )
    lines.extend(["", "## Threshold violations", ""])
    if report.threshold_violations:
        lines.extend(f"- `{item}`" for item in report.threshold_violations)
    else:
        lines.append("- None")
    lines.extend(["", "## Incorrect cases and events", ""])
    incorrect = False
    for seed in report.seed_results:
        bad_cases = tuple(item for item in seed.evaluation.case_results if not item.correct)
        if not bad_cases and not seed.evaluation.incorrect_event_ids:
            continue
        incorrect = True
        lines.append(f"### Seed {seed.seed}")
        lines.append("")
        for case in bad_cases:
            predicted_level = (
                case.predicted_proof_level.value
                if case.predicted_proof_level
                else "MISSING"
            )
            lines.append(
                f"- `{case.expected_case_id}` / `{case.scenario}`: expected "
                f"`{case.expected_proof_level.value}`, predicted "
                f"`{predicted_level}`; "
                f"decision `{case.predicted_decision_id or 'MISSING'}`"
            )
        if seed.evaluation.incorrect_event_ids:
            lines.append(
                "- Incorrect event IDs: "
                + ", ".join(f"`{item}`" for item in seed.evaluation.incorrect_event_ids)
            )
        lines.append("")
    if not incorrect:
        lines.append("No incorrect cases or events.")
        lines.append("")
    return "\n".join(lines)


def _integer_mapping(value: object, name: str) -> dict[str, int]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise TypeError(f"{name} must be a string-keyed mapping")
    if any(isinstance(item, bool) or not isinstance(item, int) for item in value.values()):
        raise TypeError(f"{name} values must be integers")
    return value


def _seeds(value: object, name: str, *, minimum: int) -> tuple[int, ...]:
    if not isinstance(value, list) or any(
        isinstance(item, bool) or not isinstance(item, int) or item < 0 for item in value
    ):
        raise TypeError(f"{name} must contain non-negative integer seeds")
    if len(value) < minimum or len(set(value)) != len(value):
        raise ValueError(f"{name} requires at least {minimum} unique seeds")
    return tuple(value)


def _json_default(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value):
        return asdict(value)
    raise TypeError(f"cannot serialize {type(value).__name__}")


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config/evaluation/default.yaml"))
    parser.add_argument("--seeds", help="Comma-separated seed override")
    parser.add_argument("--submission", action="store_true", help="Use the ten-seed profile")
    parser.add_argument(
        "--output-prefix",
        type=Path,
        default=Path("evaluation/reports/benchmark-latest"),
    )
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    config = load_benchmark_config(args.config)
    if args.seeds:
        seeds = tuple(int(item.strip()) for item in args.seeds.split(",") if item.strip())
    else:
        seeds = config.submission_seeds if args.submission else config.development_seeds
    report = run_benchmark(config, seeds=seeds)
    json_path, markdown_path = write_reports(report, args.output_prefix)
    print(
        json.dumps(
            {
                "status": "passed" if report.threshold_passed else "failed",
                "seeds": list(report.seeds),
                "event_count": report.aggregate_metrics.counts.truth_event_count,
                "case_count": report.aggregate_metrics.counts.truth_case_count,
                "auto_clear_precision_bps": report.aggregate_metrics.auto_clear_precision_bps,
                "exception_recall_bps": report.aggregate_metrics.exception_recall_bps,
                "false_clear_count": report.aggregate_metrics.counts.false_clear_count,
                "false_clear_rate_bps": report.aggregate_metrics.false_clear_rate_bps,
                "runtime_p50_ms": report.runtime_p50_ms,
                "runtime_p95_ms": report.runtime_p95_ms,
                "json_report": str(json_path),
                "markdown_report": str(markdown_path),
                "violations": list(report.threshold_violations),
            },
            sort_keys=True,
        )
    )
    return 0 if report.threshold_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
