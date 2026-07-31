"""Punto de entrada de la API FastAPI.

Ejecutar en local:  python -m uvicorn nexo_api.main:app --reload --port 8000
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from nexo_observability.logging import configure_logging, get_logger

from nexo_api.api import health, webhooks
from nexo_api.api.v1 import actions as actions_router
from nexo_api.api.v1 import admin as admin_router
from nexo_api.api.v1 import appointments as appointments_router
from nexo_api.api.v1 import auth as auth_router
from nexo_api.api.v1 import conversations as conversations_router
from nexo_api.api.v1 import runs as runs_router
from nexo_api.api.v1 import voice as voice_router
from nexo_api.core.config import get_settings
from nexo_api.core.db import dispose_engine
from nexo_api.core.errors import ProblemException, problem_exception_handler
from nexo_api.core.middleware import TraceIdMiddleware
from nexo_api.repositories import idempotency as idempotency_repo
from nexo_api.services.orchestration import build_graph_deps
from nexo_api.services.runs.tasks import RunTaskManager

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    app.state.run_task_manager = RunTaskManager()
    app.state.graph_assembly = None
    if settings.orchestrator_profile == "real":
        # Ensamblar el grafo real una sola vez (carga corpus/agentes). Falla
        # rápido: un perfil `real` mal configurado no debe arrancar en silencio.
        app.state.graph_assembly = await build_graph_deps()
    log.info(
        "app.startup",
        app_env=settings.app_env,
        orchestrator_profile=settings.orchestrator_profile,
        model_backend=(
            app.state.graph_assembly.model_backend if app.state.graph_assembly is not None else None
        ),
    )
    if settings.app_env != "development":
        try:
            count = await idempotency_repo.mark_stale_processing_unknown(
                settings.idempotency_processing_ttl_seconds
            )
            if count:
                log.warning("idempotency.stale_records_marked_unknown", count=count)
        except Exception as exc:  # readiness informa DB; startup debe seguir disponible
            log.warning("idempotency.recovery_skipped", error=str(exc))
    try:
        yield
    finally:
        await app.state.run_task_manager.shutdown(settings.run_shutdown_grace_seconds)
        if app.state.graph_assembly is not None:
            await app.state.graph_assembly.aclose()
        await dispose_engine()
        log.info("app.shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="nexo-ai API",
        version="0.1.0",
        # NexoModel usa un serializador que filtra campos internos bajo un
        # contexto explícito. Para OpenAPI HTTP se publica el schema de
        # validación canónico, no el retorno dinámico de ese serializador.
        separate_input_output_schemas=False,
        summary="Gateway HTTP/SSE/webhooks del asistente institucional nexo-ai.",
        description=(
            "API del backend (Dani). Convenciones: JSON snake_case, UTC, IDs opacos "
            "(`conv_`, `run_`, `act_`, `apt_`), dinero en unidades menores. Los errores "
            "usan **Problem Details** (`type/code/status/retryable`); el frontend nunca "
            "parsea texto. Toda respuesta propaga `X-Trace-Id`. Auth = Supabase Auth "
            "(JWT bearer validado por JWKS)."
        ),
        openapi_tags=[
            {"name": "auth", "description": "Login y perfil."},
            {"name": "conversations", "description": "Conversaciones, mensajes y disparo de runs."},
            {"name": "runs", "description": "Snapshot de runs y stream SSE de eventos."},
            {"name": "actions", "description": "Confirmación de acciones con idempotencia."},
            {
                "name": "voice",
                "description": "Turno de voz síncrono (ElevenLabs Conversational AI).",
            },
            {"name": "appointments", "description": "Disponibilidad y holds de citas."},
            {"name": "admin", "description": "Métricas, catálogo y config (rol admin)."},
            {"name": "webhooks", "description": "Webhooks firmados de Twilio (WhatsApp)."},
            {"name": "health", "description": "Liveness y readiness."},
        ],
        lifespan=lifespan,
    )

    # Orden de middlewares: el trace_id envuelve todo para estar disponible
    # en cualquier log posterior.
    app.add_middleware(TraceIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.web_origin],
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
    app.include_router(actions_router.router)
    app.include_router(voice_router.router)
    app.include_router(appointments_router.router)
    app.include_router(admin_router.router)
    app.include_router(webhooks.router)
    return app


app = create_app()
