"""Los dobles y los adapters futuros comparten contrato (`DIE-F0-030`, gate §7.9).

El objetivo de un puerto es que sustituir su implementación no cambie ningún
caso de uso. Aquí se verifica lo que se puede verificar hoy: que cada doble
satisface estructuralmente su `Protocol`, que el grafo depende solo del
protocolo y que la tabla `doble ↔ adapter real` está completa y publicada.
"""

from __future__ import annotations

import inspect

import pytest

from nexo_mcp.ports import ToolExecutorPort, ToolRegistryPort
from nexo_mcp.testing import InMemoryToolExecutor, InMemoryToolRegistry
from nexo_orchestration.ports import (
    ChatModelPort,
    CheckpointStorePort,
    Clock,
    EventSinkPort,
    IdFactory,
)
from nexo_orchestration.testing import (
    FakeChatModel,
    FrozenClock,
    InMemoryCheckpointStore,
    InMemoryEventSink,
    SequentialIdFactory,
)
from nexo_rag.ports import ChunkRepositoryPort, EmbeddingsPort, RetrieverPort
from nexo_rag.testing import (
    DeterministicEmbeddings,
    InMemoryChunkRepository,
    InMemoryRetriever,
)

pytestmark = pytest.mark.contract

# Cada puerto de `DIE-F0-021`, su doble de Fase 0 y el adapter que lo sustituirá.
# La tercera columna es un compromiso de diseño, no código: documenta quién
# implementará el puerto y en qué fase.
PORT_MATRIX: list[tuple[str, type, object, str]] = [
    ("chat model", ChatModelPort, FakeChatModel(), "gateway de proveedor (F1.1, Diego/Dani)"),
    ("embeddings", EmbeddingsPort, DeterministicEmbeddings(), "adapter de embeddings (F1.2)"),
    ("retriever", RetrieverPort, InMemoryRetriever(), "PostgreSQL FTS + pgvector (F1.3, Daher)"),
    (
        "chunk repository",
        ChunkRepositoryPort,
        InMemoryChunkRepository(),
        "repositorio SQLAlchemy (F1.2, Daher)",
    ),
    ("tool registry", ToolRegistryPort, InMemoryToolRegistry(), "MCP registry (F1.8)"),
    (
        "tool executor",
        ToolExecutorPort,
        InMemoryToolExecutor(InMemoryToolRegistry()),
        "MCP server + adapters (F1.8, Diego/Dani)",
    ),
    (
        "checkpoint store",
        CheckpointStorePort,
        InMemoryCheckpointStore(),
        "checkpoints en PostgreSQL (F1.11, Daher)",
    ),
    ("event sink", EventSinkPort, InMemoryEventSink(), "event store + SSE (F1.11, Dani)"),
    ("clock", Clock, FrozenClock(), "reloj del sistema (F1)"),
    ("id factory", IdFactory, SequentialIdFactory(), "generador ULID (F1)"),
]


@pytest.mark.parametrize(
    ("name", "port", "double", "adapter"), PORT_MATRIX, ids=lambda item: str(item)[:40]
)
def test_double_satisfies_its_port(name, port, double, adapter) -> None:
    assert isinstance(double, port), (
        f"el doble de {name} no satisface {port.__name__}; sustituirlo por "
        f"{adapter} rompería el caso de uso"
    )


def test_every_declared_port_appears_in_the_matrix() -> None:
    """Un puerto nuevo sin doble ni adapter previsto es un hueco de Fase 0."""
    declared = {
        ChatModelPort,
        EmbeddingsPort,
        RetrieverPort,
        ChunkRepositoryPort,
        ToolRegistryPort,
        ToolExecutorPort,
        CheckpointStorePort,
        EventSinkPort,
        Clock,
        IdFactory,
    }
    covered = {port for _, port, _, _ in PORT_MATRIX}
    assert declared == covered


@pytest.mark.parametrize(
    ("name", "port", "double", "adapter"), PORT_MATRIX, ids=lambda item: str(item)[:40]
)
def test_double_implements_every_port_method(name, port, double, adapter) -> None:
    """`isinstance` sobre un Protocol no comprueba firmas; esto sí las enumera."""
    expected = {
        attribute
        for attribute in dir(port)
        if not attribute.startswith("_") and attribute not in {"mro"}
    }
    missing = [attribute for attribute in expected if not hasattr(double, attribute)]
    assert not missing, f"al doble de {name} le faltan miembros del puerto: {missing}"


def test_the_graph_depends_only_on_protocols() -> None:
    """El grafo no puede nombrar un doble concreto en su firma."""
    from nexo_orchestration.graph import MinimalGraph

    annotations = inspect.get_annotations(MinimalGraph, eval_str=False)
    concrete = {
        "FakeChatModel",
        "InMemoryEventSink",
        "InMemoryCheckpointStore",
        "FrozenClock",
        "SequentialIdFactory",
    }
    offenders = [
        f"{field}: {annotation}"
        for field, annotation in annotations.items()
        if str(annotation) in concrete
    ]
    assert not offenders, f"el grafo depende de implementaciones concretas: {offenders}"


def test_ports_carry_documentation() -> None:
    """Un puerto sin docstring no comunica su contrato a quien lo implemente."""
    undocumented = [port.__name__ for _, port, _, _ in PORT_MATRIX if not port.__doc__]
    assert not undocumented
