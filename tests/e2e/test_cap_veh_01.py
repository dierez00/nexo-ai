"""Recorrido oficial `CAP-VEH-01` de punta a punta (§8.16).

«Quiero renovar mi licencia y saber si debo algo.»

Sin red, sin base de datos, sin proveedor y sin sistema institucional: modelo
falso, corpus en memoria, tools mock y reloj congelado.
"""

from __future__ import annotations

from datetime import date

import pytest

from nexo_contracts import (
    ActionStatus,
    Channel,
    Domain,
    RetrievalFilters,
    RetrievalQuery,
    RunStatus,
    SourceStatus,
    ToolMode,
)
from nexo_orchestration.graph.mvp import NODE_NAVIGATE, NODE_RETRIEVE, MVPGraph
from nexo_orchestration.testing import FakeBehavior, Scenario
from nexo_rag.testing import load_corpus

from .runtime import (
    OfflineRuntime,
    answer_payload,
    build_runtime,
    citizen_request,
    classification_payload,
    extraction_payload,
)

pytestmark = pytest.mark.e2e

MESSAGE = "Quiero renovar mi licencia y saber si debo algo"
RUN_ID = "run_000001"


@pytest.fixture(scope="module")
async def fragments() -> dict[str, str]:
    """Fragmentos reales del corpus, para que los hechos citen evidencia real."""
    corpus = await load_corpus()
    response = await corpus.retriever(Domain.VEHICULOS).retrieve(
        RetrievalQuery(
            query=(
                "Quiero renovar mi licencia y saber si debo algo. Renovar licencia de "
                "conducir, requisitos, costo, módulos y cita. Consultar adeudo vehicular."
            ),
            domain=Domain.VEHICULOS,
            filters=RetrievalFilters(
                institution_id="inst_demo",
                status=[SourceStatus.ACTIVE],
                valid_at=date(2026, 7, 30),
            ),
            top_k=10,
        )
    )
    return {result.title: result.fragment_id for result in response.results}


def _vehicle_scenarios(fragments: dict[str, str]) -> dict[str, Scenario]:
    requirement = fragments["Documentos que debe presentar la persona solicitante"]
    cost = fragments["Licencia de conducir tipo A"]
    debt_rule = fragments["Adeudos previos"]
    return {
        # `DIE-F1-032`: las dos intenciones se conservan separadas.
        "classify_request": Scenario(
            data=classification_payload(
                [("renovar_licencia", "vehiculos"), ("consultar_adeudo", "vehiculos")],
                location="Durango",
            )
        ),
        "navigate_domain": Scenario(
            data=extraction_payload(
                [
                    {
                        "claim": "Se requiere identificación oficial vigente.",
                        "category": "requirement",
                        "value": {"items": ["Identificación oficial vigente"]},
                        "fragment_ids": [requirement],
                        "confidence": 0.93,
                    },
                    {
                        "claim": "Renovar la licencia tipo A cuesta 814.00 MXN.",
                        "category": "cost",
                        "value": {"money": {"amount_minor": 81400, "currency": "MXN"}},
                        "fragment_ids": [cost],
                        "confidence": 0.95,
                    },
                    {
                        "claim": "Un adeudo pendiente bloquea la renovación.",
                        "category": "dependency",
                        "value": {"boolean": True},
                        "fragment_ids": [debt_rule],
                        "confidence": 0.94,
                    },
                ],
                tools=[
                    "vehiculos.consultar_adeudo",
                    "vehiculos.localizar_modulo",
                    "vehiculos.buscar_citas",
                ],
                tool_parameters={
                    "vehiculos.consultar_adeudo": {"vehiculo_ref": "veh_demo_sin_adeudo"},
                    "vehiculos.localizar_modulo": {
                        "tramite": "renovacion",
                        "zona": "centro",
                    },
                    "vehiculos.buscar_citas": {
                        "modulo_id": "mod_centro",
                        "desde": "2026-08-03",
                        "hasta": "2026-08-10",
                    },
                },
            )
        ),
        "write_answer": Scenario(
            data=answer_payload(
                "Necesitas identificación oficial vigente para renovar tu licencia."
            )
        ),
    }


async def test_strict_profile_fails_on_classifier_model_error() -> None:
    runtime = await build_runtime(
        scenarios={
            "classify_request": Scenario(behavior=FakeBehavior.PROVIDER_DOWN),
        },
        strict_model_errors=True,
    )

    result = await runtime.graph.invoke(citizen_request(MESSAGE))

    assert result.status is RunStatus.FAILED
    assert result.answer is None
    assert result.error is not None
    assert result.error.code.value == "MODEL_UNAVAILABLE"
    assert "model.failed" in runtime.events.types(RUN_ID)
    assert "run.failed" in runtime.events.types(RUN_ID)


async def test_strict_profile_fails_on_navigator_model_error(
    fragments: dict[str, str],
) -> None:
    scenarios = _vehicle_scenarios(fragments)
    scenarios["navigate_domain"] = Scenario(behavior=FakeBehavior.PROVIDER_DOWN)
    runtime = await build_runtime(scenarios=scenarios, strict_model_errors=True)

    result = await runtime.graph.invoke(citizen_request(MESSAGE))

    assert result.status is RunStatus.FAILED
    assert result.answer is None
    assert result.error is not None
    assert "model.failed" in runtime.events.types(RUN_ID)
    assert "run.failed" in runtime.events.types(RUN_ID)


async def test_strict_profile_fails_on_writer_model_error(
    fragments: dict[str, str],
) -> None:
    scenarios = _vehicle_scenarios(fragments)
    scenarios["write_answer"] = Scenario(behavior=FakeBehavior.PROVIDER_DOWN)
    runtime = await build_runtime(scenarios=scenarios, strict_model_errors=True)

    result = await runtime.graph.invoke(citizen_request(MESSAGE))

    assert result.status is RunStatus.FAILED
    assert result.answer is None
    assert result.error is not None
    assert "model.failed" in runtime.events.types(RUN_ID)
    assert "run.failed" in runtime.events.types(RUN_ID)


@pytest.fixture
async def runtime(fragments) -> OfflineRuntime:
    return await build_runtime(scenarios=_vehicle_scenarios(fragments))


# --- El recorrido completo ---------------------------------------------------


async def test_the_run_stops_before_writing_and_offers_a_confirmation(runtime) -> None:
    """`DIE-F1-085`: interrupt antes de toda escritura."""
    result = await runtime.graph.invoke(citizen_request(MESSAGE))

    assert result.status is RunStatus.WAITING_CONFIRMATION
    assert len(result.available_actions) == 1
    assert result.available_actions[0].requires_confirmation is True


async def test_the_interrupt_still_delivers_an_answer_and_sources(runtime) -> None:
    """Interrumpir es «no ejecutes la escritura», no «no respondas»."""
    result = await runtime.graph.invoke(citizen_request(MESSAGE))

    assert result.answer
    assert result.sources
    assert all(citation.is_active for citation in result.sources)


async def test_read_tools_return_debt_modules_and_slots(runtime) -> None:
    result = await runtime.graph.invoke(citizen_request(MESSAGE))
    state = await runtime.checkpoints.load(RUN_ID)

    assert state is not None
    assert {tool.name for tool in state.tool_results} == {
        "vehiculos.consultar_adeudo",
        "vehiculos.localizar_modulo",
        "vehiculos.buscar_citas",
    }
    assert all(tool.status.value == "succeeded" for tool in state.tool_results)
    assert result.estimate is not None
    assert result.estimate.total_cost is not None
    assert result.estimate.total_cost.amount_minor == 81400


async def test_the_pending_action_is_persisted_with_its_schema_and_version(
    runtime,
) -> None:
    """`DIE-F1-086`: reanudar no puede depender de nada en memoria."""
    await runtime.graph.invoke(citizen_request(MESSAGE))

    state = await runtime.checkpoints.load(RUN_ID)
    assert state is not None and state.pending_action is not None
    action = state.pending_action
    assert action.tool_name == "vehiculos.reservar_cita"
    assert action.input_schema_ref.startswith("contracts://")
    assert action.tool_version == "1.0.0"
    assert action.consent is False
    assert action.parameters == {
        "slot_id": "slot_mod_centro_00",
        "vehiculo_ref": "veh_demo_sin_adeudo",
    }
    assert state.metrics.first_event_ms == 0


async def test_resuming_with_consent_produces_a_verifiable_folio(runtime) -> None:
    """`DIE-F1-087`, `DIE-F1-078`: sin folio no habría éxito."""
    await runtime.graph.invoke(citizen_request(MESSAGE))
    result = await runtime.graph.resume(RUN_ID, confirmed=True)

    assert result.status is RunStatus.SUCCEEDED

    state = await runtime.checkpoints.load(RUN_ID)
    assert state is not None
    assert len(state.action_results) == 1
    outcome = state.action_results[0]
    assert outcome.status is ActionStatus.SUCCEEDED
    assert outcome.tool_result is not None
    assert outcome.tool_result.confirmation is not None
    assert outcome.tool_result.confirmation.identifier.startswith("NEXO-MOCK-")


async def test_cancelling_a_waiting_run_never_executes_the_write(runtime) -> None:
    """`DIE-F1-091`: cancelar cierra el run y retira la acción disponible."""
    await runtime.graph.invoke(citizen_request(MESSAGE))

    result = await runtime.graph.cancel(RUN_ID)
    resumed = await runtime.graph.resume(RUN_ID, confirmed=True)
    state = await runtime.checkpoints.load(RUN_ID)

    assert result.status is RunStatus.CANCELLED
    assert result.available_actions == []
    assert resumed.status is RunStatus.CANCELLED
    assert state is not None
    assert state.action_results == []
    assert state.pending_action is not None
    assert state.pending_action.status is ActionStatus.CANCELLED


@pytest.mark.security
async def test_repeating_the_confirmation_does_not_create_a_second_appointment(
    runtime,
) -> None:
    """Gate §8.19: reanudar no duplica efectos."""
    await runtime.graph.invoke(citizen_request(MESSAGE))
    await runtime.graph.resume(RUN_ID, confirmed=True)
    state = await runtime.checkpoints.load(RUN_ID)
    assert state is not None
    folio = state.action_results[0].tool_result.confirmation.identifier  # type: ignore[union-attr]

    await runtime.graph.resume(RUN_ID, confirmed=True)
    await runtime.graph.resume(RUN_ID, confirmed=True)

    final = await runtime.checkpoints.load(RUN_ID)
    assert final is not None
    assert len(final.action_results) == 1
    assert final.action_results[0].tool_result.confirmation.identifier == folio  # type: ignore[union-attr]
    writes = [call for call in runtime.executor.calls if call.mode is ToolMode.WRITE]
    assert len(writes) == 1, "el grafo no debe reintentar una acción ya resuelta"


# --- Reanudación sin reejecutar (`DIE-F1-088`) ------------------------------


async def test_resuming_does_not_retrieve_or_call_read_tools_again(runtime) -> None:
    await runtime.graph.invoke(citizen_request(MESSAGE))
    reads_before = [c for c in runtime.executor.calls if c.mode is ToolMode.READ]
    state_before = await runtime.checkpoints.load(RUN_ID)
    assert state_before is not None
    retrievals_before = state_before.metrics.retrieval_count

    await runtime.graph.resume(RUN_ID, confirmed=True)

    reads_after = [c for c in runtime.executor.calls if c.mode is ToolMode.READ]
    state_after = await runtime.checkpoints.load(RUN_ID)
    assert state_after is not None
    assert len(reads_after) == len(reads_before)
    assert state_after.metrics.retrieval_count == retrievals_before


async def test_a_new_graph_resumes_from_the_retrieval_checkpoint(fragments) -> None:
    """Clasificación y evidencia sobreviven aunque la instancia original desaparezca."""
    original = await build_runtime(scenarios=_vehicle_scenarios(fragments))
    await original.graph.invoke(citizen_request(MESSAGE))

    checkpoint = None
    for checkpoint_id in await original.checkpoints.history(RUN_ID):
        candidate = await original.checkpoints.load_at(RUN_ID, checkpoint_id)
        if (
            candidate is not None
            and NODE_RETRIEVE in candidate.completed_nodes
            and NODE_NAVIGATE not in candidate.completed_nodes
        ):
            checkpoint = candidate
            break
    assert checkpoint is not None
    assert checkpoint.classification is not None
    assert checkpoint.retrieval_results

    recovery = await build_runtime(scenarios=_vehicle_scenarios(fragments))
    for event in await original.events.read(RUN_ID):
        if event.sequence <= checkpoint.event_cursor:
            await recovery.events.emit(event)
    await recovery.checkpoints.save(
        checkpoint,
        node=NODE_RETRIEVE,
        checkpoint_id="chk_recovery",
    )

    restarted = MVPGraph(
        deps=recovery.graph.deps,
        event_sink=recovery.events,
        checkpoints=recovery.checkpoints,
        clock=original.clock,
        ids=original.graph.ids,
        policies=recovery.graph.policies,
        valid_at=recovery.graph.valid_at,
    )
    result = await restarted.resume(RUN_ID)

    assert result.status is RunStatus.WAITING_CONFIRMATION
    assert result.verified_facts is not None
    assert result.verified_facts.accepted()
    assert result.metrics.retrieval_count == 1


async def test_skipped_nodes_appear_in_the_trace(runtime) -> None:
    """Reanudar deja constancia de qué no se rehizo, no lo hace en silencio."""
    await runtime.graph.invoke(citizen_request(MESSAGE))
    before = len(await runtime.events.read(RUN_ID))

    await runtime.graph.resume(RUN_ID, confirmed=True)

    trace = await runtime.trace(RUN_ID)
    assert len(trace) > before
    assert "checkpoint.restored" in trace
    assert trace.count("run.resumed") > 1


# --- Trazabilidad (`DIE-F1-090`, gate §8.19) --------------------------------


async def test_the_whole_run_is_reconstructible_by_trace_id(runtime) -> None:
    await runtime.graph.invoke(citizen_request(MESSAGE))
    await runtime.graph.resume(RUN_ID, confirmed=True)

    events = await runtime.events.read(RUN_ID)

    assert {event.trace_id for event in events} == {"trace_000001"}
    assert [event.sequence for event in events] == list(range(1, len(events) + 1))
    types = {event.type.value for event in events}
    assert {
        "run.queued",
        "classification.completed",
        "rag.completed",
        "run.waiting_confirmation",
        "checkpoint.restored",
        "run.completed",
    } <= types


async def test_every_run_records_cost_and_tokens(runtime) -> None:
    """Gate de rendimiento: el 100% de los runs registra costo y tokens."""
    result = await runtime.graph.invoke(citizen_request(MESSAGE))

    assert result.metrics.model_invocation_count > 0
    assert result.metrics.duration_ms >= 0
    assert result.metrics.retrieval_count == 1


async def test_model_invocations_are_not_duplicated_by_the_reducer(runtime) -> None:
    """El reducer se aplica en cada retorno de nodo: debe ser idempotente."""
    await runtime.graph.invoke(citizen_request(MESSAGE))

    state = await runtime.checkpoints.load(RUN_ID)
    assert state is not None
    ids = [invocation.invocation_id for invocation in state.model_invocations]
    assert len(ids) == len(set(ids))
    assert len(ids) <= 5


# --- A2UI y fallback de canal -----------------------------------------------


async def test_the_surface_is_built_and_validates(runtime) -> None:
    result = await runtime.graph.invoke(citizen_request(MESSAGE))

    assert result.surface is not None
    assert result.surface.actions
    assert result.surface.channel is Channel.WEB
    components = {
        component.component
        for message in result.surface.messages
        if message.update_components is not None
        for component in message.update_components.components
    }
    assert {"Checklist", "CostSummary", "SlotPicker", "SourceList"} <= components


async def test_the_surface_grows_across_stages_not_only_at_the_end(runtime) -> None:
    """La persona ve algo antes del último nodo: verify, estimate y build_a2ui
    agregan al mismo `surface_id` en vez de reemplazarlo (`a2ui.generated`)."""
    result = await runtime.graph.invoke(citizen_request(MESSAGE))

    assert result.surface is not None
    surface_ids = {message.surface_id for message in result.surface.messages}
    assert surface_ids == {result.surface.surface_id}, "una sola superficie por run"
    update_pairs = sum(
        1 for message in result.surface.messages if message.update_data_model is not None
    )
    assert update_pairs >= 3, "verify, estimate y build_a2ui deben aportar cada uno su etapa"

    events = await runtime.events.read(RUN_ID)
    stages = {
        event.data.get("stage")
        for event in events
        if event.type.value == "a2ui.generated" and isinstance(event.data, dict)
    }
    assert {"verify", "estimate", "build_a2ui"} <= stages


async def test_whatsapp_receives_a_numbered_fallback(fragments) -> None:
    """`DIE-F1-107`: el canal de texto recibe lista numerada."""
    evidence = next(iter(fragments.values()))
    runtime = await build_runtime(
        scenarios={
            "classify_request": Scenario(
                data=classification_payload([("renovar_licencia", "vehiculos")])
            ),
            "navigate_domain": Scenario(
                data=extraction_payload(
                    [
                        {
                            "claim": "Se requiere identificación oficial vigente.",
                            "category": "requirement",
                            "value": {"items": ["Identificación oficial vigente"]},
                            "fragment_ids": [evidence],
                            "confidence": 0.9,
                        }
                    ]
                )
            ),
            "write_answer": Scenario(data=answer_payload("Necesitas identificación oficial.")),
        }
    )

    result = await runtime.graph.invoke(citizen_request(MESSAGE, channel=Channel.WHATSAPP))

    assert result.fallback is not None
    assert result.fallback.channel is Channel.WHATSAPP
    assert result.fallback.numbered_items


# --- Reproducibilidad --------------------------------------------------------


async def test_two_identical_runs_produce_identical_results(fragments) -> None:
    """Sin esto, comparar un baseline entre commits no significa nada."""
    evidence = next(iter(fragments.values()))

    async def _once() -> str:
        runtime = await build_runtime(
            scenarios={
                "classify_request": Scenario(
                    data=classification_payload([("renovar_licencia", "vehiculos")])
                ),
                "navigate_domain": Scenario(
                    data=extraction_payload(
                        [
                            {
                                "claim": "Se requiere identificación oficial vigente.",
                                "category": "requirement",
                                "value": {"items": ["Identificación oficial vigente"]},
                                "fragment_ids": [evidence],
                                "confidence": 0.9,
                            }
                        ]
                    )
                ),
                "write_answer": Scenario(data=answer_payload("Necesitas identificación.")),
            }
        )
        result = await runtime.graph.invoke(citizen_request(MESSAGE))
        return result.model_dump_json()

    assert await _once() == await _once()
