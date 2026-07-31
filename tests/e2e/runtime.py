"""Composition root del perfil offline.

Ensambla el MVP completo con dobles: modelo falso, corpus en memoria, tools
mock, reloj e IDs congelados. **No abre red, base de datos ni credenciales.**

Vive en `tests/e2e/` y no dentro de un paquete a propósito. Ensamblar es
inevitablemente el punto donde todo se conoce —agentes, RAG, MCP, A2UI y
orquestación—, y ponerlo dentro de cualquiera de esos módulos invertiría sus
dependencias. Cuando Dani monte la API construirá su propio ensamblado con las
mismas piezas: para eso existen los puertos.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from nexo_a2ui import CitizenSurfaceBuilder, SurfaceValidator
from nexo_a2ui.catalog import CITIZEN_CATALOG
from nexo_agents.catalog import CentralCatalog
from nexo_agents.classifier import Classifier
from nexo_agents.domain_manifest import DomainManifest, load_domains
from nexo_agents.estimator import Estimator, VehicleEstimator, load_permit_graph
from nexo_agents.navigator import DomainNavigator
from nexo_agents.tool_facts import project_tool_results
from nexo_agents.transactional import TransactionalAgent
from nexo_agents.verifier import Verifier
from nexo_agents.writer import Writer
from nexo_contracts import Channel, Domain, Identity, RunRequest
from nexo_mcp.authorization import PermissionMatrix
from nexo_mcp.catalog import ToolCatalog
from nexo_mcp.execution import AdapterFailure, ToolExecutor
from nexo_orchestration.configuration import load_config
from nexo_orchestration.graph.mvp import MVPDependencies, MVPGraph
from nexo_orchestration.models import ModelGateway
from nexo_orchestration.testing import (
    FakeChatAdapter,
    FrozenClock,
    InMemoryCheckpointStore,
    InMemoryEventSink,
    Scenario,
    SequentialIdFactory,
)
from nexo_rag.corpus.cli import CORE_DOMAINS, repository_root
from nexo_rag.testing import LoadedCorpus, load_corpus

VALID_AT = date(2026, 7, 30)


@dataclass
class OfflineRuntime:
    """El MVP ensamblado, con acceso a sus piezas para poder afirmar sobre ellas."""

    graph: MVPGraph
    events: InMemoryEventSink
    checkpoints: InMemoryCheckpointStore
    executor: ToolExecutor
    corpus: LoadedCorpus
    manifests: dict[Domain, DomainManifest]
    central_catalog: CentralCatalog
    clock: FrozenClock

    async def trace(self, run_id: str) -> tuple[str, ...]:
        """Tipos de evento del run, en orden. La forma legible de una traza."""
        return tuple(event.type.value for event in await self.events.read(run_id))


def classification_payload(intents: list[tuple[str, str]], **extra: Any) -> dict[str, Any]:
    """Salida programada del clasificador para un escenario."""
    payload: dict[str, Any] = {
        "intents": [
            {"intent": slug, "domain": domain, "confidence": 0.92} for slug, domain in intents
        ],
        "entities": {},
        "confidence": 0.9,
    }
    payload.update(extra)
    return payload


def extraction_payload(
    facts: list[dict[str, Any]],
    tools: list[str] | None = None,
    *,
    tool_parameters: dict[str, dict[str, Any]] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    parameters = tool_parameters or {}
    payload: dict[str, Any] = {
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
    payload.update(extra)
    return payload


def answer_payload(answer: str, short: str = "") -> dict[str, Any]:
    return {"answer": answer, "short_answer": short or answer[:200]}


async def build_runtime(
    *,
    scenarios: dict[str, Scenario | list[Scenario]],
    root: Path | None = None,
    failures: dict[str, AdapterFailure] | None = None,
    with_a2ui: bool = True,
    strict_model_errors: bool = False,
) -> OfflineRuntime:
    """Ensambla el MVP offline con los escenarios de modelo programados."""
    resolved_root = root or repository_root()
    config = load_config()
    clock = FrozenClock()
    ids = SequentialIdFactory()

    corpus = await load_corpus(root=resolved_root, domains=CORE_DOMAINS)
    manifests = load_domains(resolved_root, CORE_DOMAINS)

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
        resolved_root,
        domains=CORE_DOMAINS,
        tools=catalog,
        models=config.model_router,
        policies=config.policies,
        a2ui_components=frozenset(component.name for component in CITIZEN_CATALOG.components),
    )
    executor = ToolExecutor(
        catalog=catalog, permissions=permissions, clock=clock, failures=failures or {}
    )

    navigators = {
        domain: DomainNavigator(
            domain=domain,
            manifest=manifests[domain],
            gateway=gateway,
            retriever=corpus.retriever(domain),
        )
        for domain in CORE_DOMAINS
    }
    estimators = {
        Domain.VEHICULOS: VehicleEstimator(),
        Domain.AYUNTAMIENTO_EMPRESAS: Estimator(
            graph=load_permit_graph(resolved_root, Domain.AYUNTAMIENTO_EMPRESAS)
        ),
    }

    deps = MVPDependencies(
        gateway=gateway,
        classifier=Classifier(gateway=gateway, manifests=manifests),
        navigators=navigators,
        verifier_factory=lambda now, valid_at: Verifier(
            institution_id="inst_demo", now=now, valid_at=valid_at
        ),
        estimators=estimators,
        writer=Writer(gateway=gateway),
        transactional=TransactionalAgent(catalog=catalog, executor=executor),
        catalog=catalog,
        executor=executor,
        tool_fact_projector=project_tool_results,
        surface_builder=CitizenSurfaceBuilder() if with_a2ui else None,
        surface_validator=SurfaceValidator(catalog=CITIZEN_CATALOG) if with_a2ui else None,
        central_catalog=central_catalog,
        strict_model_errors=strict_model_errors,
    )

    events = InMemoryEventSink()
    checkpoints = InMemoryCheckpointStore()
    graph = MVPGraph(
        deps=deps,
        event_sink=events,
        checkpoints=checkpoints,
        clock=clock,
        ids=ids,
        policies=config.policies,
        valid_at=VALID_AT,
    )
    return OfflineRuntime(
        graph=graph,
        events=events,
        checkpoints=checkpoints,
        executor=executor,
        corpus=corpus,
        manifests=manifests,
        central_catalog=central_catalog,
        clock=clock,
    )


async def retrieved_evidence(
    message: str,
    domain: Domain,
    intent_slugs: list[str],
    *,
    root: Path | None = None,
) -> list[Any]:
    """La evidencia que el grafo recuperará **de verdad** para esta solicitud.

    Los hechos de un escenario tienen que citar fragmentos de este conjunto: el
    navegador descarta cualquier citación que no esté en la evidencia del run,
    que es justo el control que impide inventar fuentes. Recuperar aquí con otra
    consulta produciría fragmentos legítimos que el verificador rechazaría con
    razón, y la prueba estaría midiendo el fixture en vez del sistema.
    """
    resolved_root = root or repository_root()
    corpus = await load_corpus(root=resolved_root, domains=CORE_DOMAINS)
    manifests = load_domains(resolved_root, CORE_DOMAINS)
    navigator = DomainNavigator(
        domain=domain,
        manifest=manifests[domain],
        gateway=None,  # type: ignore[arg-type]
        retriever=corpus.retriever(domain),
    )
    request = citizen_request(message)
    intents = [_FakeIntent(intent=slug, domain=domain) for slug in intent_slugs]
    query = navigator.query_for(request, intents)  # type: ignore[arg-type]
    return await navigator.retrieve(query, request, VALID_AT)


@dataclass(frozen=True)
class _FakeIntent:
    """Intención mínima para reconstruir la consulta del navegador."""

    intent: str
    domain: Domain


def citizen_request(
    message: str,
    *,
    run_id: str = "run_000001",
    channel: Channel = Channel.WEB,
    received_at: Any = None,
    roles: list[str] | None = None,
    permissions: list[str] | None = None,
) -> RunRequest:
    return RunRequest(
        run_id=run_id,
        trace_id=f"trace_{run_id.removeprefix('run_')}",
        conversation_id="conv_000001",
        user_message=message,
        channel=channel,
        identity=Identity(
            user_id="usr_demo",
            institution_id="inst_demo",
            roles=roles or ["citizen"],
            permissions=permissions
            or [
                "domain:vehiculos:read",
                "domain:registro_civil:read",
                "domain:salud:read",
                "appointment:create",
            ],
        ),
        received_at=received_at or FrozenClock().now(),
    )
