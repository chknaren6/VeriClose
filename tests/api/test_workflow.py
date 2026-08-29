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
        assert len(cases.json()) == 25
        exception = next(item for item in cases.json() if item["proof_level"] != "PROVED")
        detail = await client.get(f"/api/v1/cases/{exception['case_id']}")
        assert detail.status_code == 200
        assert detail.json()["events"]
        assert detail.json()["evidence"]
        assert detail.json()["proof_checks"]
        assert detail.json()["advisory"]["status"] == "unavailable"
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
