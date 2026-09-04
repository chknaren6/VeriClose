from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from apps.api.app.composition import AppContainer, build_container
from apps.api.app.routes.health import router as health_router
from apps.api.app.routes.workflow import WorkflowError
from apps.api.app.routes.workflow import router as workflow_router
from apps.api.app.settings import AppSettings


def create_app(settings: AppSettings | None = None) -> FastAPI:
    container = build_container(settings)
    hosted = container.settings.environment == "hosted-demo"

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.container.settings.prepare_runtime_paths()
        yield

    app = FastAPI(
        title="VeriClose API",
        version="0.1.0",
        description="Evidence-first settlement-to-ERP reconciliation controller.",
        lifespan=lifespan,
        docs_url=None if hosted else "/docs",
        redoc_url=None if hosted else "/redoc",
        openapi_url=None if hosted else "/openapi.json",
    )
    app.state.container = container
    app.include_router(health_router)
    app.include_router(workflow_router)
    _install_error_handlers(app)
    _mount_frontend(app, container)
    return app


def _install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(WorkflowError)
    async def workflow_error(_request: Request, error: WorkflowError) -> JSONResponse:
        return JSONResponse(
            status_code=error.http_status,
            content={
                "error": {
                    "code": error.code,
                    "message": error.message,
                    "field": None,
                    "suggested_fix": error.suggested_fix,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_error(
        _request: Request, error: RequestValidationError
    ) -> JSONResponse:
        first = error.errors()[0]
        location = ".".join(str(item) for item in first.get("loc", ())[1:]) or None
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "REQUEST_VALIDATION_FAILED",
                    "message": first.get("msg", "Invalid request"),
                    "field": location,
                    "suggested_fix": "Correct the request field and retry",
                }
            },
        )

    @app.exception_handler(LookupError)
    async def lookup_error(_request: Request, error: LookupError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "code": "RESOURCE_NOT_FOUND",
                    "message": str(error),
                    "field": None,
                    "suggested_fix": "Check the run or case identifier",
                }
            },
        )

    @app.exception_handler(ValueError)
    async def value_error(_request: Request, error: ValueError) -> JSONResponse:
        hosted = _request.app.state.container.settings.environment == "hosted-demo"
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": {
                    "code": "WORKFLOW_CONFLICT",
                    "message": (
                        "The request conflicts with the current workflow state"
                        if hosted
                        else str(error)
                    ),
                    "field": None,
                    "suggested_fix": "Inspect validation state and supplied confirmations",
                }
            },
        )


def _mount_frontend(app: FastAPI, container: AppContainer) -> None:
    static_dir = container.settings.static_dir
    index_path = static_dir / "index.html"
    assets_dir = static_dir / "assets"

    if not index_path.is_file():

        @app.get("/", include_in_schema=False)
        async def development_root() -> dict[str, str]:
            return {
                "app": "VeriClose",
                "status": "API ready; run the Vite development server for the web UI.",
                "health": "/health/ready",
                "docs": "/docs",
            }

        return

    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="web-assets")

    @app.get("/", include_in_schema=False)
    async def production_root() -> FileResponse:
        return FileResponse(index_path)

    @app.get("/{requested_path:path}", include_in_schema=False)
    async def spa_fallback(requested_path: str) -> FileResponse:
        if requested_path.startswith(("api/", "health/")):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        candidate = (static_dir / requested_path).resolve()
        static_root = static_dir.resolve()
        if candidate.is_file() and candidate.is_relative_to(static_root):
            return FileResponse(candidate)
        return FileResponse(index_path)


app = create_app()
