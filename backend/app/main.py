"""SignalGate FastAPI Main Application

Production-structured API serving fraud triage ML pipeline, frozen policy decisions,
evaluation benchmarks, replay streams, and audit logs to the frontend dashboard.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.config import settings
from backend.app.schemas import ErrorDetail, ErrorResponse
from backend.app.routers import (
    audit,
    cases,
    governance,
    health,
    modes,
    overview,
    policies,
    replay,
    scoring,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan event handler: safely initialize resources and pre-warm model cache without fitting."""
    # Pre-cache model pipeline in memory so cold-start disk I/O does not degrade initial scoring latency
    from backend.app.dependencies import get_artifact_service
    try:
        get_artifact_service().get_model_pipeline()
    except Exception:
        pass
    yield
    # Cleanup logic on shutdown if needed


def create_app() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title=settings.project_name,
        version=settings.version,
        description=(
            "Real-time fraud triage decision API exposing calibrated gradient boosting, "
            "epistemic disagreement ensembles, capacity governance, and shift evaluation metrics."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # 1. Strict CORS Middleware for local React development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # 2. Consistent Structured Error Handlers
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        detail = exc.detail
        if isinstance(detail, dict):
            code = detail.get("code", "HTTP_ERROR")
            message = detail.get("message", "An error occurred.")
            details = detail.get("details", {})
        else:
            code = "HTTP_ERROR"
            message = str(detail)
            details = {}

        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": code, "message": message, "details": details}},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = exc.errors()
        clean_errors = []
        for err in errors:
            clean_err = {
                "type": str(err.get("type", "value_error")),
                "loc": [str(x) for x in err.get("loc", [])],
                "msg": str(err.get("msg", "Validation error")),
            }
            if "ctx" in err and isinstance(err["ctx"], dict):
                clean_err["ctx"] = {str(k): str(v) for k, v in err["ctx"].items()}
            clean_errors.append(clean_err)

        message = clean_errors[0]["msg"] if clean_errors else "Validation error"
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": message,
                    "details": {"validation_errors": clean_errors},
                }
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected internal server error occurred.",
                    "details": {},
                }
            },
        )

    # 3. Mount Routers under API prefix (/api)
    api_prefix = settings.api_prefix
    app.include_router(health.router, prefix=api_prefix)
    app.include_router(overview.router, prefix=api_prefix)
    app.include_router(policies.router, prefix=api_prefix)
    app.include_router(cases.router, prefix=api_prefix)
    app.include_router(replay.router, prefix=api_prefix)
    app.include_router(audit.router, prefix=api_prefix)
    app.include_router(scoring.router, prefix=api_prefix)
    app.include_router(modes.router, prefix=api_prefix)
    app.include_router(governance.router, prefix=api_prefix)

    return app


app = create_app()
