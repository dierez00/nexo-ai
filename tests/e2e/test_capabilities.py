"""Consulta de ayuda derivada del catálogo activo, sin modelo ni RAG."""

from __future__ import annotations

import pytest

from nexo_contracts import Domain, RunStatus

from .runtime import build_runtime, citizen_request

pytestmark = pytest.mark.e2e


@pytest.mark.parametrize(
    "message",
    ["¿Qué sabes hacer?", "Que puedes hacer", "¿Qué trámites atiendes?"],
)
async def test_capabilities_query_uses_the_catalog_without_model_or_rag(message: str) -> None:
    runtime = await build_runtime(scenarios={})

    result = await runtime.graph.invoke(citizen_request(message))

    assert result.status is RunStatus.SUCCEEDED
    assert result.answer is not None
    assert result.error is None
    assert result.sources == []
    assert result.surface is None
    assert result.metrics.model_invocation_count == 0
    assert result.metrics.retrieval_count == 0
    assert "fuera de alcance" not in " ".join(result.warnings).lower()
    for domain in Domain:
        assert runtime.manifests[domain].title in result.answer

    event_types = runtime.events.types("run_000001")
    assert "model.selected" not in event_types
    assert "rag.started" not in event_types
    assert "rag.completed" not in event_types
