"""Caso de uso: métricas operativas por tenant y ventana."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from nexo_api.repositories import metrics as metrics_repo
from nexo_api.schemas.auth import UserProfile
from nexo_api.schemas.metric import CountByStatus, MetricSet, MetricWindow, RunMetricsSummary

_DEFAULT_WINDOW_DAYS = 7


async def get_metrics(
    user: UserProfile, start: datetime | None = None, end: datetime | None = None
) -> MetricSet:
    now = datetime.now(UTC)
    window_end = end or now
    window_start = start or (window_end - timedelta(days=_DEFAULT_WINDOW_DAYS))

    data = await metrics_repo.collect(int(user.tenant_id), window_start, window_end)
    return MetricSet(
        window=MetricWindow(start=window_start, end=window_end),
        runs=RunMetricsSummary(**data["runs"]),
        conversations_total=data["conversations_total"],
        actions=CountByStatus(**data["actions"]),
        appointments=CountByStatus(**data["appointments"]),
        generated_at=now,
    )
