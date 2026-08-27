"""DuckDB repository implementations sharing one explicit transaction."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from types import TracebackType
from typing import Any

import duckdb

from core.vericlose.audit.events import AuditEvent
from core.vericlose.domain.actions import ActionReceipt, ProposedAction, ReviewDecision
from core.vericlose.domain.decisions import ReconciliationDecision
from core.vericlose.domain.enums import (
    ActionType,
    DecisionState,
    ExceptionCategory,
    ProofLevel,
    RunState,
    Severity,
    SourceType,
)
from core.vericlose.domain.events import CanonicalEvent
from core.vericlose.domain.evidence import EvidenceLink, ProofCheck
from core.vericlose.domain.exceptions import ExceptionCase
from core.vericlose.domain.money import Money
from core.vericlose.domain.runs import RunManifest, SourceFile
from core.vericlose.domain.wire import canonical_event_from_dict, canonical_event_to_dict
from core.vericlose.ingestion.contracts import (
    ControlTotals,
    IssueSeverity,
    NormalizationResult,
    ValidationIssue,
    ValidationReport,
    ValidationStage,
)
from core.vericlose.ports.repositories import ReconciliationRunRecord, SourceFileRecord

MIGRATION_ROOT = Path(__file__).with_name("migrations")


class DuckDBUnitOfWork:
    """One import/review operation commits atomically or rolls back completely."""

    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path
        self.connection: duckdb.DuckDBPyConnection | None = None

    def __enter__(self) -> DuckDBUnitOfWork:
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = duckdb.connect(str(self._database_path))
        apply_migrations(self.connection)
        self.connection.execute("BEGIN TRANSACTION")
        self.runs = DuckDBRunRepository(self.connection)
        self.source_files = DuckDBSourceFileRepository(self.connection)
        self.events = DuckDBEventRepository(self.connection)
        self.decisions = DuckDBDecisionRepository(self.connection)
        self.exceptions = DuckDBExceptionRepository(self.connection)
        self.reconciliation = DuckDBReconciliationRunRepository(self.connection)
        self.reviews = DuckDBReviewRepository(self.connection)
        self.actions = DuckDBActionRepository(self.connection)
        self.audit = DuckDBAuditRepository(self.connection)
        self.ingestion = DuckDBIngestionRepository(self.connection)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self.connection is None:
            return
        try:
            self.connection.execute("ROLLBACK" if exc_type else "COMMIT")
        finally:
            self.connection.close()
            self.connection = None


def apply_migrations(connection: duckdb.DuckDBPyConnection) -> None:
    connection.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations "
        "(version VARCHAR PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT current_timestamp)"
    )
    applied = {
        row[0] for row in connection.execute("SELECT version FROM schema_migrations").fetchall()
    }
    for path in sorted(MIGRATION_ROOT.glob("*.sql")):
        if path.stem in applied:
            continue
        connection.execute(path.read_text(encoding="utf-8"))
        connection.execute("INSERT INTO schema_migrations(version) VALUES (?)", [path.stem])


class DuckDBRunRepository:
    def __init__(self, connection: duckdb.DuckDBPyConnection) -> None:
        self._connection = connection

    def append(self, manifest: RunManifest) -> None:
        next_snapshot = self._connection.execute(
            "SELECT coalesce(max(snapshot_number), 0) + 1 FROM runs WHERE run_id = ?",
            [manifest.run_id],
        ).fetchone()[0]
        self._connection.execute(
            "INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                manifest.run_id,
                next_snapshot,
                manifest.state.value,
                manifest.policy_version,
                manifest.rule_version,
                _json(_run_to_dict(manifest)),
                manifest.created_at,
            ],
        )

    def get(self, run_id: str) -> RunManifest | None:
        row = self._connection.execute(
            "SELECT payload_json FROM runs WHERE run_id = ? ORDER BY snapshot_number DESC LIMIT 1",
            [run_id],
        ).fetchone()
        return _run_from_dict(json.loads(row[0])) if row else None


class DuckDBSourceFileRepository:
    def __init__(self, connection: duckdb.DuckDBPyConnection) -> None:
        self._connection = connection

    def add(self, record: SourceFileRecord) -> None:
        source = record.source_file
        self._connection.execute(
            "INSERT INTO source_files VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                record.run_id,
                source.file_id,
                source.source_type.value,
                source.sha256,
                source.original_name,
                source.size_bytes,
                source.uploaded_at,
                record.adapter_id,
                record.adapter_version,
                record.mapping_profile_version,
                record.relative_path,
            ],
        )

    def exists_hash(self, run_id: str, sha256: str) -> bool:
        return bool(
            self._connection.execute(
                "SELECT count(*) FROM source_files WHERE run_id = ? AND sha256 = ?",
                [run_id, sha256],
            ).fetchone()[0]
        )

    def list_for_run(self, run_id: str) -> tuple[SourceFileRecord, ...]:
        rows = self._connection.execute(
            "SELECT file_id, source_type, sha256, original_name, size_bytes, "
            "CAST(uploaded_at AS VARCHAR), "
            "adapter_id, adapter_version, mapping_profile_version, relative_path "
            "FROM source_files WHERE run_id = ? ORDER BY file_id",
            [run_id],
        ).fetchall()
        return tuple(
            SourceFileRecord(
                run_id,
                SourceFile(
                    row[0],
                    SourceType(row[1]),
                    row[2],
                    row[3],
                    row[4],
                    datetime.fromisoformat(row[5].replace(" ", "T")),
                ),
                row[6],
                row[7],
                row[8],
                row[9],
            )
            for row in rows
        )


class DuckDBEventRepository:
    def __init__(self, connection: duckdb.DuckDBPyConnection) -> None:
        self._connection = connection

    def append(self, run_id: str, events: tuple[CanonicalEvent, ...]) -> None:
        for event in events:
            if event.run_id != run_id:
                raise ValueError("event run_id does not match repository run_id")
            self._connection.execute(
                "INSERT INTO canonical_events VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    run_id,
                    event.event_id,
                    event.lineage.source_file_id,
                    event.lineage.row_number,
                    event.lineage.file_sha256,
                    event.lineage.raw_row_hash,
                    event.mapping_profile_version,
                    _json(canonical_event_to_dict(event)),
                ],
            )

    def list_for_run(self, run_id: str) -> tuple[CanonicalEvent, ...]:
        rows = self._connection.execute(
            "SELECT payload_json FROM canonical_events WHERE run_id = ? ORDER BY event_id",
            [run_id],
        ).fetchall()
        return tuple(canonical_event_from_dict(json.loads(row[0])) for row in rows)


class DuckDBDecisionRepository:
    def __init__(self, connection: duckdb.DuckDBPyConnection) -> None:
        self._connection = connection

    def append(self, run_id: str, decision: ReconciliationDecision) -> None:
        self._connection.execute(
            "INSERT INTO decisions VALUES (?, ?, ?)",
            [run_id, decision.decision_id, _json(decision)],
        )
        for ordinal, check in enumerate(decision.proof_checks, start=1):
            self._connection.execute(
                "INSERT INTO proof_checks VALUES (?, ?, ?, ?)",
                [run_id, decision.decision_id, ordinal, _json(check)],
            )
        _append_evidence(
            self._connection,
            run_id,
            "DECISION",
            decision.decision_id,
            decision.evidence_links,
        )

    def list_for_run(self, run_id: str) -> tuple[ReconciliationDecision, ...]:
        rows = self._connection.execute(
            "SELECT payload_json FROM decisions WHERE run_id = ? ORDER BY decision_id",
            [run_id],
        ).fetchall()
        return tuple(_decision_from_dict(json.loads(row[0])) for row in rows)


class DuckDBExceptionRepository:
    def __init__(self, connection: duckdb.DuckDBPyConnection) -> None:
        self._connection = connection

    def append(self, run_id: str, exception: ExceptionCase) -> None:
        self._connection.execute(
            "INSERT INTO exceptions VALUES (?, ?, ?)",
            [run_id, exception.case_id, _json(exception)],
        )
        _append_evidence(
            self._connection,
            run_id,
            "EXCEPTION",
            exception.case_id,
            exception.evidence_links,
        )

    def list_for_run(self, run_id: str) -> tuple[ExceptionCase, ...]:
        rows = self._connection.execute(
            "SELECT payload_json FROM exceptions WHERE run_id = ? ORDER BY case_id",
            [run_id],
        ).fetchall()
        return tuple(_exception_from_dict(json.loads(row[0])) for row in rows)


class DuckDBReconciliationRunRepository:
    def __init__(self, connection: duckdb.DuckDBPyConnection) -> None:
        self._connection = connection

    def append(self, record: ReconciliationRunRecord) -> None:
        self._connection.execute(
            "INSERT INTO reconciliation_runs "
            "(run_id, policy_version, rule_version, decision_count, auto_cleared_count, "
            "exception_count, amount_at_risk_minor, stage_timings_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                record.run_id,
                record.policy_version,
                record.rule_version,
                record.decision_count,
                record.auto_cleared_count,
                record.exception_count,
                record.amount_at_risk_minor,
                _json(record.stage_timings),
            ],
        )

    def get(self, run_id: str) -> ReconciliationRunRecord | None:
        row = self._connection.execute(
            "SELECT policy_version, rule_version, decision_count, auto_cleared_count, "
            "exception_count, amount_at_risk_minor, stage_timings_json "
            "FROM reconciliation_runs WHERE run_id = ?",
            [run_id],
        ).fetchone()
        if not row:
            return None
        return ReconciliationRunRecord(
            run_id,
            row[0],
            row[1],
            row[2],
            row[3],
            row[4],
            row[5],
            tuple(tuple(item) for item in json.loads(row[6])),
        )


class DuckDBReviewRepository:
    def __init__(self, connection: duckdb.DuckDBPyConnection) -> None:
        self._connection = connection

    def append(self, run_id: str, review: ReviewDecision) -> None:
        self._connection.execute(
            "INSERT INTO reviews VALUES (?, ?, ?, ?)",
            [run_id, review.review_id, _json(review), review.reviewed_at],
        )


class DuckDBActionRepository:
    def __init__(self, connection: duckdb.DuckDBPyConnection) -> None:
        self._connection = connection

    def append_action(self, run_id: str, action: ProposedAction) -> None:
        snapshot = self._connection.execute(
            "SELECT coalesce(max(snapshot_number), 0) + 1 FROM actions "
            "WHERE run_id = ? AND action_id = ?",
            [run_id, action.action_id],
        ).fetchone()[0]
        self._connection.execute(
            "INSERT INTO actions VALUES (?, ?, ?, ?, ?)",
            [run_id, action.action_id, snapshot, _json(action), action.created_at],
        )

    def append_receipt(self, run_id: str, receipt: ActionReceipt) -> None:
        self._connection.execute(
            "INSERT INTO receipts VALUES (?, ?, ?, ?, ?, ?)",
            [
                run_id,
                receipt.receipt_id,
                receipt.action_id,
                receipt.idempotency_key,
                _json(receipt),
                receipt.executed_at,
            ],
        )


class DuckDBAuditRepository:
    def __init__(self, connection: duckdb.DuckDBPyConnection) -> None:
        self._connection = connection

    def append(self, event: AuditEvent) -> None:
        self._connection.execute(
            "INSERT INTO audit_events VALUES (?, ?, ?, ?, ?)",
            [event.run_id, event.audit_id, event.event_type, _json(event), event.occurred_at],
        )


class DuckDBIngestionRepository:
    def __init__(self, connection: duckdb.DuckDBPyConnection) -> None:
        self._connection = connection

    def append_file_result(
        self,
        run_id: str,
        validation: ValidationReport,
        normalization: NormalizationResult | None,
        control_totals: ControlTotals | None,
    ) -> None:
        issues = normalization.issues if normalization is not None else validation.issues
        for ordinal, issue in enumerate(issues, start=1):
            self._connection.execute(
                "INSERT INTO validation_issues VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    run_id,
                    issue.file_id,
                    ordinal,
                    issue.stage.value,
                    issue.severity.value,
                    issue.code,
                    issue.row_number,
                    issue.blocking,
                    _json(_validation_issue_to_dict(issue)),
                ],
            )
        if normalization is not None:
            for disposition in normalization.row_dispositions:
                self._connection.execute(
                    "INSERT INTO row_dispositions VALUES (?, ?, ?, ?, ?, ?)",
                    [
                        run_id,
                        normalization.source_file_id,
                        disposition.row_number,
                        disposition.status.value,
                        _json(disposition.event_ids),
                        _json(disposition.issue_codes),
                    ],
                )
        if control_totals is not None:
            for component in control_totals.components:
                self._connection.execute(
                    "INSERT INTO control_totals VALUES (?, ?, ?, ?, ?, ?)",
                    [
                        run_id,
                        validation.source_file_id,
                        component.component,
                        component.currency,
                        component.amount_minor,
                        component.record_count,
                    ],
                )

    def list_issues(self, run_id: str) -> tuple[ValidationIssue, ...]:
        rows = self._connection.execute(
            "SELECT payload_json FROM validation_issues WHERE run_id = ? ORDER BY file_id, ordinal",
            [run_id],
        ).fetchall()
        return tuple(_validation_issue_from_dict(json.loads(row[0])) for row in rows)


def _json(value: object) -> str:
    return json.dumps(value, default=_json_default, sort_keys=True, separators=(",", ":"))


def _json_default(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if is_dataclass(value):
        return asdict(value)
    raise TypeError(f"cannot serialize {type(value).__name__}")


def _run_to_dict(manifest: RunManifest) -> dict[str, Any]:
    return {
        "run_id": manifest.run_id,
        "state": manifest.state.value,
        "seed": manifest.seed,
        "policy_version": manifest.policy_version,
        "rule_version": manifest.rule_version,
        "mapping_versions": list(manifest.mapping_versions),
        "input_files": [
            {
                "file_id": item.file_id,
                "source_type": item.source_type.value,
                "sha256": item.sha256,
                "original_name": item.original_name,
                "size_bytes": item.size_bytes,
                "uploaded_at": item.uploaded_at.isoformat(),
            }
            for item in manifest.input_files
        ],
        "build_commit": manifest.build_commit,
        "created_at": manifest.created_at.isoformat(),
    }


def _run_from_dict(payload: dict[str, Any]) -> RunManifest:
    return RunManifest(
        run_id=payload["run_id"],
        state=RunState(payload["state"]),
        seed=payload["seed"],
        policy_version=payload["policy_version"],
        rule_version=payload["rule_version"],
        mapping_versions=tuple(tuple(pair) for pair in payload["mapping_versions"]),
        input_files=tuple(
            SourceFile(
                item["file_id"],
                SourceType(item["source_type"]),
                item["sha256"],
                item["original_name"],
                item["size_bytes"],
                datetime.fromisoformat(item["uploaded_at"]),
            )
            for item in payload["input_files"]
        ),
        build_commit=payload["build_commit"],
        created_at=datetime.fromisoformat(payload["created_at"]),
    )


def _validation_issue_to_dict(issue: ValidationIssue) -> dict[str, Any]:
    return {
        "stage": issue.stage.value,
        "severity": issue.severity.value,
        "code": issue.code,
        "message": issue.message,
        "file_id": issue.file_id,
        "table_name": issue.table_name,
        "row_number": issue.row_number,
        "field_name": issue.field_name,
        "supplied_value": issue.supplied_value,
        "suggested_fix": issue.suggested_fix,
        "blocking": issue.blocking,
    }


def _validation_issue_from_dict(payload: dict[str, Any]) -> ValidationIssue:
    return ValidationIssue(
        stage=ValidationStage(payload["stage"]),
        severity=IssueSeverity(payload["severity"]),
        code=payload["code"],
        message=payload["message"],
        file_id=payload["file_id"],
        table_name=payload["table_name"],
        row_number=payload["row_number"],
        field_name=payload["field_name"],
        supplied_value=payload["supplied_value"],
        suggested_fix=payload["suggested_fix"],
        blocking=payload["blocking"],
    )


def _append_evidence(
    connection: duckdb.DuckDBPyConnection,
    run_id: str,
    owner_type: str,
    owner_id: str,
    links: tuple[EvidenceLink, ...],
) -> None:
    for ordinal, link in enumerate(links, start=1):
        connection.execute(
            "INSERT INTO evidence_links VALUES (?, ?, ?, ?, ?)",
            [run_id, owner_type, owner_id, ordinal, _json(link)],
        )


def _evidence_from_dict(payload: dict[str, Any]) -> EvidenceLink:
    return EvidenceLink(
        payload["event_id"],
        payload["source_file_id"],
        payload["table_name"],
        payload["row_number"],
        payload["raw_row_hash"],
        payload["purpose"],
    )


def _proof_check_from_dict(payload: dict[str, Any]) -> ProofCheck:
    return ProofCheck(
        payload["check_code"],
        payload["expected"],
        payload["observed"],
        payload["tolerance_minor"],
        payload["passed"],
        payload["required"],
        tuple(_evidence_from_dict(item) for item in payload["evidence_links"]),
    )


def _decision_from_dict(payload: dict[str, Any]) -> ReconciliationDecision:
    return ReconciliationDecision(
        payload["decision_id"],
        DecisionState(payload["state"]),
        tuple(payload["event_ids"]),
        ProofLevel(payload["proof_level"]),
        tuple(_proof_check_from_dict(item) for item in payload["proof_checks"]),
        tuple(_evidence_from_dict(item) for item in payload["evidence_links"]),
        payload["uniqueness_passed"],
        payload["contradiction_reason"],
        payload["policy_allows_auto_clear"],
        tuple(payload["related_proposal_ids"]),
    )


def _exception_from_dict(payload: dict[str, Any]) -> ExceptionCase:
    money = payload["amount_at_risk"]
    return ExceptionCase(
        payload["case_id"],
        payload["reason_code"],
        ExceptionCategory(payload["category"]),
        Severity(payload["severity"]),
        Money(money["amount_minor"], money["currency"]),
        ProofLevel(payload["proof_level"]),
        tuple(_evidence_from_dict(item) for item in payload["evidence_links"]),
        tuple(payload["rules_attempted"]),
        payload["requires_company_input"],
        ActionType(payload["recommended_action"]),
        payload["owner"],
    )
