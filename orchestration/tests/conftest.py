"""Fixtures compartidas de la orquestación.

Todas las dependencias son dobles en memoria con reloj e IDs congelados: ninguna
prueba de este paquete abre red, base de datos ni credenciales.
"""

from __future__ import annotations

import pytest

from nexo_contracts import Channel, Identity, RunRequest
from nexo_contracts.config import PoliciesConfig
from nexo_orchestration.configuration import load_config
from nexo_orchestration.graph import MinimalGraph
from nexo_orchestration.testing import (
    FakeChatModel,
    FrozenClock,
    InMemoryCheckpointStore,
    InMemoryEventSink,
    Scenario,
    SequentialIdFactory,
)


@pytest.fixture
def clock() -> FrozenClock:
    return FrozenClock()


@pytest.fixture
def ids() -> SequentialIdFactory:
    return SequentialIdFactory()


@pytest.fixture
def event_sink() -> InMemoryEventSink:
    return InMemoryEventSink()


@pytest.fixture
def checkpoints() -> InMemoryCheckpointStore:
    return InMemoryCheckpointStore()


@pytest.fixture
def policies() -> PoliciesConfig:
    return load_config().policies


@pytest.fixture
def model() -> FakeChatModel:
    """Modelo falso que clasifica correctamente en el camino feliz."""
    return FakeChatModel(
        {"classify_request": Scenario(data={"domain": "vehiculos", "confidence": 0.91})}
    )


@pytest.fixture
def graph(
    model: FakeChatModel,
    event_sink: InMemoryEventSink,
    checkpoints: InMemoryCheckpointStore,
    clock: FrozenClock,
    ids: SequentialIdFactory,
    policies: PoliciesConfig,
) -> MinimalGraph:
    return MinimalGraph(
        model=model,
        event_sink=event_sink,
        checkpoints=checkpoints,
        clock=clock,
        ids=ids,
        policies=policies,
    )


@pytest.fixture
def request_factory(clock: FrozenClock):
    def build(**overrides) -> RunRequest:
        payload = {
            "run_id": "run_000001",
            "trace_id": "trace_000001",
            "conversation_id": "conv_000001",
            "user_message": "Quiero renovar mi licencia y saber si debo algo",
            "channel": Channel.WEB,
            "identity": Identity(
                user_id="usr_demo",
                institution_id="inst_demo",
                roles=["citizen"],
                permissions=["domain:vehiculos:read"],
            ),
            "received_at": clock.now(),
        }
        payload.update(overrides)
        return RunRequest(**payload)

    return build
