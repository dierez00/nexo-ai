"""Caso de uso: métricas operativas por tenant y ventana."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from nexo_a2ui import (
    ADMIN_ALLOWED_PROPERTIES,
    ADMIN_CATALOG,
    AdminAnalyticsData,
    AdminAnalyticsSurfaceBuilder,
    SurfaceValidator,
)
from nexo_api.core.errors import ProblemException
from nexo_api.repositories import metrics as metrics_repo
from nexo_api.schemas.auth import UserProfile
from nexo_api.schemas.metric import CountByStatus, MetricSet, MetricWindow, RunMetricsSummary
from nexo_contracts import A2UISurface, ErrorCode

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


async def build_chart_surface(
    user: UserProfile,
    prompt: str,
    start: datetime | None = None,
    end: datetime | None = None,
) -> A2UISurface:
    """Construye una superficie A2UI admin desde agregados autorizados."""
    now = datetime.now(UTC)
    window_end = end or now
    window_start = start or (window_end - timedelta(days=_DEFAULT_WINDOW_DAYS))
    tenant_id = int(user.tenant_id)

    data, trend = await _collect_chart_data(tenant_id, window_start, window_end)
    analytics = AdminAnalyticsData(
        window_start=window_start,
        window_end=window_end,
        runs_total=data["runs"]["total"],
        conversations_total=data["conversations_total"],
        avg_latency_ms=data["runs"]["avg_latency_ms"],
        total_cost_usd=data["runs"]["total_cost_usd"],
        runs_by_status=data["runs"]["by_status"],
        runs_by_domain=data["runs"]["by_domain"],
        actions_by_status=data["actions"]["by_status"],
        appointments_by_status=data["appointments"]["by_status"],
        runs_trend=trend,
    )
    surface = AdminAnalyticsSurfaceBuilder().build(
        prompt,
        analytics,
        surface_id="surf_admin_chart",
    )
    result = SurfaceValidator(
        catalog=ADMIN_CATALOG,
        allowed_properties=dict(ADMIN_ALLOWED_PROPERTIES),
    ).validate(surface)
    if not result.is_valid:
        raise ProblemException(
            code=ErrorCode.CONTRACT_INVALID,
            title="La superficie A2UI admin no validó",
            detail="El servidor rechazó la superficie antes de enviarla al cliente.",
            errors=[error.model_dump(mode="json") for error in result.errors],
        )
    return surface


async def _collect_chart_data(
    tenant_id: int,
    start: datetime,
    end: datetime,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    data = await metrics_repo.collect(tenant_id, start, end)
    trend = await metrics_repo.collect_runs_trend(tenant_id, start, end)
    return data, trend
