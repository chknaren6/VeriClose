from __future__ import annotations

import base64
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx2
import pytest

from apps.api.app.main import create_app
from apps.api.app.settings import AppSettings
from synthetic.base_case import SyntheticConfig
from synthetic.generate import generate


@asynccontextmanager
async def _client(tmp_path: Path) -> AsyncIterator[httpx2.AsyncClient]:
    settings = AppSettings(
        environment="test",
        data_dir=tmp_path / "data",
        database_path=tmp_path / "data" / "workflow.duckdb",
        static_dir=tmp_path / "missing-static",
        build_commit="segment6-test",
        demo_mode=True,
        # Hermetic: never call the live advisory model from tests,
        # even when a developer .env key is present.
        model_api_key=None,
    )
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        transport = httpx2.ASGITransport(app=app)
        async with httpx2.AsyncClient(transport=transport, base_url="http://test") as client:
            yield client


def _upload_payload(generated: Path) -> dict:
    documents = []
    for file_id, filename in (
        ("gateway", "gateway.csv"),
        ("bank", "bank.csv"),
        ("erp", "erp_gl.csv"),
    ):
        documents.append(
            {
                "file_id": file_id,
                "original_name": filename,
                "media_type": "text/csv",
                "content_base64": base64.b64encode(
                    (generated / "inputs" / filename).read_bytes()
                ).decode(),
            }
        )
    return {
        "run_id": "segment6-api-flow",
        "legal_entity_id": "demo-merchant-in",
        "documents": documents,
        "confirmations": [],
    }


@pytest.mark.anyio
async def test_api_completes_import_reconcile_evidence_and_review_loop(tmp_path: Path) -> None:
    generated = tmp_path / "generated"
    generate(SyntheticConfig(), generated)
    payload = _upload_payload(generated)

    async with _client(tmp_path) as client:
        detected = await client.post("/api/v1/uploads/detect", json=payload)
        assert detected.status_code == 200
        payload["confirmations"] = [
            {
                "file_id": item["file_id"],
                "adapter_id": item["candidates"][0]["adapter_id"],
                "profile_versioned_id": item["candidates"][0]["profile_versioned_id"],
            }
            for item in detected.json()["files"]
            if item["requires_confirmation"]
        ]

        imported = await client.post("/api/v1/uploads", json=payload)
        assert imported.status_code == 201, imported.text
        assert imported.json()["state"] == "VALIDATED"
        assert imported.json()["event_count"] == 315
        assert all(item["mapping"] for item in imported.json()["files"])
        assert all(item["sample_rows"] for item in imported.json()["files"])

        started = await client.post("/api/v1/runs", json={"run_id": payload["run_id"]})
        assert started.status_code == 200, started.text
        assert started.json()["state"] == "COMPLETED"
        assert started.json()["benchmark_accuracy_available"] is False

        cases = await client.get(f"/api/v1/runs/{payload['run_id']}/cases")
        assert cases.status_code == 200
        case_items = cases.json()
        assert len(case_items) == 25
        exception = next(item for item in case_items if item["proof_level"] != "PROVED")
        detail = await client.get(f"/api/v1/cases/{exception['case_id']}")
        assert detail.status_code == 200
        assert detail.json()["events"]
        assert detail.json()["evidence"]
        assert detail.json()["proof_checks"]
        assert detail.json()["advisory"]["status"] == "NOT_REQUESTED"
        assert all("row_number" in event for event in detail.json()["events"])
        original_event_ids = [event["event_id"] for event in detail.json()["events"]]

        metrics = await client.get(f"/api/v1/runs/{payload['run_id']}/metrics")
        assert metrics.status_code == 200
        assert metrics.json()["kind"] == "operational"
        assert metrics.json()["accuracy_claims"] is None
        assert metrics.json()["summary"]["decision_count"] == 25

        reviewed = await client.post(
            f"/api/v1/cases/{exception['case_id']}/reviews",
            json={
                "state": "DEFERRED",
                "reviewer_id": "dad-reviewer",
                "comment": "Waiting for company remittance advice",
            },
        )
        assert reviewed.status_code == 201
        refreshed = await client.get(f"/api/v1/cases/{exception['case_id']}")
        assert refreshed.json()["reviews"][-1]["state"] == "DEFERRED"
        assert [event["event_id"] for event in refreshed.json()["events"]] == original_event_ids

        investigation = await client.post(f"/api/v1/cases/{exception['case_id']}/investigations")
        assert investigation.status_code == 201
        assert investigation.json()["status"] == "DETERMINISTIC_FALLBACK"
        assert investigation.json()["failure_code"] == "MODEL_UNAVAILABLE"
        rejected_advice = await client.post(
            f"/api/v1/cases/{exception['case_id']}/investigation-reviews",
            json={
                "state": "REJECTED",
                "reviewer_id": "dad-reviewer",
                "comment": "Need remittance advice first",
            },
        )
        assert rejected_advice.status_code == 201

        answered = await client.post(
            f"/api/v1/runs/{payload['run_id']}/questions",
            json={"question": f"Why is {exception['case_id']} unresolved?"},
        )
        assert answered.json()["status"] == "ANSWERED"
        abstained = await client.post(
            f"/api/v1/runs/{payload['run_id']}/questions",
            json={"question": "What happened in an absent supplier system?"},
        )
        assert abstained.json()["status"] == "ABSTAINED"

        for kind in ("close-report", "exception-pack", "audit-log"):
            artifact = await client.get(f"/api/v1/runs/{payload['run_id']}/artifacts/{kind}")
            assert artifact.status_code == 200
            assert artifact.content
            assert len(artifact.headers["x-vericlose-sha256"]) == 64

        missing_erp = next(
            item for item in case_items if item["reason_code"] == "MISSING_ERP_POSTING"
        )
        proposed = await client.post(f"/api/v1/cases/{missing_erp['case_id']}/actions")
        assert proposed.status_code == 201, proposed.text
        action = proposed.json()
        assert action["action_type"] == "JOURNAL_EXPORT"
        assert action["journal_lines"]
        premature = await client.post(f"/api/v1/actions/{action['action_id']}/export")
        assert premature.status_code == 409
        approved = await client.post(
            f"/api/v1/actions/{action['action_id']}/reviews",
            json={
                "state": "APPROVED",
                "reviewer_id": "controller-01",
                "comment": "Accounts and evidence checked",
                "edits": {},
            },
        )
        assert approved.json()["state"] == "APPROVED"
        exported = await client.post(f"/api/v1/actions/{action['action_id']}/export")
        assert exported.status_code == 200
        repeated_export = await client.post(f"/api/v1/actions/{action['action_id']}/export")
        assert repeated_export.json()["receipt_id"] == exported.json()["receipt_id"]
        journal = await client.get(f"/api/v1/actions/{action['action_id']}/artifact")
        assert journal.status_code == 200
        assert b"amount_minor" in journal.content

        correction = await client.post(
            f"/api/v1/actions/{action['action_id']}/apply-correction",
            json={"new_run_id": "segment9-corrected"},
        )
        assert correction.status_code == 200, correction.text
        assert correction.json()["previous_proof_level"] == "SUPPORTED"
        assert correction.json()["new_proof_level"] == "PROVED"
        assert correction.json()["resolved"] is True

        benchmark = await client.get("/api/v1/benchmarks/latest")
        assert benchmark.status_code == 404
        assert benchmark.json()["error"]["code"] == "BENCHMARK_MODE_REQUIRED"


@pytest.mark.anyio
async def test_invalid_batch_cannot_start_reconciliation(tmp_path: Path) -> None:
    generated = tmp_path / "generated-invalid"
    generate(SyntheticConfig(), generated)
    payload = _upload_payload(generated)
    payload["run_id"] = "segment6-invalid"
    payload["documents"] = payload["documents"][:1]

    async with _client(tmp_path) as client:
        detected = await client.post("/api/v1/uploads/detect", json=payload)
        assert detected.status_code == 200
        imported = await client.post("/api/v1/uploads", json=payload)
        assert imported.status_code == 201
        assert imported.json()["state"] == "FAILED_VALIDATION"
        started = await client.post("/api/v1/runs", json={"run_id": payload["run_id"]})
        assert started.status_code == 409
        assert started.json()["error"]["code"] == "WORKFLOW_CONFLICT"


@pytest.mark.anyio
async def test_demo_reset_restores_known_proved_and_exception_cases(tmp_path: Path) -> None:
    async with _client(tmp_path) as client:
        reset = await client.post("/api/v1/demo/reset")
        assert reset.status_code == 200, reset.text
        run = reset.json()
        assert run["state"] == "COMPLETED"
        summary = run["operational_summary"]
        assert summary["decision_count"] == 25
        assert summary["verified_count"] == 15
        assert summary["review_or_exception_count"] == 10
        assert max(item["input_count"] for item in summary["stage_timings"]) == 315

        cases = (await client.get(f"/api/v1/runs/{run['run_id']}/cases")).json()
        assert {item["proof_level"] for item in cases} == {
            "PROVED",
            "SUPPORTED",
            "AMBIGUOUS",
            "CONTRADICTED",
            "INVALID_INPUT",
        }
        assert {item["reason_code"] for item in cases if item["reason_code"]} >= {
            "MISSING_BANK_RECEIPT",
            "MISSING_ERP_POSTING",
        }
        exception = next(item for item in cases if item["proof_level"] != "PROVED")
        detail = await client.get(f"/api/v1/cases/{exception['case_id']}")
        assert detail.status_code == 200
        assert detail.json()["evidence"]

        restored_again = await client.post("/api/v1/demo/reset")
        assert restored_again.status_code == 200
        assert restored_again.json()["run_id"] != run["run_id"]


@pytest.mark.anyio
async def test_upload_boundary_rejects_invalid_encoding_format_and_size(tmp_path: Path) -> None:
    async with _client(tmp_path) as client:
        base = {
            "run_id": "unsafe-upload-test",
            "legal_entity_id": "demo-merchant-in",
            "confirmations": [],
        }
        invalid_base64 = await client.post(
            "/api/v1/uploads/detect",
            json={
                **base,
                "documents": [
                    {
                        "file_id": "gateway",
                        "original_name": "gateway.csv",
                        "media_type": "text/csv",
                        "content_base64": "not-base64!",
                    }
                ],
            },
        )
        assert invalid_base64.status_code == 400
        assert invalid_base64.json()["error"]["code"] == "UPLOAD_BASE64_INVALID"

        unsupported = await client.post(
            "/api/v1/uploads/detect",
            json={
                **base,
                "documents": [
                    {
                        "file_id": "gateway",
                        "original_name": "../../client-ledger.pdf",
                        "media_type": "application/pdf",
                        "content_base64": base64.b64encode(b"synthetic").decode(),
                    }
                ],
            },
        )
        assert unsupported.status_code == 400
        assert unsupported.json()["error"]["code"] == "UPLOAD_FORMAT_UNSUPPORTED"
