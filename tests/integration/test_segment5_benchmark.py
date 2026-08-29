from datetime import UTC, datetime
from pathlib import Path

from evaluation.benchmark import load_benchmark_config, run_benchmark, write_reports


def test_single_seed_benchmark_reads_stored_results_and_writes_diagnostics(
    tmp_path: Path,
) -> None:
    config = load_benchmark_config(Path("config/evaluation/default.yaml"))
    report = run_benchmark(
        config,
        seeds=(19,),
        generated_at=datetime(2026, 8, 27, tzinfo=UTC),
    )
    assert report.threshold_passed
    assert report.aggregate_metrics.counts.truth_event_count >= 50
    assert report.aggregate_metrics.counts.truth_case_count == 25
    assert report.aggregate_metrics.auto_clear_precision_bps == 10_000
    assert report.aggregate_metrics.exception_recall_bps == 10_000
    assert report.aggregate_metrics.counts.false_clear_count == 0
    assert not report.seed_results[0].evaluation.incorrect_event_ids

    json_path, markdown_path = write_reports(report, tmp_path / "benchmark")
    assert '"threshold_passed": true' in json_path.read_text(encoding="utf-8")
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "Status: **PASS**" in markdown
    assert "No incorrect cases or events." in markdown
