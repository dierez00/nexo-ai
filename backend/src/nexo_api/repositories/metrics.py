"""Agregados de métricas (tenant-scoped, por ventana temporal)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from nexo_api.repositories._base import read_session

_WINDOW = "tenant_id = :tenant_id and created_at >= :start and created_at < :end"


async def _by_status(session: AsyncSession, table: str, params: dict[str, Any]) -> dict[str, Any]:
    rows = (
        (
            await session.execute(
                text(
                    f"select status, count(*) as c from public.{table} "
                    f"where {_WINDOW} group by status"
                ),
                params,
            )
        )
        .mappings()
        .all()
    )
    by_status = {str(r["status"]): int(r["c"]) for r in rows}
    return {"total": sum(by_status.values()), "by_status": by_status}


async def collect(tenant_id: int, start: datetime, end: datetime) -> dict[str, Any]:
    params = {"tenant_id": tenant_id, "start": start, "end": end}
    async with read_session() as session:
        run_totals = (
            (
                await session.execute(
                    text(
                        "select count(*) as total, coalesce(avg(latency_ms), 0) as avg_latency, "
                        f"coalesce(sum(total_cost_usd), 0) as cost from public.runs where {_WINDOW}"
                    ),
                    params,
                )
            )
            .mappings()
            .one()
        )
        run_status_rows = (
            (
                await session.execute(
                    text(
                        f"select status, count(*) as c from public.runs "
                        f"where {_WINDOW} group by status"
                    ),
                    params,
                )
            )
            .mappings()
            .all()
        )
        run_domain_rows = (
            (
                await session.execute(
                    text(
                        "select coalesce(domain, 'unknown') as domain, count(*) as c "
                        f"from public.runs where {_WINDOW} group by domain"
                    ),
                    params,
                )
            )
            .mappings()
            .all()
        )
        conversations_total = int(
            await session.scalar(
                text(f"select count(*) from public.conversations where {_WINDOW}"), params
            )
            or 0
        )
        actions = await _by_status(session, "actions", params)
        appointments = await _by_status(session, "appointments", params)

    return {
        "runs": {
            "total": int(run_totals["total"]),
            "avg_latency_ms": float(run_totals["avg_latency"]),
            "total_cost_usd": float(run_totals["cost"]),
            "by_status": {str(r["status"]): int(r["c"]) for r in run_status_rows},
            "by_domain": {str(r["domain"]): int(r["c"]) for r in run_domain_rows},
        },
        "conversations_total": conversations_total,
        "actions": actions,
        "appointments": appointments,
    }


async def collect_runs_trend(
    tenant_id: int,
    start: datetime,
    end: datetime,
) -> list[dict[str, Any]]:
    """Serie diaria de runs para superficies admin A2UI."""
    params = {"tenant_id": tenant_id, "start": start, "end": end}
    async with read_session() as session:
        rows = (
            (
                await session.execute(
                    text(
                        "select date_trunc('day', created_at)::date as day, "
                        "count(*) as total, "
                        "count(*) filter (where status in ('succeeded', 'partial')) as succeeded "
                        f"from public.runs where {_WINDOW} group by 1 order by 1"
                    ),
                    params,
                )
            )
            .mappings()
            .all()
        )
    return [
        {
            "date": row["day"].isoformat(),
            "total": int(row["total"]),
            "succeeded": int(row["succeeded"]),
        }
        for row in rows
    ]
