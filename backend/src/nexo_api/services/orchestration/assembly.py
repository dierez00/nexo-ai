"""Composition root de producción del grafo MVP real (perfil `real`).

Ensambla las mismas piezas que `tests/e2e/runtime.py:build_runtime` —agentes,
RAG, MCP, A2UI y gateway— pero con reloj e IDs reales. El modelo es un doble
programado por escenario: el adaptador Anthropic real es trabajo posterior
(`integrations/models`), así que este perfil corre el **recorrido real con tools
mock**, determinista sobre el escenario de demostración vehicular.

Las dependencias pesadas se importan dentro de `build_graph_deps` para que el
perfil `fake` (default) no cargue corpus ni agentes al importar la app.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Any, cast

from nexo_observability.logging import get_logger

from nexo_api.services.orchestration.clock import SystemClock, UuidIdFactory

if TYPE_CHECKING:
    from collections.abc import Sequence

    from nexo_contracts.config import PoliciesConfig
    from nexo_mcp.catalog import ToolCatalog
    from nexo_mcp.execution import ToolExecutor
    from nexo_orchestration.graph.mvp import MVPDependencies
    from nexo_orchestration.testing import Scenario
    from nexo_rag.testing import LoadedCorpus

log = get_logger(__name__)

VALID_AT = date(2026, 7, 30)

# Institución del corpus de demostración; el verificador filtra fuentes por ella.
_DEMO_INSTITUTION = "inst_demo"


@dataclass
class GraphAssembly:
    """Piezas ensambladas una vez y reutilizadas por cada run."""

    deps: MVPDependencies
    catalog: ToolCatalog
    executor: ToolExecutor
    clock: SystemClock
    ids: UuidIdFactory
    policies: PoliciesConfig
    valid_at: date = VALID_AT


# -- payloads del modelo falso (mismos shapes que los agentes esperan) ---------


def _classification_payload(intents: list[tuple[str, str]], **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "intents": [
            {"intent": slug, "domain": domain, "confidence": 0.92} for slug, domain in intents
        ],
        "entities": {},
        "confidence": 0.9,
    }
    payload.update(extra)
    return payload


def _extraction_payload(
    facts: list[dict[str, Any]],
    tools: list[str] | None = None,
    *,
    tool_parameters: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    parameters = tool_parameters or {}
    return {
        "facts": facts,
        "proposed_tools": [
            {
                "name": name,
                "rationale": "necesario para el trámite",
                "parameters": parameters.get(name, {}),
            }
            for name in (tools or [])
        ],
    }


def _answer_payload(answer: str) -> dict[str, Any]:
    return {"answer": answer, "short_answer": answer[:200]}


async def _demo_scenarios(corpus: LoadedCorpus) -> dict[str, Scenario | Sequence[Scenario]]:
    """Guion vehicular del modelo falso, citando fragmentos reales del corpus.

    Reproduce el recorrido `CAP-VEH-01`: renovar licencia + consultar adeudo,
    que llega a `waiting_confirmation` con requisitos, costo, fuentes y la acción
    de reservar cita.
    """
    from nexo_contracts import Domain, RetrievalFilters, RetrievalQuery, SourceStatus
    from nexo_orchestration.testing import Scenario

    response = await corpus.retriever(Domain.VEHICULOS).retrieve(
        RetrievalQuery(
            query=(
                "Quiero renovar mi licencia y saber si debo algo. Renovar licencia de "
                "conducir, requisitos, costo, módulos y cita. Consultar adeudo vehicular."
            ),
            domain=Domain.VEHICULOS,
            filters=RetrievalFilters(
                institution_id=_DEMO_INSTITUTION,
                status=[SourceStatus.ACTIVE],
                valid_at=VALID_AT,
            ),
            top_k=10,
        )
    )
    fragments = {result.title: result.fragment_id for result in response.results}

    def fragment(title: str) -> str:
        found = fragments.get(title)
        if found is None:
            # El escenario depende de títulos estables del corpus; si cambian, se
            # cae al primer fragmento disponible para no romper el arranque.
            log.warning("orchestration.demo_fragment_missing", title=title)
            return next(iter(fragments.values()))
        return found

    facts = [
        {
            "claim": "Se requiere identificación oficial vigente.",
            "category": "requirement",
            "value": {"items": ["Identificación oficial vigente"]},
            "fragment_ids": [fragment("Documentos que debe presentar la persona solicitante")],
            "confidence": 0.93,
        },
        {
            "claim": "Renovar la licencia tipo A cuesta 814.00 MXN.",
            "category": "cost",
            "value": {"money": {"amount_minor": 81400, "currency": "MXN"}},
            "fragment_ids": [fragment("Licencia de conducir tipo A")],
            "confidence": 0.95,
        },
        {
            "claim": "Un adeudo pendiente bloquea la renovación.",
            "category": "dependency",
            "value": {"boolean": True},
            "fragment_ids": [fragment("Adeudos previos")],
            "confidence": 0.94,
        },
    ]
    scenarios: dict[str, Scenario | Sequence[Scenario]] = {
        "classify_request": Scenario(
            data=_classification_payload(
                [("renovar_licencia", "vehiculos"), ("consultar_adeudo", "vehiculos")],
                location="Durango",
            )
        ),
        "navigate_domain": Scenario(
            data=_extraction_payload(
                facts,
                tools=[
                    "vehiculos.consultar_adeudo",
                    "vehiculos.localizar_modulo",
                    "vehiculos.buscar_citas",
                ],
                tool_parameters={
                    "vehiculos.consultar_adeudo": {"vehiculo_ref": "veh_demo_sin_adeudo"},
                    "vehiculos.localizar_modulo": {"tramite": "renovacion", "zona": "centro"},
                    "vehiculos.buscar_citas": {
                        "modulo_id": "mod_centro",
                        "desde": "2026-08-03",
                        "hasta": "2026-08-10",
                    },
                },
            )
        ),
        "write_answer": Scenario(
            data=_answer_payload(
                "Para renovar tu licencia necesitas identificación oficial vigente; "
                "el costo de la tipo A es de 814.00 MXN. Confirma para reservar tu cita."
            )
        ),
    }
    return scenarios


async def build_graph_deps() -> GraphAssembly:
    """Ensambla el grafo real offline (tools mock, modelo falso)."""
    from nexo_a2ui import CitizenSurfaceBuilder, SurfaceValidator
    from nexo_a2ui.catalog import CITIZEN_CATALOG
    from nexo_agents.catalog import CentralCatalog
    from nexo_agents.classifier import Classifier
    from nexo_agents.domain_manifest import load_domains
    from nexo_agents.estimator import Estimator, VehicleEstimator, load_permit_graph
    from nexo_agents.navigator import DomainNavigator
    from nexo_agents.tool_facts import project_tool_results
    from nexo_agents.transactional import TransactionalAgent
    from nexo_agents.verifier import Verifier
    from nexo_agents.writer import Writer
    from nexo_contracts import Domain
    from nexo_mcp.authorization import PermissionMatrix
    from nexo_mcp.catalog import ToolCatalog
    from nexo_mcp.execution import ToolExecutor
    from nexo_orchestration.configuration import load_config
    from nexo_orchestration.graph.mvp import MVPDependencies
    from nexo_orchestration.models import ModelGateway
    from nexo_orchestration.testing import FakeChatAdapter
    from nexo_rag.corpus.cli import CORE_DOMAINS, repository_root
    from nexo_rag.testing import load_corpus

    root = repository_root()
    config = load_config()
    clock = SystemClock()
    ids = UuidIdFactory()

    corpus = await load_corpus(root=root, domains=CORE_DOMAINS)
    manifests = load_domains(root, CORE_DOMAINS)
    scenarios = await _demo_scenarios(corpus)

    gateway = ModelGateway(
        router=config.model_router,
        outcomes=config.policies.outcomes,
        adapters={"fake": FakeChatAdapter(scenarios, provider="fake")},
        clock=clock,
        ids=ids,
    )

    permissions = PermissionMatrix(config=config.permissions)
    catalog = ToolCatalog(config=config.tool_registry, permissions=permissions)
    central_catalog = CentralCatalog.load(
        root,
        domains=CORE_DOMAINS,
        tools=catalog,
        models=config.model_router,
        policies=config.policies,
        a2ui_components=frozenset(component.name for component in CITIZEN_CATALOG.components),
    )
    executor = ToolExecutor(catalog=catalog, permissions=permissions, clock=clock)

    navigators = {
        domain: DomainNavigator(
            domain=domain,
            manifest=manifests[domain],
            gateway=gateway,
            retriever=corpus.retriever(domain),
        )
        for domain in CORE_DOMAINS
    }
    # VehicleEstimator y Estimator son hermanos con la misma interfaz `.estimate`;
    # MVPDependencies los agrupa por su forma estructural, no por herencia.
    estimators = cast(
        "dict[Domain, Estimator]",
        {
            Domain.VEHICULOS: VehicleEstimator(),
            Domain.AYUNTAMIENTO_EMPRESAS: Estimator(
                graph=load_permit_graph(root, Domain.AYUNTAMIENTO_EMPRESAS)
            ),
        },
    )

    deps = MVPDependencies(
        gateway=gateway,
        classifier=Classifier(gateway=gateway, manifests=manifests),
        navigators=navigators,
        verifier_factory=lambda now, valid_at: Verifier(
            institution_id=_DEMO_INSTITUTION, now=now, valid_at=valid_at
        ),
        estimators=estimators,
        writer=Writer(gateway=gateway),
        transactional=TransactionalAgent(catalog=catalog, executor=executor),
        catalog=catalog,
        executor=executor,
        tool_fact_projector=project_tool_results,
        surface_builder=CitizenSurfaceBuilder(),
        surface_validator=SurfaceValidator(catalog=CITIZEN_CATALOG),
        central_catalog=central_catalog,
    )

    log.info("orchestration.real_profile_assembled", domains=len(navigators))
    return GraphAssembly(
        deps=deps,
        catalog=catalog,
        executor=executor,
        clock=clock,
        ids=ids,
        policies=config.policies,
    )
