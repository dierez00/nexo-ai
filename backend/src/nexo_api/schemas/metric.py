"""Esquemas de métricas admin (§9.2 `MetricSet`)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class MetricWindow(BaseModel):
    start: datetime
    end: datetime


class RunMetricsSummary(BaseModel):
    total: int = 0
    by_status: dict[str, int] = Field(default_factory=dict)
    by_domain: dict[str, int] = Field(default_factory=dict)
    avg_latency_ms: float = 0.0
    total_cost_usd: float = 0.0


class CountByStatus(BaseModel):
    total: int = 0
    by_status: dict[str, int] = Field(default_factory=dict)


class MetricSet(BaseModel):
    window: MetricWindow
    runs: RunMetricsSummary
    conversations_total: int = 0
    actions: CountByStatus
    appointments: CountByStatus
    generated_at: datetime


class AdminChartRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=500)
    from_: datetime | None = Field(default=None, alias="from")
    to: datetime | None = None
