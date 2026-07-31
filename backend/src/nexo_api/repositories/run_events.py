"""Repositorio de eventos de run (append-only, secuenciados por contrato)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sqlalchemy import RowMapping, text

from nexo_contracts import RunEvent

from nexo_api.repositories._base import dump_json, read_session, uow


async def bulk_create(run_id: int, trace_id: str, events: Sequence[RunEvent]) -> None:
    """Persiste `RunEvent` canónicos y su proyección expandida para consultas SSE."""
    sql = text("""
        insert into public.run_events (
          run_id, trace_id, event_type, node_name, payload,
          event_id, sequence, actor_type, actor_name, status, visibility,
          correlation_id, parent_event_id, duration_ms, public_data, error,
          policy_version, catalog_version, skill_id, skill_version, canonical_event
        )
        values (
          :run_id, :trace_id, :event_type, :node_name, cast(:payload as jsonb),
          :event_id, :sequence, :actor_type, :actor_name, :status, :visibility,
          :correlation_id, :parent_event_id, :duration_ms, cast(:public_data as jsonb),
          cast(:error as jsonb), :policy_version, :catalog_version, :skill_id,
          :skill_version, cast(:canonical_event as jsonb)
        )
    """)
    async with uow() as session:
        for event in events:
            await session.execute(
                sql,
                {
                    "run_id": run_id,
                    "trace_id": trace_id,
                    "event_type": event.type.value,
                    "node_name": _node_name(event),
                    "payload": dump_json(event.data),
                    "event_id": event.event_id,
                    "sequence": event.sequence,
                    "actor_type": event.actor.type.value,
                    "actor_name": event.actor.name,
                    "status": event.status.value,
                    "visibility": event.visibility.value,
                    "correlation_id": event.correlation_id,
                    "parent_event_id": event.parent_event_id,
                    "duration_ms": event.duration_ms,
                    "public_data": dump_json(event.public_data),
                    "error": dump_json(event.error.model_dump(mode="json"))
                    if event.error is not None
                    else None,
                    "policy_version": event.policy_version,
                    "catalog_version": event.catalog_version,
                    "skill_id": event.skill_id,
                    "skill_version": event.skill_version,
                    "canonical_event": event.model_dump_json(),
                },
            )


async def list_after(run_id: int, after_sequence: int = 0) -> list[RowMapping]:
    """Eventos del run con `sequence` > after_sequence, para reconexión SSE."""
    sql = text("""
        select
          id, trace_id, event_type, node_name, payload, created_at,
          event_id, sequence, actor_type, actor_name, status, visibility,
          correlation_id, parent_event_id, duration_ms, public_data, error,
          policy_version, catalog_version, skill_id, skill_version, canonical_event
        from public.run_events
        where run_id = :run_id
          and coalesce(sequence, id) > :after_sequence
        order by coalesce(sequence, id) asc
    """)
    async with read_session() as session:
        result = await session.execute(
            sql, {"run_id": run_id, "after_sequence": after_sequence}
        )
        return list(result.mappings().all())


def _node_name(event: RunEvent) -> str:
    node = event.data.get("node")
    return node if isinstance(node, str) and node else event.actor.name
