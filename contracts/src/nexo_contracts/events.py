"""Contrato de eventos (§5.8).

Todo evento lleva `event_id`, `trace_id`, `run_id`, `sequence`, timestamp UTC,
actor, status y datos minimizados. La secuencia es estrictamente monotónica por
run: es lo que permite reconstruir un workflow, reconectar un SSE desde una
posición conocida y reproducir una ejecución sin ambigüedad.
"""

from __future__ import annotations

from typing import Annotated, Self

from pydantic import Field, model_validator

from .base import FrozenNexoModel, NexoModel
from .enums import ActorType, EventStatus, EventType, EventVisibility
from .errors import NormalizedError
from .ids import EventId, RunId, TraceId
from .primitives import PositiveMillis, UtcDatetime
from .safety import SafePayload


class EventActor(FrozenNexoModel):
    """Quién produjo el evento."""

    type: ActorType
    name: str = Field(max_length=120)


class RunEvent(FrozenNexoModel):
    """Evento inmutable de la traza de un run (§5.8).

    `data` es un payload minimizado y seguro: nunca transporta prompts
    completos, secretos ni PII directa (lo hace cumplir `SafePayload`).
    """

    event_id: EventId
    trace_id: TraceId
    run_id: RunId
    sequence: int = Field(ge=1, description="Posición 1-indexada dentro del run.")
    type: EventType
    timestamp: UtcDatetime
    actor: EventActor
    status: EventStatus
    visibility: EventVisibility = EventVisibility.PUBLIC
    correlation_id: str = Field(max_length=120)
    parent_event_id: EventId | None = None
    duration_ms: PositiveMillis | None = None
    # El default vive dentro de `SafePayload`, pero repetirlo aquí lo hace
    # visible para quien lee el contrato y para el análisis estático.
    data: SafePayload = Field(default_factory=dict)
    public_data: SafePayload = Field(
        default_factory=dict,
        description="Proyección minimizada para workflow público; `data` queda para auditoría.",
    )
    error: NormalizedError | None = None
    policy_version: str | None = Field(
        default=None,
        max_length=40,
        description="Versión de políticas vigente, propagada a evaluaciones (`DIE-F0-037`).",
    )
    catalog_version: str | None = Field(
        default=None,
        max_length=80,
        description="Snapshot del catálogo central usado para decidir este run (`DIE-F2-008`).",
    )
    skill_id: str | None = Field(default=None, max_length=80)
    skill_version: str | None = Field(default=None, max_length=40)

    @model_validator(mode="after")
    def _failures_carry_an_error(self) -> Self:
        if self.status is EventStatus.FAILED and self.error is None:
            raise ValueError(
                f"el evento {self.type.value!r} tiene estado 'failed' sin error normalizado; "
                f"un fallo sin código no es reconstruible"
            )
        if self.status is EventStatus.SUCCEEDED and self.error is not None:
            raise ValueError(
                f"el evento {self.type.value!r} tiene estado 'succeeded' y transporta un error"
            )
        return self


class EventSequence(NexoModel):
    """Secuencia completa de eventos de un run, con su invariante de orden.

    Se valida como contrato y no solo en el sink: un replay que recibe eventos
    desordenados o con huecos debe fallar de forma visible en vez de dibujar un
    workflow incorrecto.
    """

    run_id: RunId
    events: Annotated[list[RunEvent], Field(max_length=10_000)] = Field(default_factory=list)

    @model_validator(mode="after")
    def _sequence_is_strictly_monotonic(self) -> Self:
        expected = 1
        for event in self.events:
            if event.run_id != self.run_id:
                raise ValueError(
                    f"el evento {event.event_id!r} pertenece al run {event.run_id!r}, "
                    f"no a {self.run_id!r}"
                )
            if event.sequence != expected:
                raise ValueError(
                    f"secuencia rota en {event.event_id!r}: se esperaba {expected} y llegó "
                    f"{event.sequence}; la secuencia por run es estrictamente monotónica y sin "
                    f"huecos"
                )
            expected += 1
        return self

    @property
    def last_sequence(self) -> int:
        return self.events[-1].sequence if self.events else 0

    def since(self, sequence: int) -> tuple[RunEvent, ...]:
        """Eventos posteriores a una posición conocida, para reconexión de SSE."""
        return tuple(event for event in self.events if event.sequence > sequence)
