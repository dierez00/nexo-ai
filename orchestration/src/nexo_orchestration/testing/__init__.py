"""Dobles de prueba de la orquestación (`DIE-F0-021`–`DIE-F0-028`).

Se publican como parte del paquete, no como código de test, porque los demás
módulos y los recorridos E2E offline los consumen. Ninguno abre red, base de
datos ni credenciales.
"""

from .checkpoints import InMemoryCheckpointStore
from .clock import DEFAULT_EPOCH, FrozenClock, SequentialIdFactory
from .event_sink import InMemoryEventSink
from .fake_model import (
    FakeBehavior,
    FakeChatAdapter,
    FakeChatModel,
    FakeEmbeddingsAdapter,
    Scenario,
    ScenarioScript,
)

__all__ = [
    "DEFAULT_EPOCH",
    "FakeBehavior",
    "FakeChatAdapter",
    "FakeChatModel",
    "FakeEmbeddingsAdapter",
    "FrozenClock",
    "InMemoryCheckpointStore",
    "InMemoryEventSink",
    "Scenario",
    "ScenarioScript",
    "SequentialIdFactory",
]
