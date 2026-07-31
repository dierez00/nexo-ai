"""Construcción de superficies ciudadanas desde hechos verificados (`DIE-F1-103`).

La superficie se arma con **plantillas y datos**, nunca con estructura generada
por un modelo. El builder recibe `VerifiedFacts` —un snapshot cerrado— y decide
qué componentes usar según la categoría de cada hecho. Un modelo no interviene
en ningún punto de este archivo, y por eso no hay forma de que produzca un
componente que el catálogo no admita.

**Datos y estructura van separados** (`DIE-F1-102`). Los valores viven en el
data model y el árbol los referencia por binding (`{"path": "/requisitos/items"}`).
Incrustarlos en el árbol haría imposible actualizar un dato sin reenviar la
estructura entera, y —más importante— mezclaría contenido de la persona usuaria
con la definición de la interfaz.

Esta es la instalación mínima: cubre los dos recorridos del MVP. Formularios y
superficies administrativas son Fase 3.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from nexo_contracts import (
    A2UI_PROTOCOL_VERSION,
    A2UIAction,
    A2UIComponent,
    A2UIMessage,
    A2UISurface,
    ActionRequest,
    CatalogDescriptor,
    Channel,
    CreateSurface,
    Estimate,
    FactCategory,
    Money,
    UpdateComponents,
    UpdateDataModel,
    VerifiedFact,
    VerifiedFacts,
)

from .catalog import CITIZEN_CATALOG

ROOT = "root"


def format_money(money: Money) -> str:
    """Formatea un monto desde unidades menores. Nunca se suma aquí.

    El builder **presenta**; sumar es del estimador, con código y sobre
    `amount_minor`. Un total calculado al renderizar sería un número sin
    respaldo y sin `derived_from`.
    """
    units, cents = divmod(abs(money.amount_minor), 100)
    sign = "-" if money.amount_minor < 0 else ""
    return f"{sign}{units:,}.{cents:02d} {money.currency}".replace(",", " ")


def _fact_text(fact: VerifiedFact) -> str:
    """Texto presentable de un hecho, sin reinterpretarlo."""
    value = fact.value
    if value.money is not None:
        return f"{fact.claim} ({format_money(value.money)})"
    return fact.claim


@dataclass
class CitizenSurfaceBuilder:
    """Arma la superficie ciudadana de un run.

    No recibe puertos de RAG, de tools ni de modelo: todo lo que puede decir
    está en el `VerifiedFacts` que se le entrega.
    """

    catalog: CatalogDescriptor = field(default_factory=lambda: CITIZEN_CATALOG)

    def build(
        self,
        facts: VerifiedFacts,
        *,
        surface_id: str,
        channel: Channel = Channel.WEB,
        estimate: Estimate | None = None,
        pending_action: ActionRequest | None = None,
        action_label: str = "Confirmar",
        headline: str = "Esto es lo que encontré",
        warnings: tuple[str, ...] = (),
    ) -> A2UISurface:
        """Construye la superficie completa a partir del snapshot verificado."""
        accepted = list(facts.accepted())
        requirements = [f for f in accepted if f.category is FactCategory.REQUIREMENT]
        costs = [f for f in accepted if f.category is FactCategory.COST]
        schedules = [f for f in accepted if f.category is FactCategory.SCHEDULE]
        others = [
            f
            for f in accepted
            if f.category
            not in {
                FactCategory.REQUIREMENT,
                FactCategory.COST,
                FactCategory.SCHEDULE,
            }
        ]

        data = self._data_model(
            headline=headline,
            requirements=requirements,
            costs=costs,
            schedules=schedules,
            others=others,
            estimate=estimate,
            facts=facts,
            warnings=warnings,
        )
        components = self._components(
            has_requirements=bool(requirements),
            has_costs=bool(costs or estimate),
            has_schedules=bool(schedules),
            has_others=bool(others),
            has_sources=bool(data["fuentes"]),
            has_warnings=bool(warnings),
            action=pending_action,
        )

        actions: list[A2UIAction] = []
        if pending_action is not None:
            actions.append(pending_action.to_a2ui_action(label=action_label))

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
                    update_data_model=UpdateDataModel(surface_id=surface_id, path="/", value=data),
                ),
                A2UIMessage(
                    version=A2UI_PROTOCOL_VERSION,
                    update_components=UpdateComponents(
                        surface_id=surface_id, components=components
                    ),
                ),
            ],
            actions=actions,
        )

    # -- data model ---------------------------------------------------------

    def _data_model(
        self,
        *,
        headline: str,
        requirements: list[VerifiedFact],
        costs: list[VerifiedFact],
        schedules: list[VerifiedFact],
        others: list[VerifiedFact],
        estimate: Estimate | None,
        facts: VerifiedFacts,
        warnings: tuple[str, ...],
    ) -> dict[str, Any]:
        sources = sorted(
            {
                (citation.source_id, citation.corpus_version)
                for fact in facts.facts
                for citation in fact.citations
                if citation.is_active
            }
        )
        return {
            "titular": headline,
            "requisitos": {
                "items": [_fact_text(fact) for fact in requirements],
                "progreso": 0,
            },
            "costos": {
                "lineas": [_fact_text(fact) for fact in costs],
                "total": (
                    format_money(estimate.total_cost)
                    if estimate is not None and estimate.total_cost is not None
                    else ""
                ),
            },
            "detalles": [_fact_text(fact) for fact in others],
            "citas": [
                item for fact in schedules for item in (fact.value.items or [_fact_text(fact)])
            ],
            # Las fuentes se presentan por identificador opaco y versión de
            # corpus: es lo que hace auditable una respuesta sin exponer rutas
            # internas ni el texto completo del documento.
            "fuentes": [
                {"fuente": source_id, "version_corpus": corpus_version}
                for source_id, corpus_version in sources
            ],
            "avisos": list(warnings),
        }

    # -- árbol de componentes ------------------------------------------------

    def _components(
        self,
        *,
        has_requirements: bool,
        has_costs: bool,
        has_schedules: bool,
        has_others: bool,
        has_sources: bool,
        has_warnings: bool,
        action: ActionRequest | None,
    ) -> list[A2UIComponent]:
        children: list[str] = ["titular"]
        components: list[A2UIComponent] = [
            A2UIComponent(
                id="titular",
                component="Text",
                properties={"text": {"path": "/titular"}, "variant": "h1"},
            )
        ]

        if has_warnings:
            children.append("avisos")
            components.append(
                A2UIComponent(
                    id="avisos",
                    component="StatusBanner",
                    properties={
                        "title": "Ten en cuenta",
                        "message": {"path": "/avisos"},
                        "tone": "warning",
                    },
                )
            )

        if has_requirements:
            children.append("requisitos")
            components.append(
                A2UIComponent(
                    id="requisitos",
                    component="Checklist",
                    properties={
                        "title": "Requisitos",
                        "items": {"path": "/requisitos/items"},
                        "progress": {"path": "/requisitos/progreso"},
                    },
                )
            )

        if has_costs:
            children.append("costos")
            components.append(
                A2UIComponent(
                    id="costos",
                    component="CostSummary",
                    properties={
                        "title": "Costos",
                        "lines": {"path": "/costos/lineas"},
                        "total": {"path": "/costos/total"},
                    },
                )
            )

        if has_schedules:
            children.append("citas")
            components.append(
                A2UIComponent(
                    id="citas",
                    component="SlotPicker",
                    properties={
                        "title": "Horarios disponibles",
                        "slots": {"path": "/citas"},
                    },
                )
            )

        if has_others:
            children.append("detalles")
            components.append(
                A2UIComponent(
                    id="detalles",
                    component="List",
                    properties={"items": {"path": "/detalles"}, "ordered": False},
                )
            )

        if has_sources:
            children.append("fuentes")
            components.append(
                A2UIComponent(
                    id="fuentes",
                    component="SourceList",
                    properties={"title": "Fuentes", "sources": {"path": "/fuentes"}},
                )
            )

        if action is not None:
            children.append("confirmar")
            components.append(
                A2UIComponent(
                    id="confirmar",
                    component="ConfirmButton",
                    action_id=action.action_id,
                    properties={
                        "label": "Confirmar",
                        "description": "La operación se enviará una sola vez.",
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
