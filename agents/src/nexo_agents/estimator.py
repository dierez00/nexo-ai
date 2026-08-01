"""Estimador secuencial y determinista (F1.7).

Calcula la ruta de trámites, sus dependencias, sus costos y sus documentos
faltantes. **El modelo no interviene en ningún cálculo** (`DIE-F1-063`): puede
explicar un resultado ya calculado, pero no producirlo ni alterarlo. Por eso
este módulo no recibe un `ModelGateway`.

Tres invariantes cargan el peso:

1. **Los montos se suman en código sobre unidades menores** (`DIE-F1-057`). Un
   total redactado por un modelo es un número sin `derived_from`: nadie puede
   decir de qué hechos salió ni invalidarlo cuando uno se rechace.
2. **Un paso solo entra si hay evidencia verificada que lo respalde**
   (`DIE-F1-061`). El grafo de permisos dice qué buscar; los `VerifiedFacts`
   dicen qué se puede afirmar. Un paso declarado en el YAML y sin respaldo se
   omite y se advierte.
3. **Un ciclo o una dependencia rota detiene la estimación** (`DIE-F1-059`). Es
   preferible no dar ruta a darla en un orden imposible: alguien la seguiría.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Self

import yaml
from pydantic import Field, ValidationError, model_validator

from nexo_contracts import (
    ConfigurationError,
    Domain,
    Estimate,
    EstimateStep,
    FactCategory,
    Money,
    NexoModel,
    SelfCheckResult,
    VerificationStatus,
    VerifiedFact,
    VerifiedFacts,
)
from nexo_contracts.ids import FactId
from nexo_contracts.primitives import Slug

PERMIT_GRAPH_FILENAME = "permit_graph.yaml"


class PermitStep(NexoModel):
    """Un trámite del grafo, con su identificador estable."""

    step_id: Slug
    title: str = Field(max_length=200)
    depends_on: Annotated[list[Slug], Field(max_length=20)] = Field(default_factory=list)
    duration_days: int | None = Field(default=None, ge=0, le=3650)
    evidence_keywords: Annotated[list[str], Field(min_length=1, max_length=20)]
    required_documents: Annotated[list[str], Field(max_length=30)] = Field(default_factory=list)


class PermitGraph(NexoModel):
    """`domains/<slug>/permit_graph.yaml`."""

    version: str = Field(max_length=80, pattern=r"^[a-z0-9][a-z0-9._-]{2,79}$")
    domain: Domain
    title: str = Field(max_length=200)
    steps: Annotated[list[PermitStep], Field(min_length=1, max_length=50)]

    @model_validator(mode="after")
    def _dependencies_resolve_and_are_acyclic(self) -> Self:
        """`DIE-F1-059`: el grafo se rechaza al cargarlo, no al recorrerlo."""
        known = {step.step_id for step in self.steps}
        if len(known) != len(self.steps):
            raise ValueError("hay step_id duplicados en el grafo de permisos")
        for step in self.steps:
            missing = [dep for dep in step.depends_on if dep not in known]
            if missing:
                raise ValueError(
                    f"el trámite {step.step_id!r} depende de trámites inexistentes: {missing}"
                )

        pending = {step.step_id: set(step.depends_on) for step in self.steps}
        resolved: set[str] = set()
        while pending:
            ready = {name for name, deps in pending.items() if deps <= resolved}
            if not ready:
                raise ValueError(
                    f"ciclo de dependencias entre trámites {sorted(pending)}; una ruta "
                    f"circular no se puede recorrer y no debe entregarse"
                )
            resolved |= ready
            pending = {name: deps for name, deps in pending.items() if name not in ready}
        return self

    def step(self, step_id: str) -> PermitStep | None:
        return next((step for step in self.steps if step.step_id == step_id), None)


def load_permit_graph(root: Path, domain: Domain) -> PermitGraph:
    """Carga el grafo de un dominio. Un grafo inválido detiene la estimación."""
    path = root / "domains" / domain.value / PERMIT_GRAPH_FILENAME
    if not path.exists():
        raise ConfigurationError(str(path), "<archivo>", "el grafo de permisos no existe")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    try:
        graph = PermitGraph.model_validate(raw)
    except ValidationError as exc:
        first = exc.errors()[0]
        location = ".".join(str(part) for part in first["loc"]) or "<raíz>"
        raise ConfigurationError(str(path), location, first["msg"]) from exc
    if graph.domain is not domain:
        raise ConfigurationError(
            str(path), "domain", f"el grafo declara el dominio {graph.domain.value!r}"
        )
    return graph


@dataclass(frozen=True)
class EstimationOutcome:
    """Estimación más lo que hizo falta advertir para producirla."""

    estimate: Estimate
    self_check: SelfCheckResult
    warnings: tuple[str, ...] = ()
    unsupported_steps: tuple[str, ...] = ()


def _matches(fact: VerifiedFact, keywords: Sequence[str]) -> bool:
    """Enlace entre un hecho verificado y un trámite del grafo.

    Es coincidencia por palabras clave y es **deuda reconocida**: F2.1 lo
    sustituye por IDs de trámite del catálogo central. Hoy es lo que hay, y al
    menos es determinista y está declarado en datos, no escondido en código.
    """
    from nexo_agents.keywords import normalize_for_match

    haystack = normalize_for_match(fact.claim)
    return any(normalize_for_match(keyword) in haystack for keyword in keywords)


@dataclass
class Estimator:
    """Estimación determinista sobre un snapshot de hechos verificados."""

    graph: PermitGraph

    def estimate(self, facts: VerifiedFacts) -> EstimationOutcome:
        """Construye la ruta ordenada, suma los costos y registra su origen."""
        accepted = [
            fact for fact in facts.facts if fact.verification is VerificationStatus.ACCEPTED
        ]

        steps: list[EstimateStep] = []
        warnings: list[str] = []
        unsupported: list[str] = []
        included: set[str] = set()

        for permit in self.graph.steps:
            backing = [fact for fact in accepted if _matches(fact, permit.evidence_keywords)]
            if not backing:
                # `DIE-F1-061`: sin evidencia no se afirma el trámite. Omitirlo
                # es menos dañino que incluirlo sin poder citarlo.
                unsupported.append(permit.step_id)
                continue

            cost = self._cost_of(backing)
            steps.append(
                EstimateStep(
                    step_id=permit.step_id,
                    title=permit.title,
                    # Las dependencias se recortan a los pasos realmente
                    # incluidos: apuntar a un trámite omitido dejaría la
                    # estimación con una referencia irresoluble.
                    depends_on=[dep for dep in permit.depends_on if dep in included],
                    cost=cost,
                    duration_days=permit.duration_days,
                    missing_documents=list(permit.required_documents),
                    # `DIE-F1-062`: de qué hechos salió cada paso, para poder
                    # invalidarlo cuando uno de ellos se rechace.
                    derived_from=[fact.fact_id for fact in backing],
                )
            )
            included.add(permit.step_id)

        if unsupported:
            warnings.append(
                f"{len(unsupported)} trámite(s) del grafo no tienen evidencia verificada "
                f"y quedaron fuera de la ruta"
            )

        steps, dropped = self._drop_foreign_currencies(steps)
        if dropped:
            warnings.append(
                f"{len(dropped)} costo(s) llegaron en otra moneda y se omitieron; "
                f"la ruta se mantiene, el importe no"
            )
        total = self._total(steps)

        estimate = Estimate(
            domain=self.graph.domain,
            steps=self._topological(steps),
            total_cost=total,
            derived_from=sorted({fact_id for step in steps for fact_id in step.derived_from}),
        )
        return EstimationOutcome(
            estimate=estimate,
            self_check=SelfCheckResult(
                schema_valid=True,
                unsupported_claims=len(unsupported),
                notes=["estimation_deterministic"],
            ),
            warnings=tuple(warnings),
            unsupported_steps=tuple(unsupported),
        )

    # -- costos -------------------------------------------------------------

    def _cost_of(self, backing: Sequence[VerifiedFact]) -> Money | None:
        """Costo del trámite, tomado del hecho de costo que lo respalda.

        Si varios hechos de costo respaldan el mismo trámite se toma el primero
        y no se suman: dos costos para un trámite es una contradicción, no un
        subtotal, y resolverla es del verificador.
        """
        for fact in backing:
            if fact.category is FactCategory.COST and fact.value.money is not None:
                return fact.value.money
        return None

    def _drop_foreign_currencies(
        self, steps: list[EstimateStep]
    ) -> tuple[list[EstimateStep], list[str]]:
        """Quita el importe de los pasos cuya moneda no es la mayoritaria.

        El contrato de `Estimate` rechaza una estimación con monedas mezcladas,
        y hace bien: sumarlas exigiría un tipo de cambio que nadie declaró. Lo
        que se conserva es la **ruta** —que sigue siendo correcta— y lo que se
        pierde es el importe divergente, con su aviso. Convertir en silencio
        sería el único desenlace inaceptable.
        """
        currencies = [step.cost.currency for step in steps if step.cost is not None]
        if len(set(currencies)) <= 1:
            return steps, []

        # Mayoría simple; a igualdad, la primera en aparecer, que es estable.
        dominant = max(
            set(currencies),
            key=lambda currency: (currencies.count(currency), -currencies.index(currency)),
        )
        kept: list[EstimateStep] = []
        dropped: list[str] = []
        for step in steps:
            if step.cost is not None and step.cost.currency != dominant:
                dropped.append(step.step_id)
                kept.append(step.model_copy(update={"cost": None}))
            else:
                kept.append(step)
        return kept, dropped

    def _total(self, steps: Sequence[EstimateStep]) -> Money | None:
        """Suma en código sobre `amount_minor` (`DIE-F1-057`).

        Mezclar monedas devuelve `None` en vez de convertir: una conversión
        implícita a mitad de un trámite es exactamente el tipo de número que
        nadie puede auditar después.
        """
        costs = [step.cost for step in steps if step.cost is not None]
        if not costs:
            return None
        currencies = {cost.currency for cost in costs}
        if len(currencies) > 1:
            return None
        return Money(
            amount_minor=sum(cost.amount_minor for cost in costs),
            currency=costs[0].currency,
        )

    # -- orden --------------------------------------------------------------

    def _topological(self, steps: Sequence[EstimateStep]) -> list[EstimateStep]:
        """Orden topológico con desempate alfabético (`DIE-F1-060`).

        El desempate no es cosmético: sin él, dos trámites sin dependencias
        entre sí alternarían de orden entre corridas y ningún golden test ni
        baseline sería comparable.
        """
        by_id = {step.step_id: step for step in steps}
        pending = {step.step_id: set(step.depends_on) for step in steps}
        ordered: list[EstimateStep] = []
        seen: set[str] = set()

        while pending:
            ready = sorted(name for name, deps in pending.items() if deps <= seen)
            if not ready:  # pragma: no cover - el contrato ya rechaza los ciclos
                raise ValueError(f"ciclo de dependencias entre {sorted(pending)}")
            ordered.extend(by_id[name] for name in ready)
            seen.update(ready)
            pending = {name: deps for name, deps in pending.items() if name not in seen}
        return ordered


@dataclass
class VehicleEstimator:
    """Ruta determinista de trámites vehiculares de licencia tipo A.

    Vehículos no necesita un DAG de cuatro permisos, pero sí debe entregar el
    costo y los documentos faltantes con trazabilidad. El adeudo consultado es
    un costo distinto y nunca se suma como tarifa de licencia.
    """

    def estimate(self, facts: VerifiedFacts) -> EstimationOutcome:
        accepted = [
            fact for fact in facts.facts if fact.verification is VerificationStatus.ACCEPTED
        ]
        requirements = [fact for fact in accepted if fact.category is FactCategory.REQUIREMENT]
        license_costs = [
            fact
            for fact in accepted
            if fact.category is FactCategory.COST
            and "licencia" in fact.claim.casefold()
            and any(
                term in fact.claim.casefold()
                for term in ("renov", "primera emision", "primera emisión")
            )
            and fact.value.money is not None
        ]
        backing = [*requirements, *license_costs]
        if not backing:
            return EstimationOutcome(
                estimate=Estimate(domain=Domain.VEHICULOS),
                self_check=SelfCheckResult(
                    schema_valid=True,
                    unsupported_claims=1,
                    notes=["vehicle_estimation_without_evidence"],
                ),
                warnings=("No hay evidencia verificada suficiente para calcular la licencia.",),
                unsupported_steps=("licencia_conducir",),
            )

        documents = sorted({item for fact in requirements for item in (fact.value.items or [])})
        derived_from = sorted({fact.fact_id for fact in backing})
        first_time = any(
            any(term in fact.claim.casefold() for term in ("primera emision", "primera emisión"))
            for fact in backing
        )
        cost_candidates = [
            fact
            for fact in license_costs
            if (
                any(
                    term in fact.claim.casefold()
                    for term in ("primera emision", "primera emisión")
                )
                if first_time
                else "renov" in fact.claim.casefold()
            )
        ]
        selected_cost = (
            cost_candidates[0]
            if cost_candidates
            else (license_costs[0] if license_costs else None)
        )
        cost = selected_cost.value.money if selected_cost is not None else None
        step_id = "primera_emision_licencia" if first_time else "renovar_licencia"
        title = (
            "Tramitar licencia de conducir por primera vez"
            if first_time
            else "Renovar licencia de conducir"
        )
        estimate = Estimate(
            domain=Domain.VEHICULOS,
            steps=[
                EstimateStep(
                    step_id=step_id,
                    title=title,
                    cost=cost,
                    missing_documents=documents,
                    derived_from=derived_from,
                )
            ],
            total_cost=cost,
            derived_from=derived_from,
        )
        return EstimationOutcome(
            estimate=estimate,
            self_check=SelfCheckResult(
                schema_valid=True,
                notes=["vehicle_estimation_deterministic"],
            ),
        )


def invalidated_by(estimate: Estimate, rejected_fact_ids: Sequence[FactId]) -> tuple[str, ...]:
    """Pasos que dejan de sostenerse si esos hechos se rechazan (`DIE-F1-062`).

    Existe para que rechazar un hecho después de estimar tenga consecuencia
    visible en vez de dejar una ruta que ya no se apoya en nada.
    """
    rejected = set(rejected_fact_ids)
    return tuple(
        step.step_id
        for step in estimate.steps
        if rejected.issuperset(step.derived_from) and step.derived_from
    )
