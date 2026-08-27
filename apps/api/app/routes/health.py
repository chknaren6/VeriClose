from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Request, status
from pydantic import BaseModel

router = APIRouter(tags=["system"])


class LiveResponse(BaseModel):
    status: str


class ReadyResponse(BaseModel):
    status: str
    checks: dict[str, str]


class MetaResponse(BaseModel):
    app: str
    environment: str
    build_commit: str
    rule_version: str
    policy_version: str
    demo_mode: bool
    model_enabled: bool


def _check_writable(directory: Path) -> None:
    with NamedTemporaryFile(prefix=".vericlose-ready-", dir=directory):
        pass


@router.get("/health/live", response_model=LiveResponse)
async def live() -> LiveResponse:
    return LiveResponse(status="alive")


@router.get(
    "/health/ready",
    response_model=ReadyResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Runtime is not ready"}},
)
async def ready(request: Request) -> ReadyResponse:
    container = request.app.state.container
    settings = container.settings
    settings.prepare_runtime_paths()
    _check_writable(settings.data_dir)
    return ReadyResponse(
        status="ready",
        checks={
            "data_directory": "writable",
            "configuration": "loaded",
            "policy": container.reconciliation_policy.versioned_id,
            "model": "enabled" if settings.model_enabled else "deterministic-fallback",
        },
    )


@router.get("/api/meta", response_model=MetaResponse)
async def meta(request: Request) -> MetaResponse:
    container = request.app.state.container
    settings = container.settings
    return MetaResponse(
        app=settings.app_name,
        environment=settings.environment,
        build_commit=settings.build_commit,
        rule_version=settings.rule_version,
        policy_version=container.reconciliation_policy.versioned_id,
        demo_mode=settings.demo_mode,
        model_enabled=settings.model_enabled,
    )
