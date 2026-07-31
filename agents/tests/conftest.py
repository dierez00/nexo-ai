"""Fixtures compartidas de los agentes.

Todo son dobles en memoria con reloj e IDs congelados: ninguna prueba de este
paquete abre red, base de datos ni credenciales.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest

from nexo_agents.domain_manifest import DomainManifest, load_domains
from nexo_contracts import Budgets, Channel, Domain, Identity, RunRequest
from nexo_orchestration.configuration import load_config
from nexo_orchestration.models import BudgetLedger, ModelCallContext, ModelGateway
from nexo_orchestration.testing import (
    FakeChatAdapter,
    FrozenClock,
    Scenario,
    SequentialIdFactory,
)
from nexo_rag.corpus.cli import MVP_DOMAINS, repository_root
from nexo_rag.testing import LoadedCorpus, load_corpus

VALID_AT = date(2026, 7, 30)


@pytest.fixture(scope="session")
def root() -> Path:
    return repository_root()


@pytest.fixture(scope="session")
def manifests(root: Path) -> dict[Domain, DomainManifest]:
    return load_domains(root, MVP_DOMAINS)


@pytest.fixture(scope="module")
async def corpus() -> LoadedCorpus:
    return await load_corpus()


@pytest.fixture
def clock() -> FrozenClock:
    return FrozenClock()


@pytest.fixture
def context() -> ModelCallContext:
    return ModelCallContext(
        run_id="run_000001",
        trace_id="trace_000001",
        ledger=BudgetLedger(budgets=Budgets()),
    )


@pytest.fixture
def gateway_factory(clock: FrozenClock):
    """Construye un gateway con un adapter falso programado por `purpose`."""

    def build(scenarios: dict[str, Any]) -> ModelGateway:
        config = load_config()
        return ModelGateway(
            router=config.model_router,
            outcomes=config.policies.outcomes,
            adapters={"fake": FakeChatAdapter(scenarios, provider="fake")},
            clock=clock,
            ids=SequentialIdFactory(),
        )

    return build


@pytest.fixture
def scenario():
    return Scenario


@pytest.fixture
def request_factory(clock: FrozenClock):
    def build(message: str = "Quiero renovar mi licencia y saber si debo algo") -> RunRequest:
        return RunRequest(
            run_id="run_000001",
            trace_id="trace_000001",
            conversation_id="conv_000001",
            user_message=message,
            channel=Channel.WEB,
            identity=Identity(
                user_id="usr_demo",
                institution_id="inst_demo",
                roles=["citizen"],
                permissions=["domain:vehiculos:read"],
            ),
            received_at=clock.now(),
        )

    return build
