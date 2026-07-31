"""Persistencia append-only de ``RunEvent`` canónicos."""

from __future__ import annotations

from sqlalchemy import RowMapping, text

from nexo_api.repositories._base import dump_json, load_json, read_session, uow
from nexo_contracts import ActorType, EventActor, EventStatus, EventType, NormalizedError, RunEvent


async def create(event: RunEvent) -> RowMapping:
    sql = text("""
        insert into public.run_events
            (run_id, trace_id, event_id, sequence, event_type, actor_type,
             actor_name, event_status, duration_ms, payload, error, policy_version)
        values
            (:run_id, :trace_id, :event_id, :sequence, :event_type, :actor_type,
             :actor_name, :event_status, :duration_ms, cast(:payload as jsonb),
             cast(:error as jsonb), :policy_version)
        returning event_id, sequence, trace_id, event_type, actor_type, actor_name,
                  event_status, duration_ms, payload, error, policy_version, created_at
    """)
    async with uow() as session:
        result = await session.execute(
            sql,
            {
                "run_id": int(str(event.run_id).removeprefix("run_")),
                "trace_id": event.trace_id,
                "event_id": event.event_id,
                "sequence": event.sequence,
                "event_type": event.type.value,
                "actor_type": event.actor.type.value,
                "actor_name": event.actor.name,
                "event_status": event.status.value,
                "duration_ms": event.duration_ms,
                "payload": dump_json(event.data),
                "error": dump_json(event.error.model_dump(mode="json")) if event.error else None,
                "policy_version": event.policy_version,
            },
        )
        return result.mappings().one()


async def list_after(run_id: int, after_sequence: int = 0) -> list[RowMapping]:
    sql = text("""
        select event_id, sequence, trace_id, event_type, actor_type, actor_name,
               event_status, duration_ms, payload, error, policy_version, created_at
        from public.run_events
        where run_id = :run_id and sequence > :after_sequence
        order by sequence asc
    """)
    async with read_session() as session:
        result = await session.execute(sql, {"run_id": run_id, "after_sequence": after_sequence})
        return list(result.mappings().all())


async def last_sequence(run_id: int) -> int:
    async with read_session() as session:
        value = await session.scalar(
            text("select coalesce(max(sequence), 0) from public.run_events where run_id = :run_id"),
            {"run_id": run_id},
        )
        return int(value or 0)


def to_contract(row: RowMapping, run_id: str) -> RunEvent:
    error = load_json(row["error"])
    return RunEvent(
        event_id=str(row["event_id"]),
        run_id=run_id,
        trace_id=str(row["trace_id"]),
        sequence=int(row["sequence"]),
        type=EventType(str(row["event_type"])),
        timestamp=row["created_at"],
        actor=EventActor(type=ActorType(str(row["actor_type"])), name=str(row["actor_name"])),
        status=EventStatus(str(row["event_status"])),
        # La tabla aún no persiste correlation_id; la convención canónica es
        # correlation_id = trace_id (persistir los campos extendidos requiere
        # una migración de Daher: TODO paridad total de RunEvent).
        correlation_id=str(row["trace_id"]),
        duration_ms=row["duration_ms"],
        data=load_json(row["payload"]) or {},
        error=NormalizedError.model_validate(error) if error else None,
        policy_version=row["policy_version"],
    )
