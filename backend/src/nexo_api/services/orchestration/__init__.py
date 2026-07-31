"""Orquestación — puerto e implementación fake (intercambiable por Diego)."""

from __future__ import annotations

from nexo_api.services.orchestration.assembly import (
    GraphAssembly,
    build_graph_deps,
    resolve_model_backend,
)
from nexo_api.services.orchestration.fake import FakeOrchestrator
from nexo_api.services.orchestration.port import Orchestrator, PendingActionSink
from nexo_api.services.orchestration.real import RealOrchestrator

__all__ = [
    "FakeOrchestrator",
    "GraphAssembly",
    "Orchestrator",
    "PendingActionSink",
    "RealOrchestrator",
    "build_graph_deps",
    "resolve_model_backend",
]
