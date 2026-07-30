"""Repositorio de eventos de run (append-only, secuenciados por id)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sqlalchemy import RowMapping, text

from nexo_api.repositories._base import dump_json, read_session, uow


async def bulk_create(
    run_id: int, trace_id: str, events: Sequence[tuple[str, str, dict[str, Any]]]
) -> None:
    """events: secuencia de (event_type, node_name, payload)."""
    sql = text("""
        insert into public.run_events (run_id, trace_id, event_type, node_name, payload)
        values (:run_id, :trace_id, :event_type, :node_name, cast(:payload as jsonb))
    """)
    async with uow() as session:
        for event_type, node_name, payload in events:
            await session.execute(
                sql,
                {
                    "run_id": run_id,
                    "trace_id": trace_id,
                    "event_type": event_type,
                    "node_name": node_name,
                    "payload": dump_json(payload),
                },
            )


async def list_after(run_id: int, after_id: int = 0) -> list[RowMapping]:
    """Eventos del run con id > after_id (para SSE reanudable por Last-Event-ID)."""
    sql = text("""
        select id, trace_id, event_type, node_name, payload, created_at
        from public.run_events
        where run_id = :run_id and id > :after_id
        order by id asc
    """)
    async with read_session() as session:
        result = await session.execute(sql, {"run_id": run_id, "after_id": after_id})
        return list(result.mappings().all())
