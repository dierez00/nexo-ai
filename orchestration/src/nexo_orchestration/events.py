"""Emisión de eventos con secuencia derivada del estado (`DIE-F0-040`).

La `sequence` sale de `RunState.event_cursor`, no de un contador del emisor. Es
lo que permite reanudar desde un checkpoint sin repetir ni saltar posiciones: el
cursor viaja con el estado, y el estado es lo que se persiste.
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import JsonValue

from nexo_contracts import (
    ActorType,
    EventActor,
    EventStatus,
    EventType,
    EventVisibility,
    NormalizedError,
    RunEvent,
    RunState,
)

from .ports.clock import Clock, IdFactory
from .ports.events import EventSinkPort


@dataclass
class EventEmitter:
    """Construye y publica eventos coherentes con el estado del run."""

    sink: EventSinkPort
    clock: Clock
    ids: IdFactory
    policy_version: str = "unset"

    async def emit(
        self,
        state: RunState,
        event_type: EventType,
        *,
        actor_type: ActorType,
        actor_name: str,
        status: EventStatus,
        data: dict[str, JsonValue] | None = None,
        public_data: dict[str, JsonValue] | None = None,
        visibility: EventVisibility = EventVisibility.PUBLIC,
        duration_ms: int | None = None,
        error: NormalizedError | None = None,
    ) -> RunState:
        """Publica un evento y devuelve el estado con el cursor avanzado.

        Devolver el estado en vez de mutarlo mantiene la regla de que ningún
        componente muta estado compartido (`DIE-F0-039`).
        """
        sequence = state.event_cursor + 1
        event_id = self.ids.new_id("evt")
        audit_data = data or {}
        event = RunEvent(
            event_id=event_id,
            trace_id=state.trace_id,
            run_id=state.run_id,
            sequence=sequence,
            type=event_type,
            timestamp=self.clock.now(),
            actor=EventActor(type=actor_type, name=actor_name),
            status=status,
            visibility=visibility,
            correlation_id=state.trace_id,
            parent_event_id=state.last_event_id,
            duration_ms=duration_ms,
            data=audit_data,
            public_data=public_data if public_data is not None else audit_data,
            error=error,
            policy_version=self.policy_version,
            catalog_version=state.catalog_version,
            skill_id=state.active_skill_id,
            skill_version=state.active_skill_version,
        )
        await self.sink.emit(event)
        return state.model_copy(update={"event_cursor": sequence, "last_event_id": event_id})

    async def node_started(self, state: RunState, node: str) -> RunState:
        return await self.emit(
            state,
            EventType.AGENT_STARTED,
            actor_type=ActorType.SUPERVISOR,
            actor_name=node,
            status=EventStatus.STARTED,
            data={"node": node},
        )

    async def node_completed(self, state: RunState, node: str, *, duration_ms: int) -> RunState:
        return await self.emit(
            state,
            EventType.AGENT_COMPLETED,
            actor_type=ActorType.SUPERVISOR,
            actor_name=node,
            status=EventStatus.SUCCEEDED,
            duration_ms=duration_ms,
            data={"node": node},
        )

    async def node_failed(
        self, state: RunState, node: str, error: NormalizedError, *, duration_ms: int
    ) -> RunState:
        return await self.emit(
            state,
            EventType.AGENT_FAILED,
            actor_type=ActorType.SUPERVISOR,
            actor_name=node,
            status=EventStatus.FAILED,
            duration_ms=duration_ms,
            data={"node": node},
            error=error,
        )

    async def node_skipped(self, state: RunState, node: str) -> RunState:
        """Reanudación: el nodo ya estaba confirmado y no se reejecuta."""
        return await self.emit(
            state,
            EventType.RUN_RESUMED,
            actor_type=ActorType.SUPERVISOR,
            actor_name=node,
            status=EventStatus.SKIPPED,
            data={"node": node, "reason": "already_completed"},
        )

    async def checkpoint_saved(self, state: RunState, node: str, checkpoint_id: str) -> RunState:
        return await self.emit(
            state,
            EventType.CHECKPOINT_SAVED,
            actor_type=ActorType.SYSTEM,
            actor_name="checkpoint_store",
            status=EventStatus.SUCCEEDED,
            data={"node": node, "checkpoint_id": checkpoint_id},
        )
