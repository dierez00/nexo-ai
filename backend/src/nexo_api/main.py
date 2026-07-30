"""Punto de entrada de la API FastAPI.

Ejecutar en local:  python -m uvicorn nexo_api.main:app --reload --port 8000
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from nexo_observability.logging import configure_logging, get_logger

from nexo_api.api import health
from nexo_api.api.v1 import auth as auth_router
from nexo_api.api.v1 import conversations as conversations_router
from nexo_api.api.v1 import runs as runs_router
from nexo_api.core.config import get_settings
from nexo_api.core.db import dispose_engine
from nexo_api.core.errors import ProblemException, problem_exception_handler
from nexo_api.core.middleware import TraceIdMiddleware

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    log.info("app.startup", app_env=settings.app_env)
    try:
        yield
    finally:
        await dispose_engine()
        log.info("app.shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="nexo-ai API",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Orden de middlewares: el trace_id envuelve todo para estar disponible
    # en cualquier log posterior.
    app.add_middleware(TraceIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.public_base_url, "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Trace-Id"],
    )

    app.add_exception_handler(ProblemException, problem_exception_handler)  # type: ignore[arg-type]

    app.include_router(health.router)
    app.include_router(auth_router.router)
    app.include_router(conversations_router.router)
    app.include_router(runs_router.router)
    return app


app = create_app()
