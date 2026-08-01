"""Repositorio de runs."""

from __future__ import annotations

from typing import Any

from sqlalchemy import RowMapping, text

from nexo_api.repositories._base import dump_json, read_session, uow

_GET_COLS = "id, trace_id, status, domain, latency_ms, total_cost_usd, metadata, created_at"
_LIST_COLS = "id, trace_id, status, domain, latency_ms, total_cost_usd, created_at"


async def create(
    tenant_id: int, conversation_id: int | None, trace_id: str, *, status: str = "queued"
) -> RowMapping:
    sql = text("""
        insert into public.runs (tenant_id, conversation_id, trace_id, status)
        values (:tenant_id, :conversation_id, :trace_id, :status)
        returning id, trace_id, created_at
    """)
    async with uow() as session:
        result = await session.execute(
            sql,
            {
                "tenant_id": tenant_id,
                "conversation_id": conversation_id,
                "trace_id": trace_id,
                "status": status,
            },
        )
        return result.mappings().one()


async def set_status(tenant_id: int, run_id: int, status: str) -> None:
    sql = text("update public.runs set status = :status where id = :id and tenant_id = :tenant_id")
    async with uow() as session:
        await session.execute(sql, {"id": run_id, "tenant_id": tenant_id, "status": status})


async def get_status(run_id: int) -> str | None:
    sql = text("select status from public.runs where id = :id")
    async with read_session() as session:
        row = (await session.execute(sql, {"id": run_id})).mappings().first()
        return str(row["status"]) if row is not None else None


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


async def list_by_tenant(
    tenant_id: int,
    *,
    conversation_id: int | None,
    domain: str | None,
    status: str | None,
    limit: int,
) -> list[RowMapping]:
    """Runs más recientes del tenant, para "mis trámites" (`GET /runs`).

    Sin `metadata` a propósito: el listado es un resumen liviano, no el
    snapshot completo que ya sirve `GET /runs/{id}`.
    """
    sql = text(f"""
        select {_LIST_COLS} from public.runs
        where tenant_id = :tenant_id
          and (cast(:conversation_id as bigint) is null or conversation_id = :conversation_id)
          and (cast(:domain as text) is null or domain = :domain)
          and (cast(:status as text) is null or status = :status)
        order by id desc
        limit :limit
    """)
    async with read_session() as session:
        result = await session.execute(
            sql,
            {
                "tenant_id": tenant_id,
                "conversation_id": conversation_id,
                "domain": domain,
                "status": status,
                "limit": limit,
            },
        )
        return list(result.mappings().all())
