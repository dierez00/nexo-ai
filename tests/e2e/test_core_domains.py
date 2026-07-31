"""Recorridos oficiales Core: CAP-RC-01, CAP-SAL-01 y CAP-GAN-01."""

from __future__ import annotations

import pytest

from nexo_contracts import ActionStatus, Domain, RunStatus
from nexo_orchestration.testing import Scenario

from .runtime import (
    answer_payload,
    build_runtime,
    citizen_request,
    classification_payload,
    extraction_payload,
    retrieved_evidence,
)

pytestmark = pytest.mark.e2e


async def _fragment(message: str, domain: Domain, intent: str, source_id: str) -> str:
    evidence = await retrieved_evidence(message, domain, [intent])
    return next(item.fragment_id for item in evidence if item.source_id == source_id)


async def test_cap_rc_01_asks_only_the_indispensable_question_and_routes() -> None:
    message = "Mi acta tiene un error y no sé si es aclaración o corrección"
    fragment = await _fragment(
        message,
        Domain.REGISTRO_CIVIL,
        "corregir_acta",
        "src_rc_tramites",
    )
    runtime = await build_runtime(
        scenarios={
            "classify_request": Scenario(
                data=classification_payload([("corregir_acta", "registro_civil")])
            ),
            "navigate_domain": Scenario(
                data=extraction_payload(
                    [
                        {
                            "claim": (
                                "Una corrección que cambia datos sustantivos requiere revisión "
                                "de la oficialía."
                            ),
                            "category": "requirement",
                            "value": {"text": "revision_oficialia"},
                            "fragment_ids": [fragment],
                            "confidence": 0.95,
                        }
                    ],
                    tools=[
                        "registro_civil.clasificar_tipo_correccion",
                        "registro_civil.localizar_oficialia",
                        "registro_civil.consultar_disponibilidad",
                    ],
                    tool_parameters={
                        "registro_civil.clasificar_tipo_correccion": {
                            "descripcion": message,
                        },
                        "registro_civil.localizar_oficialia": {"municipio": "Durango"},
                        "registro_civil.consultar_disponibilidad": {
                            "oficialia_id": "oficialia_centro",
                            "tramite": "correccion",
                        },
                    },
                    question=(
                        "¿El acta tiene un error de captura o necesitas cambiar un dato de fondo?"
                    ),
                )
            ),
            "write_answer": Scenario(
                data=answer_payload(
                    "La ruta depende de si es un error de captura o un cambio de fondo."
                )
            ),
        }
    )

    result = await runtime.graph.invoke(citizen_request(message))
    state = await runtime.checkpoints.load("run_000001")

    assert result.status is RunStatus.WAITING_CONFIRMATION
    assert result.questions == [
        "¿El acta tiene un error de captura o necesitas cambiar un dato de fondo?"
    ]
    assert result.metrics.question_count == 1
    assert result.skill_id == "skill_rc_correccion"
    assert result.catalog_version == "core-catalog-2026-07-30"
    assert result.surface is not None
    assert result.surface.catalog_id.endswith("citizen:v1")
    assert state is not None
    assert {tool.name for tool in state.tool_results} == {
        "registro_civil.clasificar_tipo_correccion",
        "registro_civil.localizar_oficialia",
        "registro_civil.consultar_disponibilidad",
    }


async def test_cap_sal_01_returns_only_administrative_navigation() -> None:
    message = "¿Dónde está la unidad de salud y qué requisitos pide para consulta general?"
    fragment = await _fragment(
        message,
        Domain.SALUD,
        "localizar_unidad",
        "src_sal_directorio",
    )
    runtime = await build_runtime(
        scenarios={
            "classify_request": Scenario(
                data=classification_payload([("localizar_unidad", "salud")])
            ),
            "navigate_domain": Scenario(
                data=extraction_payload(
                    [
                        {
                            "claim": (
                                "La unidad aplicable depende del municipio y de la afiliación."
                            ),
                            "category": "location",
                            "value": {"text": "unidad_por_municipio_y_afiliacion"},
                            "fragment_ids": [fragment],
                            "confidence": 0.96,
                        }
                    ],
                    tools=[
                        "salud.localizar_unidad_salud",
                        "salud.consultar_servicios",
                        "salud.consultar_requisitos",
                        "salud.buscar_horarios",
                    ],
                    tool_parameters={
                        "salud.localizar_unidad_salud": {
                            "municipio": "Durango",
                            "afiliacion": "sin_afiliacion",
                        },
                        "salud.consultar_servicios": {
                            "unidad_id": "unidad_centro_demo",
                        },
                        "salud.consultar_requisitos": {
                            "servicio": "consulta_general",
                            "afiliacion": "sin_afiliacion",
                        },
                        "salud.buscar_horarios": {
                            "unidad_id": "unidad_centro_demo",
                        },
                    },
                )
            ),
            "write_answer": Scenario(
                data=answer_payload(
                    "Puedo ayudarte con la unidad, sus requisitos y horarios administrativos."
                )
            ),
        }
    )

    result = await runtime.graph.invoke(citizen_request(message))
    state = await runtime.checkpoints.load("run_000001")

    assert result.status is RunStatus.SUCCEEDED
    assert result.available_actions == []
    assert result.skill_id == "skill_sal_navegacion"
    assert result.sources
    assert result.surface is not None
    assert state is not None
    assert len(state.tool_results) == 4
    assert all(tool.name.startswith("salud.") for tool in state.tool_results)


@pytest.mark.security
async def test_health_clinical_request_is_blocked_by_a_deterministic_gate() -> None:
    message = "Diagnostica qué tengo y dime qué medicamento y dosis debo tomar"
    runtime = await build_runtime(
        scenarios={
            "classify_request": Scenario(
                data=classification_payload([("consultar_servicio", "salud")])
            )
        }
    )

    result = await runtime.graph.invoke(citizen_request(message))
    state = await runtime.checkpoints.load("run_000001")

    assert result.answer is not None
    assert "[salud-seguridad]" in result.answer
    assert result.available_actions == []
    assert state is not None
    assert state.tool_results == []
    assert len(state.model_invocations) == 1


async def test_cap_gan_01_registers_a_vaccine_once_with_rule_actor_and_folio() -> None:
    message = "Registré una vacuna al animal autorizado y quiero actualizar su historial"
    fragment = await _fragment(
        message,
        Domain.GANADERIA,
        "registrar_vacuna",
        "src_gan_expediente",
    )
    runtime = await build_runtime(
        scenarios={
            "classify_request": Scenario(
                data=classification_payload([("registrar_vacuna", "ganaderia")])
            ),
            "navigate_domain": Scenario(
                data=extraction_payload(
                    [
                        {
                            "claim": (
                                "Una vacuna nueva exige nombre, fecha, confirmación expresa "
                                "e idempotencia."
                            ),
                            "category": "requirement",
                            "value": {"text": "vacuna_confirmada_e_idempotente"},
                            "fragment_ids": [fragment],
                            "confidence": 0.96,
                        }
                    ],
                    tools=[
                        "ganaderia.consultar_animal",
                        "ganaderia.consultar_historial",
                    ],
                    tool_parameters={
                        "ganaderia.consultar_animal": {
                            "animal_ref": "animal_demo_001",
                        },
                        "ganaderia.consultar_historial": {
                            "animal_ref": "animal_demo_001",
                        },
                    },
                )
            ),
            "write_answer": Scenario(
                data=answer_payload(
                    "El expediente está listo para confirmar un registro de vacuna."
                )
            ),
        }
    )
    request = citizen_request(
        message,
        roles=["producer"],
        permissions=["domain:ganaderia:read", "domain:ganaderia:write"],
    )

    waiting = await runtime.graph.invoke(request)
    completed = await runtime.graph.resume("run_000001", confirmed=True)
    repeated = await runtime.graph.resume("run_000001", confirmed=True)
    state = await runtime.checkpoints.load("run_000001")

    assert waiting.status is RunStatus.WAITING_CONFIRMATION
    assert waiting.available_actions[0].tool_name == "ganaderia.registrar_vacuna"
    assert completed.status is RunStatus.SUCCEEDED
    assert repeated.status is RunStatus.SUCCEEDED
    assert state is not None
    assert len(state.action_results) == 1
    action = state.action_results[0]
    assert action.status is ActionStatus.SUCCEEDED
    assert action.tool_result is not None
    assert action.tool_result.confirmation is not None
    assert action.tool_result.data["actor_ref"] == "actor_demo_productor"
    assert action.tool_result.data["regla_id"] == "sanidad_demo_2026_01"
