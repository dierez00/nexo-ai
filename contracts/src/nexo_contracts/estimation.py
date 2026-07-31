"""Contrato de estimación determinista.

`RunState` transporta una estimación (§5.1), así que su forma debe congelarse en
Fase 0 aunque las reglas de cálculo sean trabajo de Fase 1 (F1.7).

Dos invariantes viajan con el contrato: los montos se suman en código sobre
unidades menores, y cada cálculo declara de qué hechos depende para poder
invalidarse cuando uno de ellos se rechace (`DIE-F1-062`).
"""

from __future__ import annotations

from typing import Annotated, Self

from pydantic import Field, model_validator

from .base import NexoModel
from .enums import Domain
from .ids import FactId
from .primitives import Money, Slug


class EstimateStep(NexoModel):
    """Un trámite dentro de la ruta calculada, con dependencias estables."""

    step_id: Slug
    title: str = Field(max_length=200)
    depends_on: Annotated[list[Slug], Field(max_length=20)] = Field(default_factory=list)
    cost: Money | None = None
    duration_days: int | None = Field(default=None, ge=0, le=3650)
    missing_documents: Annotated[list[str], Field(max_length=30)] = Field(default_factory=list)
    derived_from: Annotated[list[FactId], Field(min_length=1, max_length=50)]


class Estimate(NexoModel):
    """Resultado del estimador: pasos ordenados, costo total y trazabilidad."""

    domain: Domain
    steps: Annotated[list[EstimateStep], Field(max_length=100)] = Field(default_factory=list)
    total_cost: Money | None = None
    derived_from: Annotated[list[FactId], Field(max_length=200)] = Field(default_factory=list)

    @model_validator(mode="after")
    def _dependencies_resolve_and_are_acyclic(self) -> Self:
        known = {step.step_id for step in self.steps}
        if len(known) != len(self.steps):
            raise ValueError("hay step_id duplicados en la estimación")
        for step in self.steps:
            missing = [dep for dep in step.depends_on if dep not in known]
            if missing:
                raise ValueError(
                    f"el paso {step.step_id!r} depende de trámites inexistentes: {missing}"
                )

        pending = {step.step_id: set(step.depends_on) for step in self.steps}
        resolved: set[str] = set()
        while pending:
            ready = {name for name, deps in pending.items() if deps <= resolved}
            if not ready:
                raise ValueError(
                    f"ciclo de dependencias entre trámites {sorted(pending)}; el DAG de "
                    f"permisos debe fallar de forma segura en lugar de ordenarse mal"
                )
            resolved |= ready
            pending = {name: deps for name, deps in pending.items() if name not in ready}
        return self

    @model_validator(mode="after")
    def _total_matches_the_sum_of_steps(self) -> Self:
        """El total se suma con código; si no cuadra, el contrato lo rechaza."""
        costed = [step.cost for step in self.steps if step.cost is not None]
        if not costed:
            return self
        currencies = {money.currency for money in costed}
        if len(currencies) > 1:
            raise ValueError(f"la estimación mezcla monedas distintas: {sorted(currencies)}")
        if self.total_cost is None:
            return self
        expected = sum(money.amount_minor for money in costed)
        if self.total_cost.amount_minor != expected:
            raise ValueError(
                f"el total declarado ({self.total_cost.amount_minor}) no coincide con la suma "
                f"de los pasos ({expected}); los montos se suman en código, no se redactan"
            )
        return self

    def topological_order(self) -> tuple[str, ...]:
        """Orden topológico con desempate alfabético estable (`DIE-F1-060`)."""
        pending = {step.step_id: set(step.depends_on) for step in self.steps}
        resolved: list[str] = []
        seen: set[str] = set()
        while pending:
            ready = sorted(name for name, deps in pending.items() if deps <= seen)
            resolved.extend(ready)
            seen.update(ready)
            pending = {name: deps for name, deps in pending.items() if name not in seen}
        return tuple(resolved)
