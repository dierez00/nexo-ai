"""Superficies A2UI administrativas para analítica determinista.

El prompt del admin solo selecciona una plantilla conocida. No genera SQL,
componentes ni propiedades; esas decisiones viven en este módulo y en el
catálogo `admin:v1`.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from nexo_contracts import (
    A2UI_PROTOCOL_VERSION,
    A2UIComponent,
    A2UIMessage,
    A2UISurface,
    CatalogDescriptor,
    Channel,
    CreateSurface,
    UpdateComponents,
    UpdateDataModel,
)

from .catalog import ADMIN_CATALOG

ROOT = "root"

AdminChartKind = Literal[
    "trend",
    "domain_distribution",
    "status_distribution",
    "latency_cost",
    "actions",
    "appointments",
    "conversations",
    "unsupported",
]

SUPPORTED_PROMPTS = (
    "trámites por dominio",
    "tendencia de trámites",
    "runs por estado",
    "latencia y costo",
    "acciones por estado",
    "citas por estado",
    "conversaciones",
)


@dataclass(frozen=True)
class AdminAnalyticsData:
    """Datos agregados y tenant-scoped que recibe el builder."""

    window_start: datetime
    window_end: datetime
    runs_total: int
    conversations_total: int
    avg_latency_ms: float
    total_cost_usd: float
    runs_by_status: dict[str, int] = field(default_factory=dict)
    runs_by_domain: dict[str, int] = field(default_factory=dict)
    actions_by_status: dict[str, int] = field(default_factory=dict)
    appointments_by_status: dict[str, int] = field(default_factory=dict)
    runs_trend: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class AdminAnalyticsSurfaceBuilder:
    """Convierte una solicitud textual en una superficie admin validable."""

    catalog: CatalogDescriptor = field(default_factory=lambda: ADMIN_CATALOG)

    def build(
        self,
        prompt: str,
        data: AdminAnalyticsData,
        *,
        surface_id: str,
        channel: Channel = Channel.WEB,
    ) -> A2UISurface:
        intent = classify_prompt(prompt)
        model = self._data_model(prompt=prompt, intent=intent, data=data)
        components = self._components(intent)
        return A2UISurface(
            surface_id=surface_id,
            catalog_id=self.catalog.catalog_id,
            channel=channel,
            messages=[
                A2UIMessage(
                    version=A2UI_PROTOCOL_VERSION,
                    create_surface=CreateSurface(
                        surface_id=surface_id,
                        catalog_id=self.catalog.catalog_id,
                        send_data_model=True,
                    ),
                ),
                A2UIMessage(
                    version=A2UI_PROTOCOL_VERSION,
                    update_data_model=UpdateDataModel(surface_id=surface_id, path="/", value=model),
                ),
                A2UIMessage(
                    version=A2UI_PROTOCOL_VERSION,
                    update_components=UpdateComponents(
                        surface_id=surface_id,
                        components=components,
                    ),
                ),
            ],
            actions=[],
        )

    def _data_model(
        self,
        *,
        prompt: str,
        intent: AdminChartKind,
        data: AdminAnalyticsData,
    ) -> dict[str, Any]:
        common = {
            "prompt": prompt.strip(),
            "intent": _intent_label(intent),
            "window": _window_label(data.window_start, data.window_end),
            "summary": {
                "runs": _format_int(data.runs_total),
                "conversations": _format_int(data.conversations_total),
                "latency": _format_ms(data.avg_latency_ms),
                "cost": f"${data.total_cost_usd:.4f}",
            },
            "suggestions": list(SUPPORTED_PROMPTS),
        }
        if intent == "trend":
            return {
                **common,
                "chart": {
                    "title": "Tendencia de trámites",
                    "description": "Runs creados por día en la ventana seleccionada.",
                    "type": "area",
                    "xKey": "date",
                    "yKey": "total",
                    "series": [{"key": "total", "label": "Runs"}],
                    "data": data.runs_trend,
                },
                "table": _table(["date", "total", "succeeded"], data.runs_trend),
            }
        if intent == "status_distribution":
            rows = _pairs(data.runs_by_status, "status", "total")
            return {
                **common,
                "chart": _categorical_chart("Runs por estado", "bar", rows, "status"),
                "table": _table(["status", "total"], rows),
            }
        if intent == "latency_cost":
            rows = [
                {"metric": "Latencia promedio", "value": round(data.avg_latency_ms, 2)},
                {"metric": "Costo total USD", "value": round(data.total_cost_usd, 4)},
            ]
            return {
                **common,
                "chart": _categorical_chart("Latencia y costo", "bar", rows, "metric"),
                "table": _table(["metric", "value"], rows),
            }
        if intent == "actions":
            rows = _pairs(data.actions_by_status, "status", "total")
            return {
                **common,
                "chart": _categorical_chart("Acciones por estado", "donut", rows, "status"),
                "table": _table(["status", "total"], rows),
            }
        if intent == "appointments":
            rows = _pairs(data.appointments_by_status, "status", "total")
            return {
                **common,
                "chart": _categorical_chart("Citas por estado", "donut", rows, "status"),
                "table": _table(["status", "total"], rows),
            }
        if intent == "conversations":
            rows = [{"metric": "Conversaciones", "total": data.conversations_total}]
            return {
                **common,
                "chart": _categorical_chart("Conversaciones", "bar", rows, "metric"),
                "table": _table(["metric", "total"], rows),
            }
        if intent == "unsupported":
            return {
                **common,
                "chart": _categorical_chart(
                    "Trámites por dominio",
                    "bar",
                    _pairs(data.runs_by_domain, "domain", "total"),
                    "domain",
                ),
                "table": _table(
                    ["suggestion"],
                    [{"suggestion": item} for item in SUPPORTED_PROMPTS],
                ),
            }
        return {
            **common,
            "chart": _categorical_chart(
                "Trámites por dominio",
                "bar",
                _pairs(data.runs_by_domain, "domain", "total"),
                "domain",
            ),
            "table": _table(
                ["domain", "total"],
                _pairs(data.runs_by_domain, "domain", "total"),
            ),
        }

    def _components(self, intent: AdminChartKind) -> list[A2UIComponent]:
        children = ["headline", "trace", "metric-runs", "metric-latency", "chart", "table"]
        components = [
            A2UIComponent(
                id="headline",
                component="Text",
                properties={"text": {"path": "/intent"}, "variant": "h1"},
            ),
            A2UIComponent(
                id="trace",
                component="StatusBanner",
                properties={
                    "title": "Interpretación",
                    "message": {"path": "/window"},
                    "tone": "info" if intent != "unsupported" else "warning",
                },
            ),
            A2UIComponent(
                id="metric-runs",
                component="MetricCard",
                properties={
                    "label": "Runs",
                    "value": {"path": "/summary/runs"},
                    "caption": "Ventana seleccionada",
                    "tone": "success",
                },
            ),
            A2UIComponent(
                id="metric-latency",
                component="MetricCard",
                properties={
                    "label": "Latencia promedio",
                    "value": {"path": "/summary/latency"},
                    "caption": {"path": "/summary/cost"},
                    "tone": "info",
                },
            ),
            A2UIComponent(
                id="chart",
                component="ChartPanel",
                properties={
                    "title": {"path": "/chart/title"},
                    "description": {"path": "/chart/description"},
                    "chartType": {"path": "/chart/type"},
                    "data": {"path": "/chart/data"},
                    "xKey": {"path": "/chart/xKey"},
                    "yKey": {"path": "/chart/yKey"},
                    "series": {"path": "/chart/series"},
                },
            ),
            A2UIComponent(
                id="table",
                component="DataTable",
                properties={
                    "title": "Datos",
                    "columns": {"path": "/table/columns"},
                    "rows": {"path": "/table/rows"},
                    "caption": "Datos agregados y autorizados para este tenant.",
                },
            ),
        ]
        if intent == "unsupported":
            children.insert(2, "unsupported")
            components.append(
                A2UIComponent(
                    id="unsupported",
                    component="StatusBanner",
                    properties={
                        "title": "Solicitud no soportada",
                        "message": "Prueba una de las solicitudes sugeridas en la tabla.",
                        "tone": "warning",
                    },
                )
            )
        components.insert(
            0,
            A2UIComponent(
                id=ROOT,
                component="Column",
                children=children,
                properties={"align": "stretch", "gap": "md"},
            ),
        )
        return components


def classify_prompt(prompt: str) -> AdminChartKind:
    normalized = _normalize(prompt)
    if any(token in normalized for token in ("tendencia", "diario", "dia", "evolucion")):
        return "trend"
    if "dominio" in normalized or "modulo" in normalized or "area" in normalized:
        return "domain_distribution"
    if "estado" in normalized or "status" in normalized:
        if "accion" in normalized:
            return "actions"
        if "cita" in normalized:
            return "appointments"
        return "status_distribution"
    if "latencia" in normalized or "costo" in normalized or "coste" in normalized:
        return "latency_cost"
    if "accion" in normalized:
        return "actions"
    if "cita" in normalized or "appointment" in normalized:
        return "appointments"
    if "conversacion" in normalized or "chat" in normalized:
        return "conversations"
    if "tramite" in normalized or "run" in normalized:
        return "domain_distribution"
    return "unsupported"


def _normalize(value: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", ascii_text.lower()).strip()


def _intent_label(intent: AdminChartKind) -> str:
    labels = {
        "trend": "Tendencia de trámites",
        "domain_distribution": "Trámites por dominio",
        "status_distribution": "Runs por estado",
        "latency_cost": "Latencia y costo",
        "actions": "Acciones por estado",
        "appointments": "Citas por estado",
        "conversations": "Conversaciones",
        "unsupported": "Solicitud no soportada",
    }
    return labels[intent]


def _window_label(start: datetime, end: datetime) -> str:
    return f"{start.date().isoformat()} a {end.date().isoformat()}"


def _format_int(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def _format_ms(value: float) -> str:
    if value < 1000:
        return f"{round(value)} ms"
    return f"{value / 1000:.1f} s"


def _pairs(values: dict[str, int], name_key: str, value_key: str) -> list[dict[str, Any]]:
    rows = [{name_key: key, value_key: value} for key, value in sorted(values.items())]
    return rows or [{name_key: "sin datos", value_key: 0}]


def _categorical_chart(
    title: str,
    chart_type: str,
    rows: list[dict[str, Any]],
    x_key: str,
) -> dict[str, Any]:
    return {
        "title": title,
        "description": "Agregado determinista sobre datos autorizados.",
        "type": chart_type,
        "xKey": x_key,
        "yKey": "total" if "total" in rows[0] else "value",
        "series": [{"key": "total" if "total" in rows[0] else "value", "label": title}],
        "data": rows,
    }


def _table(columns: list[str], rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "columns": [
            {"key": column, "label": column.replace("_", " ").title()} for column in columns
        ],
        "rows": rows,
    }
