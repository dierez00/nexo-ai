"""Recorrido oficial `CAP-EMP-01` y escenarios adversariales (§8.17, §8.18).

«Quiero abrir una taquería en Durango.»

Además del camino feliz, cubre los escenarios críticos de §15 que el MVP debe
sostener: fuente vencida con similitud alta, injection documental, permiso
denegado, escritura con outcome desconocido y fallo del modelo.
"""

from __future__ import annotations

from datetime import date

import pytest

from nexo_contracts import (
    Domain,
    ErrorCode,
    Outcome,
    RetrievalFilters,
    RetrievalQuery,
    RunStatus,
    SourceStatus,
    ToolMode,
)
from nexo_mcp.execution import AdapterFailure
from nexo_orchestration.testing import FakeBehavior, Scenario
from nexo_rag.testing import load_corpus

from .runtime import (
    answer_payload,
    build_runtime,
    citizen_request,
    classification_payload,
    extraction_payload,
)

pytestmark = pytest.mark.e2e

MESSAGE = "Quiero abrir una taquería en Durango"
RUN_ID = "run_000001"


@pytest.fixture(scope="module")
async def permit_fragments() -> dict[str, str]:
    """Fragmentos reales que respaldan cada trámite de la ruta."""
    corpus = await load_corpus()
    retriever = corpus.retriever(Domain.AYUNTAMIENTO_EMPRESAS)
    wanted = {
        "uso_de_suelo": "constancia de uso de suelo para giro comercial",
        "proteccion_civil": "visto bueno de protección civil medidas de seguridad",
        "aviso_sanitario": "aviso de funcionamiento sanitario alimentos",
        "licencia_funcionamiento": "licencia de funcionamiento municipal costo",
    }
    found: dict[str, str] = {}
    for key, query in wanted.items():
        response = await retriever.retrieve(
            RetrievalQuery(
                query=query,
                domain=Domain.AYUNTAMIENTO_EMPRESAS,
                filters=RetrievalFilters(
                    institution_id="inst_demo",
                    status=[SourceStatus.ACTIVE],
                    valid_at=date(2026, 7, 30),
                ),
                top_k=3,
            )
        )
        found[key] = response.results[0].fragment_id
    return found


def _cost_fact(claim: str, minor: int, fragment: str) -> dict[str, object]:
    return {
        "claim": claim,
        "category": "cost",
        "value": {"money": {"amount_minor": minor, "currency": "MXN"}},
        "fragment_ids": [fragment],
        "confidence": 0.94,
    }


@pytest.fixture
async def runtime(permit_fragments):
    facts = [
        _cost_fact(
            "La constancia de uso de suelo cuesta 1180.00 MXN.",
            118000,
            permit_fragments["uso_de_suelo"],
        ),
        _cost_fact(
            "El visto bueno de protección civil cuesta 940.00 MXN.",
            94000,
            permit_fragments["proteccion_civil"],
        ),
        _cost_fact(
            "El aviso de funcionamiento sanitario no genera derechos.",
            0,
            permit_fragments["aviso_sanitario"],
        ),
        _cost_fact(
            "La licencia de funcionamiento municipal cuesta 2350.00 MXN.",
            235000,
            permit_fragments["licencia_funcionamiento"],
        ),
    ]
    return await build_runtime(
        scenarios={
            "classify_request": Scenario(
                data=classification_payload(
                    [("abrir_negocio", "ayuntamiento_empresas")], location="Durango"
                )
            ),
            "navigate_domain": Scenario(
                data=extraction_payload(
                    facts,
                    tools=[
                        "ayuntamiento.consultar_uso_suelo",
                        "ayuntamiento.calcular_costos",
                        "ayuntamiento.consultar_requisitos_negocio",
                        "ayuntamiento.consultar_citas",
                    ],
                    tool_parameters={
                        "ayuntamiento.consultar_uso_suelo": {
                            "giro": "taqueria",
                            "predio_ref": "pred_demo",
                            "superficie_m2": 45,
                        },
                        "ayuntamiento.calcular_costos": {
                            "giro": "taqueria",
                            "tramites": [
                                "uso_de_suelo",
                                "proteccion_civil",
                                "aviso_sanitario",
                                "licencia_funcionamiento",
                            ],
                        },
                        "ayuntamiento.consultar_requisitos_negocio": {"giro": "taqueria"},
                        "ayuntamiento.consultar_citas": {
                            "dependencia": "desarrollo_economico",
                            "desde": "2026-08-05",
                        },
                    },
                )
            ),
            "write_answer": Scenario(
                data=answer_payload("Para abrir tu taquería necesitas cuatro trámites en orden.")
            ),
        }
    )


# --- El recorrido (§8.17) ----------------------------------------------------


async def test_the_route_is_ordered_with_stable_dependencies(runtime) -> None:
    result = await runtime.graph.invoke(citizen_request(MESSAGE))

    assert result.estimate is not None
    order = [step.step_id for step in result.estimate.steps]
    assert order.index("uso_de_suelo") < order.index("proteccion_civil")
    assert order.index("proteccion_civil") < order.index("licencia_funcionamiento")


async def test_the_total_is_summed_in_code_from_verified_costs(runtime) -> None:
    """`DIE-F1-057`: 1180 + 940 + 0 + 2350 = 4470.00 MXN."""
    result = await runtime.graph.invoke(citizen_request(MESSAGE))

    assert result.estimate is not None
    assert result.estimate.total_cost is not None
    assert result.estimate.total_cost.amount_minor == 447000
    assert result.estimate.total_cost.currency == "MXN"


async def test_every_step_traces_back_to_the_facts_that_produced_it(runtime) -> None:
    result = await runtime.graph.invoke(citizen_request(MESSAGE))

    assert result.estimate is not None
    for step in result.estimate.steps:
        assert step.derived_from
        assert step.missing_documents


async def test_the_food_business_requires_the_sanitary_notice(runtime) -> None:
    """Una taquería es un giro de alimentos: el aviso sanitario entra en la ruta."""
    result = await runtime.graph.invoke(citizen_request(MESSAGE))

    assert result.estimate is not None
    assert "aviso_sanitario" in {step.step_id for step in result.estimate.steps}


async def test_the_official_read_tools_return_validated_results(runtime) -> None:
    await runtime.graph.invoke(citizen_request(MESSAGE))
    state = await runtime.checkpoints.load(RUN_ID)

    assert state is not None
    assert {tool.name for tool in state.tool_results} == {
        "ayuntamiento.consultar_uso_suelo",
        "ayuntamiento.calcular_costos",
        "ayuntamiento.consultar_requisitos_negocio",
        "ayuntamiento.consultar_citas",
    }
    assert all(tool.status.value == "succeeded" for tool in state.tool_results)


async def test_the_run_interrupts_before_registering_the_request(runtime) -> None:
    result = await runtime.graph.invoke(citizen_request(MESSAGE))

    assert result.status is RunStatus.WAITING_CONFIRMATION
    assert result.available_actions[0].tool_name == "ayuntamiento.registrar_solicitud"


async def test_the_surface_grows_across_stages_reusing_the_mvp_pipeline(runtime) -> None:
    """Mismo grafo que `CAP-VEH-01`: verify/estimate/build_a2ui aportan cada
    uno su etapa al mismo `surface_id`, sin duplicar lógica por dominio."""
    result = await runtime.graph.invoke(citizen_request(MESSAGE))

    assert result.surface is not None
    surface_ids = {message.surface_id for message in result.surface.messages}
    assert surface_ids == {result.surface.surface_id}
    update_pairs = sum(
        1 for message in result.surface.messages if message.update_data_model is not None
    )
    assert update_pairs >= 3

    events = await runtime.events.read(RUN_ID)
    stages = {
        event.data.get("stage")
        for event in events
        if event.type.value == "a2ui.generated" and isinstance(event.data, dict)
    }
    assert {"verify", "estimate", "build_a2ui"} <= stages


async def test_confirming_returns_a_verifiable_folio(runtime) -> None:
    await runtime.graph.invoke(citizen_request(MESSAGE))
    result = await runtime.graph.resume(RUN_ID, confirmed=True)

    assert result.status is RunStatus.SUCCEEDED
    state = await runtime.checkpoints.load(RUN_ID)
    assert state is not None
    confirmation = state.action_results[0].tool_result.confirmation  # type: ignore[union-attr]
    assert confirmation is not None
    assert confirmation.identifier.startswith("NEXO-MOCK-")
    assert confirmation.is_mock is True


# --- Escenarios críticos de §15 ---------------------------------------------


@pytest.mark.security
async def test_an_expired_source_never_backs_a_cost(permit_fragments) -> None:
    """Escenario 1: fuente sustituida con similitud alta.

    El tarifario de 2024 habla de las mismas tarifas con casi las mismas
    palabras. Si el modelo lo cita, el verificador lo rechaza porque el
    fragmento no está en la evidencia activa que se recuperó.
    """
    runtime = await build_runtime(
        scenarios={
            "classify_request": Scenario(
                data=classification_payload([("abrir_negocio", "ayuntamiento_empresas")])
            ),
            "navigate_domain": Scenario(
                data=extraction_payload(
                    [
                        _cost_fact(
                            "La licencia cuesta 690.00 MXN.",
                            69000,
                            "frag_de_una_fuente_vencida",
                        )
                    ]
                )
            ),
            "write_answer": Scenario(data=answer_payload("No pude confirmar los costos.")),
        }
    )

    result = await runtime.graph.invoke(citizen_request(MESSAGE))

    assert result.verified_facts is not None
    assert result.verified_facts.accepted() == ()
    assert "690" not in (result.answer or "")


@pytest.mark.security
async def test_a_document_injection_never_changes_the_plan() -> None:
    """Escenario 2: injection documental.

    El documento manipulado pide ejecutar la reserva sin confirmación. Lo que
    debe ocurrir es que se recupere marcado, se advierta y el run siga
    interrumpiéndose antes de cualquier escritura.
    """
    runtime = await build_runtime(
        scenarios={
            "classify_request": Scenario(
                data=classification_payload([("localizar_modulo", "vehiculos")])
            ),
            "navigate_domain": Scenario(data=extraction_payload([])),
            "write_answer": Scenario(data=answer_payload("Estos son los módulos.")),
        }
    )

    result = await runtime.graph.invoke(
        citizen_request("nota administrativa sobre horarios de los módulos")
    )

    writes = [call for call in runtime.executor.calls if call.mode is ToolMode.WRITE]
    assert writes == []
    assert result.status is not RunStatus.FAILED


@pytest.mark.security
async def test_a_denied_tool_does_not_stop_the_run(permit_fragments) -> None:
    """Escenario 4: una tool denegada degrada, no rompe."""
    runtime = await build_runtime(
        scenarios={
            "classify_request": Scenario(
                data=classification_payload([("abrir_negocio", "ayuntamiento_empresas")])
            ),
            "navigate_domain": Scenario(
                data=extraction_payload(
                    [
                        _cost_fact(
                            "La constancia de uso de suelo cuesta 1180.00 MXN.",
                            118000,
                            permit_fragments["uso_de_suelo"],
                        )
                    ],
                    tools=["ayuntamiento.consultar_uso_suelo"],
                )
            ),
            "write_answer": Scenario(data=answer_payload("Necesitas uso de suelo.")),
        },
        failures={
            "ayuntamiento.consultar_uso_suelo": AdapterFailure(
                ErrorCode.PERMISSION_DENIED,
                "el actor no está autorizado",
                outcome=Outcome.KNOWN_FAILURE,
            )
        },
    )

    result = await runtime.graph.invoke(citizen_request(MESSAGE))

    assert result.status is not RunStatus.FAILED
    assert result.estimate is not None


@pytest.mark.security
async def test_a_write_with_unknown_outcome_degrades_to_partial(permit_fragments) -> None:
    """Escenario 6: write timeout con outcome desconocido.

    No se reintenta y el run **no** dice que el trámite se hizo.
    """
    runtime = await build_runtime(
        scenarios={
            "classify_request": Scenario(
                data=classification_payload([("abrir_negocio", "ayuntamiento_empresas")])
            ),
            "navigate_domain": Scenario(
                data=extraction_payload(
                    [
                        _cost_fact(
                            "La licencia de funcionamiento municipal cuesta 2350.00 MXN.",
                            235000,
                            permit_fragments["licencia_funcionamiento"],
                        )
                    ]
                )
            ),
            "write_answer": Scenario(data=answer_payload("Tu solicitud está lista.")),
        },
        failures={
            "ayuntamiento.registrar_solicitud": AdapterFailure(
                ErrorCode.UNKNOWN_OUTCOME,
                "se perdió la conexión tras enviar la operación",
                outcome=Outcome.UNKNOWN,
            )
        },
    )

    await runtime.graph.invoke(citizen_request(MESSAGE))
    result = await runtime.graph.resume(RUN_ID, confirmed=True)

    assert result.status is RunStatus.PARTIAL
    writes = [call for call in runtime.executor.calls if call.mode is ToolMode.WRITE]
    assert len(writes) == 1, "una escritura con outcome desconocido no se reintenta"
    assert any("No la repetimos" in warning for warning in result.warnings)


async def test_a_failing_model_still_produces_an_answer(permit_fragments) -> None:
    """El redactor cae a plantilla determinista; el run no se queda mudo."""
    runtime = await build_runtime(
        scenarios={
            "classify_request": Scenario(
                data=classification_payload([("abrir_negocio", "ayuntamiento_empresas")])
            ),
            "navigate_domain": Scenario(
                data=extraction_payload(
                    [
                        _cost_fact(
                            "La constancia de uso de suelo cuesta 1180.00 MXN.",
                            118000,
                            permit_fragments["uso_de_suelo"],
                        )
                    ]
                )
            ),
            "write_answer": Scenario(behavior=FakeBehavior.PROVIDER_DOWN),
        }
    )

    result = await runtime.graph.invoke(citizen_request(MESSAGE))

    assert result.answer
    assert "1180" in result.answer or "1 180" in result.answer


async def test_an_out_of_scope_request_does_not_invent_a_domain() -> None:
    """`DIE-F1-035`: sin dominio no hay ruta, y se dice."""
    runtime = await build_runtime(
        scenarios={
            "classify_request": Scenario(
                data={"intents": [], "entities": {}, "confidence": 0.1, "is_out_of_scope": True}
            ),
            "navigate_domain": Scenario(data=extraction_payload([])),
            "write_answer": Scenario(data=answer_payload("No puedo ayudarte con eso.")),
        }
    )

    result = await runtime.graph.invoke(citizen_request("cómo tramito mi pasaporte"))

    assert result.available_actions == []
    assert any("no corresponde" in warning for warning in result.warnings)
