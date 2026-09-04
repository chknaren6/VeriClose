"""Generate traceable submission artifacts from the checked-in synthetic demo batch."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory

from apps.api.app.composition import build_container
from apps.api.app.settings import AppSettings
from core.vericlose.domain.enums import ActionType, ReviewState

GENERATED_AT = datetime(2026, 9, 4, 12, 0, tzinfo=UTC)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("docs/examples"))
    parser.add_argument("--build-commit", default="local")
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    with TemporaryDirectory(prefix="vericlose-examples-") as temporary:
        root = Path(temporary)
        container = build_container(
            AppSettings(
                environment="test",
                data_dir=root / "data",
                database_path=root / "data" / "examples.duckdb",
                static_dir=root / "missing-static",
                demo_fixture_dir=Path("demo/seed-42/inputs"),
                build_commit=args.build_commit,
                demo_mode=True,
            )
        )
        run = container.demo_reset.reset(
            run_id="example-seed-42-v1", now=GENERATED_AT
        ).run
        case = next(
            item
            for item in container.review_query.list_cases(run.manifest.run_id)
            if item.exception
            and item.exception.recommended_action is ActionType.JOURNAL_EXPORT
        )
        action = container.actions.propose(case.case_id, proposed_at=GENERATED_AT)
        container.actions.review(
            action.action_id,
            state=ReviewState.APPROVED,
            reviewer_id="example-controller",
            comment="Synthetic example approval",
            reviewed_at=GENERATED_AT,
        )
        container.actions.export(action.action_id, exported_at=GENERATED_AT)
        action_download = container.actions.download(action.action_id)
        journal_path = output / "approved-journal.csv"
        journal_path.write_bytes(action_download.content)
        written.append(journal_path)

        for kind, filename in (
            ("close-report", "close-report.csv"),
            ("exception-pack", "exception-pack.json"),
            ("audit-log", "audit-log.json"),
        ):
            artifact = container.artifacts.build(run.manifest.run_id, kind)
            path = output / filename
            path.write_bytes(artifact.content)
            written.append(path)

    benchmark = Path("evaluation/reports/benchmark-latest.md")
    if not benchmark.is_file():
        raise FileNotFoundError("run `make benchmark` before generating examples")
    benchmark_copy = output / "benchmark-report.md"
    shutil.copyfile(benchmark, benchmark_copy)
    written.append(benchmark_copy)
    written.extend(sorted(output.glob("deployment-smoke-*.json")))
    browser_check = output / "browser-path-check.md"
    if browser_check.is_file():
        written.append(browser_check)

    manifest = {
        "schema_version": "1.0",
        "dataset": "checked-in synthetic seed-42 demo",
        "run_id": "example-seed-42-v1",
        "generated_at": GENERATED_AT.isoformat(),
        "build_commit": args.build_commit,
        "files": {
            path.name: {
                "sha256": sha256(path.read_bytes()).hexdigest(),
                "size_bytes": path.stat().st_size,
            }
            for path in sorted(written)
        },
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": "generated", "output": str(output), **manifest}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
