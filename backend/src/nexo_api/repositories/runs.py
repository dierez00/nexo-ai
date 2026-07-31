"""Repositorio de runs."""

from __future__ import annotations

from typing import Any

from sqlalchemy import RowMapping, text

from nexo_api.repositories._base import dump_json, read_session, uow

_GET_COLS = "id, trace_id, status, domain, latency_ms, total_cost_usd, metadata, created_at"


async def create(tenant_id: int, conversation_id: int | None, trace_id: str) -> RowMapping:
    sql = text("""
        insert into public.runs (tenant_id, conversation_id, trace_id, status)
        values (:tenant_id, :conversation_id, :trace_id, 'running')
        returning id, trace_id, created_at
    """)
    async with uow() as session:
        result = await session.execute(
            sql,
            {"tenant_id": tenant_id, "conversation_id": conversation_id, "trace_id": trace_id},
        )
        return result.mappings().one()


async def finalize(
    tenant_id: int,
    run_id: int,
    status: str,
    domain: str | None,
    metadata: dict[str, Any],
    latency_ms: int,
    total_cost_usd: float,
) -> None:
    sql = text("""
        update public.runs set
            status = :status,
            domain = :domain,
            latency_ms = :latency_ms,
            total_cost_usd = :total_cost_usd,
            metadata = cast(:metadata as jsonb)
        where id = :id and tenant_id = :tenant_id
    """)
    async with uow() as session:
        await session.execute(
            sql,
            {
                "id": run_id,
                "tenant_id": tenant_id,
                "status": status,
                "domain": domain,
                "latency_ms": latency_ms,
                "total_cost_usd": total_cost_usd,
                "metadata": dump_json(metadata),
            },
        )


async def get(tenant_id: int, run_id: int) -> RowMapping | None:
    sql = text(f"select {_GET_COLS} from public.runs where id = :id and tenant_id = :tenant_id")
    async with read_session() as session:
        result = await session.execute(sql, {"id": run_id, "tenant_id": tenant_id})
        return result.mappings().first()
