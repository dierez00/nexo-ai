"""Proyección determinista de resultados MCP a hechos candidatos (F1.5/F1.6).

Las tools devuelven datos tipados, pero el verificador opera sobre
``CandidateFact``. Esta frontera convierte únicamente las nueve respuestas del
MVP; no interpreta texto libre ni permite que una respuesta de tool cambie el
plan. Cada hecho conserva el ``tool_call_id`` que lo respalda.
"""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import JsonValue

from nexo_contracts import (
    CandidateFact,
    Domain,
    FactCategory,
    FactOrigin,
    FactValue,
    Money,
    ToolCallStatus,
    ToolResult,
)


def project_tool_results(
    results: Sequence[ToolResult],
    domain: Domain,
) -> tuple[CandidateFact, ...]:
    """Convierte resultados exitosos conocidos en hechos verificables."""
    projected: list[CandidateFact] = []
    ordinal = 0
    for result in results:
        if result.status is not ToolCallStatus.SUCCEEDED:
            continue
        for claim, category, value in _facts_for(result):
            ordinal += 1
            projected.append(
                CandidateFact(
                    fact_id=f"fact_tool{ordinal:04d}",
                    claim=claim,
                    value=value,
                    category=category,
                    domain=domain,
                    origin=FactOrigin.TOOL,
                    confidence=1.0,
                    tool_call_id=result.tool_call_id,
                )
            )
    return tuple(projected)


def _facts_for(result: ToolResult) -> tuple[tuple[str, FactCategory, FactValue], ...]:
    data = result.data
    if result.name == "vehiculos.consultar_adeudo":
        total = Money.model_validate(data["total"])
        blocks = bool(data["bloquea_renovacion"])
        return (
            (
                f"El adeudo vehicular consultado es de {_money_text(total)}.",
                FactCategory.COST,
                FactValue(money=total),
            ),
            (
                (
                    "El adeudo consultado bloquea la renovación."
                    if blocks
                    else "El vehículo consultado no tiene un adeudo que bloquee la renovación."
                ),
                # Es el estado de este vehículo en esta consulta, no la regla
                # normativa que dice que un adeudo pendiente bloquea el trámite.
                FactCategory.CONTEXT,
                FactValue(boolean=blocks),
            ),
        )

    if result.name == "vehiculos.localizar_modulo":
        modules = _object_list(data.get("modulos"))
        items = [
            f"{item.get('nombre', 'Módulo')}: {item.get('horario', 'horario no disponible')}"
            for item in modules
        ]
        return (
            (
                "Estos módulos atienden la renovación solicitada.",
                FactCategory.LOCATION,
                FactValue(items=items),
            ),
        )

    if result.name == "vehiculos.buscar_citas":
        return (
            (
                "Estos horarios de cita están disponibles en el módulo seleccionado.",
                FactCategory.SCHEDULE,
                FactValue(items=_slot_items(data.get("slots"))),
            ),
        )

    if result.name == "ayuntamiento.consultar_uso_suelo":
        allowed = bool(data["permitido"])
        return (
            (
                (
                    "El uso de suelo consultado permite el giro indicado."
                    if allowed
                    else "El uso de suelo consultado no permite el giro indicado."
                ),
                FactCategory.DEPENDENCY,
                FactValue(boolean=allowed),
            ),
        )

    if result.name == "ayuntamiento.calcular_costos":
        total = Money.model_validate(data["total"])
        return (
            (
                f"El cálculo institucional de derechos suma {_money_text(total)}.",
                FactCategory.COST,
                FactValue(money=total),
            ),
        )

    if result.name == "ayuntamiento.consultar_requisitos_negocio":
        requirements = [str(item) for item in _list(data.get("requisitos"))]
        return (
            (
                "La consulta institucional devolvió estos requisitos para el negocio.",
                FactCategory.REQUIREMENT,
                FactValue(items=requirements),
            ),
        )

    if result.name == "ayuntamiento.consultar_citas":
        return (
            (
                "Estos horarios están disponibles para atención municipal.",
                FactCategory.SCHEDULE,
                FactValue(items=_slot_items(data.get("slots"))),
            ),
        )

    return ()


def _money_text(money: Money) -> str:
    units, cents = divmod(abs(money.amount_minor), 100)
    sign = "-" if money.amount_minor < 0 else ""
    return f"{sign}{units}.{cents:02d} {money.currency}"


def _slot_items(value: JsonValue | None) -> list[str]:
    return [
        f"{item.get('inicio', 'horario no disponible')} · {item.get('slot_id', 'slot')}"
        for item in _object_list(value)
        if bool(item.get("disponible", True))
    ]


def _list(value: JsonValue | None) -> list[JsonValue]:
    return value if isinstance(value, list) else []


def _object_list(value: JsonValue | None) -> list[dict[str, JsonValue]]:
    return [item for item in _list(value) if isinstance(item, dict)]


__all__ = ["project_tool_results"]
