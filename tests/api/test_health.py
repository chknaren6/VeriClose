from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx2
import pytest

from apps.api.app.composition import build_container
from apps.api.app.main import create_app
from apps.api.app.settings import AppSettings


@asynccontextmanager
async def build_test_client(tmp_path: Path) -> AsyncIterator[httpx2.AsyncClient]:
    settings = AppSettings(
        environment="test",
        data_dir=tmp_path / "data",
        database_path=tmp_path / "data" / "test.duckdb",
        static_dir=tmp_path / "missing-static",
        build_commit="test-commit",
        demo_mode=True,
    )
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        transport = httpx2.ASGITransport(app=app)
        async with httpx2.AsyncClient(transport=transport, base_url="http://test") as client:
            yield client


@pytest.mark.anyio
async def test_liveness(tmp_path: Path) -> None:
    async with build_test_client(tmp_path) as client:
        response = await client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


@pytest.mark.anyio
async def test_readiness_prepares_writable_storage(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"

    async with build_test_client(tmp_path) as client:
        response = await client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["checks"]["model"] == "deterministic-fallback"
    assert data_dir.is_dir()


@pytest.mark.anyio
async def test_judge_readiness_fails_when_production_assets_are_missing(tmp_path: Path) -> None:
    settings = AppSettings(
        environment="judge-local",
        data_dir=tmp_path / "data",
        database_path=tmp_path / "data" / "test.duckdb",
        static_dir=tmp_path / "missing-static",
    )
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        transport = httpx2.ASGITransport(app=app)
        async with httpx2.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["detail"] == "VeriClose runtime dependencies are not ready"


@pytest.mark.anyio
async def test_meta_reports_non_secret_runtime_configuration(tmp_path: Path) -> None:
    async with build_test_client(tmp_path) as client:
        response = await client.get("/api/meta")

    assert response.status_code == 200
    assert response.json() == {
        "app": "VeriClose",
        "environment": "test",
        "build_commit": "test-commit",
        "rule_version": "segment4-v1",
        "policy_version": "razorpay_inr_v1@1.0.0",
        "demo_mode": True,
        "model_enabled": False,
    }


@pytest.mark.anyio
async def test_development_root_explains_how_to_open_the_ui(tmp_path: Path) -> None:
    async with build_test_client(tmp_path) as client:
        response = await client.get("/")

    assert response.status_code == 200
    assert response.json()["health"] == "/health/ready"


def test_composition_rejects_a_policy_version_mismatch(tmp_path: Path) -> None:
    settings = AppSettings(
        environment="test",
        data_dir=tmp_path / "data",
        database_path=tmp_path / "data" / "test.duckdb",
        static_dir=tmp_path / "missing-static",
        policy_version="unexpected@9",
    )
    with pytest.raises(ValueError, match="does not match"):
        build_container(settings)
