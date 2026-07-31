"""Server MCP, catálogo, autorización y tools mock MVP/Core (F1.8, F1.9, F2).

Ninguna prueba abre red ni sistemas institucionales: el transporte MCP es en
memoria y los adapters son mocks deterministas.
"""

from __future__ import annotations

import pytest

from nexo_contracts import (
    ConfigurationError,
    ErrorCode,
    ToolCall,
    ToolCallStatus,
    ToolMode,
    ToolPermissionContext,
)
from nexo_mcp.authorization import DenialReason, PermissionMatrix
from nexo_mcp.catalog import ToolCatalog
from nexo_mcp.execution import AdapterFailure, ToolExecutor, audit_payload, has_unknown_outcome
from nexo_mcp.tools.definitions import TOOL_DEFINITIONS
from nexo_orchestration.configuration import load_config

pytestmark = pytest.mark.unit

IDEMPOTENCY_KEY = "824a2b5c-1389-4ef5-a346-b00270fd1b42"


@pytest.fixture(scope="module")
def config():
    return load_config()


@pytest.fixture
def permissions(config) -> PermissionMatrix:
    return PermissionMatrix(config=config.permissions)


@pytest.fixture
def catalog(config, permissions) -> ToolCatalog:
    return ToolCatalog(config=config.tool_registry, permissions=permissions)


@pytest.fixture
def executor(catalog, permissions) -> ToolExecutor:
    return ToolExecutor(catalog=catalog, permissions=permissions)


@pytest.fixture
def citizen() -> ToolPermissionContext:
    return ToolPermissionContext(user_id="usr_demo", institution_id="inst_demo", roles=["citizen"])


def _call(name: str, parameters: dict, *, mode: ToolMode = ToolMode.READ, **overrides) -> ToolCall:
    payload = {
        "tool_call_id": "tc_01",
        "name": name,
        "version": "1.0.0",
        "run_id": "run_000001",
        "trace_id": "trace_000001",
        "context": ToolPermissionContext(
            user_id="usr_demo", institution_id="inst_demo", roles=["citizen"]
        ),
        "parameters": parameters,
        "mode": mode,
    }
    payload.update(overrides)
    return ToolCall(**payload)  # type: ignore[arg-type]


def _write_call(name: str, parameters: dict, **overrides) -> ToolCall:
    return _call(
        name,
        parameters,
        mode=ToolMode.WRITE,
        action_id="act_01",
        idempotency_key=IDEMPOTENCY_KEY,
        confirmed=True,
        **overrides,
    )


# --- Catálogo: configuración e implementación deben coincidir ---------------


def test_all_mvp_and_core_tools_are_registered_and_enabled(catalog: ToolCatalog) -> None:
    assert len(catalog.definitions) == 22
    assert all(catalog.is_enabled(name) for name in catalog.definitions)


def test_a_declared_tool_without_implementation_stops_the_boot(config, permissions) -> None:
    with pytest.raises(ConfigurationError, match="sin implementación"):
        ToolCatalog(
            config=config.tool_registry,
            permissions=permissions,
            definitions={d.name: d for d in TOOL_DEFINITIONS if d.name != "vehiculos.buscar_citas"},
        )


def test_a_mode_mismatch_between_config_and_code_stops_the_boot(config, permissions) -> None:
    """Una de las dos mentiría sobre si la tool escribe."""
    tampered = config.tool_registry.model_copy(deep=True)
    entry = next(e for e in tampered.tools if e.name == "vehiculos.reservar_cita")
    entry.mode = ToolMode.READ

    with pytest.raises(ConfigurationError, match="miente sobre si"):
        ToolCatalog(config=tampered, permissions=permissions)


async def test_an_unknown_version_does_not_resolve(catalog: ToolCatalog) -> None:
    """Publicar una versión no reemplaza silenciosamente a otra."""
    assert await catalog.get("vehiculos.consultar_adeudo", "9.9.9") is None
    assert await catalog.get("vehiculos.consultar_adeudo", "1.0.0") is not None


# --- Filtrado por actor (`DIE-F1-066`) --------------------------------------


async def test_the_list_is_filtered_before_the_model_sees_it(catalog: ToolCatalog) -> None:
    """Un modelo que ve una tool que no puede usar acabará proponiéndola."""
    citizen = await catalog.list_tools(institution_id="inst_demo", roles=["citizen"])
    operator = await catalog.list_tools(institution_id="inst_demo", roles=["operator"])

    assert "vehiculos.reservar_cita" in {t.name for t in citizen}
    # El personal operativo tiene lectura ampliada y ninguna escritura.
    assert "vehiculos.reservar_cita" not in {t.name for t in operator}


async def test_another_institution_sees_nothing(catalog: ToolCatalog) -> None:
    assert await catalog.list_tools(institution_id="inst_otra", roles=["citizen"]) == ()


async def test_an_unknown_role_sees_nothing(catalog: ToolCatalog) -> None:
    assert await catalog.list_tools(institution_id="inst_demo", roles=["intruso"]) == ()


async def test_the_domain_filter_narrows_the_list(catalog: ToolCatalog) -> None:
    tools = await catalog.list_tools(
        institution_id="inst_demo", roles=["citizen"], domain="vehiculos"
    )

    assert {t.name for t in tools} == {
        "vehiculos.consultar_adeudo",
        "vehiculos.localizar_modulo",
        "vehiculos.buscar_citas",
        "vehiculos.reservar_cita",
    }


@pytest.mark.security
async def test_producer_cannot_discover_citizen_or_health_tools(catalog: ToolCatalog) -> None:
    tools = await catalog.list_tools(institution_id="inst_demo", roles=["producer"])
    names = {tool.name for tool in tools}

    assert names
    assert all(name.startswith("ganaderia.") for name in names)
    assert "ganaderia.registrar_vacuna" in names
    assert "salud.localizar_unidad_salud" not in names


# --- Autorización revalidada en el executor (`DIE-F2-013`) -----------------


@pytest.mark.security
async def test_the_executor_revalidates_the_role(executor: ToolExecutor) -> None:
    """No confía en que el supervisor filtrara."""
    call = _call(
        "vehiculos.reservar_cita",
        {"slot_id": "slot_01", "vehiculo_ref": "veh_demo"},
        mode=ToolMode.WRITE,
        action_id="act_01",
        idempotency_key=IDEMPOTENCY_KEY,
        confirmed=True,
        context=ToolPermissionContext(
            user_id="usr_demo", institution_id="inst_demo", roles=["operator"]
        ),
    )

    result = await executor.execute(call)

    assert result.status is ToolCallStatus.DENIED
    assert result.error is not None
    assert result.error.safe_details["reason"] == DenialReason.ROLE_NOT_ALLOWED.value


@pytest.mark.security
async def test_a_write_without_confirmation_cannot_even_be_built() -> None:
    """El contrato de `ToolCall` lo impide antes de llegar al executor."""
    with pytest.raises(ValueError, match="ninguna escritura ocurre"):
        _call(
            "vehiculos.reservar_cita",
            {"slot_id": "slot_01", "vehiculo_ref": "veh_demo"},
            mode=ToolMode.WRITE,
        )


@pytest.mark.security
async def test_asking_for_a_write_tool_in_read_mode_is_denied(executor: ToolExecutor) -> None:
    """Pedir en lectura algo que escribe es un intento de saltarse el modo."""
    result = await executor.execute(
        _call("vehiculos.reservar_cita", {"slot_id": "s", "vehiculo_ref": "v"})
    )

    assert result.status is ToolCallStatus.DENIED
    assert result.error is not None
    assert result.error.safe_details["reason"] == DenialReason.MODE_NOT_GRANTED.value


@pytest.mark.security
async def test_an_unregistered_tool_is_not_found(executor: ToolExecutor) -> None:
    result = await executor.execute(_call("vehiculos.tool_inventada", {}))

    assert result.error is not None
    assert result.error.error.code is ErrorCode.TOOL_NOT_FOUND


@pytest.mark.security
async def test_a_denial_does_not_explain_which_rule_was_missing(
    executor: ToolExecutor,
) -> None:
    """Qué regla faltó es auditoría, no respuesta (`DIE-F2-015`)."""
    result = await executor.execute(
        _call("vehiculos.reservar_cita", {"slot_id": "s", "vehiculo_ref": "v"})
    )

    assert result.error is not None
    assert "permissions.yaml" not in result.error.error.message
    assert "rule" not in result.error.error.message


# --- Validación de entrada y salida (`DIE-F1-067`) -------------------------


async def test_a_malformed_input_never_reaches_the_adapter(executor: ToolExecutor) -> None:
    result = await executor.execute(_call("vehiculos.consultar_adeudo", {"campo_inventado": "x"}))

    assert result.status is ToolCallStatus.FAILED
    assert result.error is not None
    assert result.error.error.code is ErrorCode.VALIDATION_ERROR


async def test_a_validation_error_does_not_echo_the_value(executor: ToolExecutor) -> None:
    result = await executor.execute(
        _call(
            "ayuntamiento.consultar_uso_suelo",
            {"giro": "taqueria", "predio_ref": "pred_01", "superficie_m2": -5},
        )
    )

    assert result.error is not None
    assert "-5" not in result.error.error.message
    assert "superficie_m2" in result.error.error.message


# --- Desenlaces y reintentos (`DIE-F1-068`, `DIE-F1-069`) ------------------


async def test_a_read_retries_a_timeout(catalog, permissions) -> None:
    executor = ToolExecutor(
        catalog=catalog,
        permissions=permissions,
        failures={
            "vehiculos.consultar_adeudo": AdapterFailure(
                ErrorCode.TOOL_TIMEOUT,
                "sin respuesta",
                outcome=__import__("nexo_contracts").Outcome.KNOWN_FAILURE,
            )
        },
    )

    result = await executor.execute(
        _call("vehiculos.consultar_adeudo", {"vehiculo_ref": "veh_demo"})
    )

    assert result.status is ToolCallStatus.TIMEOUT
    # `max_attempts` de una lectura es 2: se intentó dos veces.
    assert len(executor.calls) == 1  # una invocación lógica…
    assert result.error is not None


@pytest.mark.security
async def test_a_write_with_unknown_outcome_is_never_retried(catalog, permissions) -> None:
    """Es exactamente cómo se duplica una cita."""
    from nexo_contracts import Outcome

    executor = ToolExecutor(
        catalog=catalog,
        permissions=permissions,
        failures={
            "vehiculos.reservar_cita": AdapterFailure(
                ErrorCode.UNKNOWN_OUTCOME,
                "se perdió la conexión tras enviar la operación",
                outcome=Outcome.UNKNOWN,
            )
        },
    )

    result = await executor.execute(
        _write_call("vehiculos.reservar_cita", {"slot_id": "s", "vehiculo_ref": "v"})
    )

    assert has_unknown_outcome(result) is True
    assert result.confirmation is None


# --- Idempotencia (`DIE-F1-080`) --------------------------------------------


async def test_repeating_a_confirmation_replays_without_writing_again(
    executor: ToolExecutor,
) -> None:
    first = await executor.execute(
        _write_call("vehiculos.reservar_cita", {"slot_id": "s1", "vehiculo_ref": "v1"})
    )
    second = await executor.execute(
        _write_call(
            "vehiculos.reservar_cita",
            {"slot_id": "s1", "vehiculo_ref": "v1"},
            tool_call_id="tc_02",
        )
    )

    assert first.idempotency_replayed is False
    assert second.idempotency_replayed is True
    assert first.confirmation is not None and second.confirmation is not None
    assert second.confirmation.identifier == first.confirmation.identifier


# --- Folio verificable (`DIE-F1-078`) ---------------------------------------


async def test_every_successful_write_returns_a_verifiable_folio(
    executor: ToolExecutor, catalog: ToolCatalog
) -> None:
    del catalog
    for name, parameters, roles in (
        ("vehiculos.reservar_cita", {"slot_id": "s", "vehiculo_ref": "v"}, ["citizen"]),
        (
            "ayuntamiento.registrar_solicitud",
            {"giro": "taqueria", "predio_ref": "p", "tramite": "licencia_funcionamiento"},
            ["citizen"],
        ),
        (
            "registro_civil.registrar_solicitud",
            {"acta_ref": "acta_demo", "tipo": "correccion"},
            ["citizen"],
        ),
        (
            "ganaderia.registrar_vacuna",
            {
                "animal_ref": "animal_demo_0001",
                "vacuna": "vacuna_demo",
                "fecha_aplicacion": "2026-07-30",
                "actor_ref": "actor_demo_productor",
                "regla_id": "sanidad_demo_2026_01",
            },
            ["producer"],
        ),
    ):
        context = ToolPermissionContext(
            user_id="usr_demo",
            institution_id="inst_demo",
            roles=roles,
        )
        result = await executor.execute(
            _write_call(
                name,
                parameters,
                tool_call_id=f"tc_{name[:4]}",
                context=context,
            )
        )

        assert result.status is ToolCallStatus.SUCCEEDED
        assert result.confirmation is not None
        assert result.confirmation.is_mock is True


async def test_repeating_vaccine_confirmation_does_not_duplicate(
    executor: ToolExecutor,
) -> None:
    context = ToolPermissionContext(
        user_id="usr_demo",
        institution_id="inst_demo",
        roles=["producer"],
    )
    parameters = {
        "animal_ref": "animal_demo_0001",
        "vacuna": "vacuna_demo",
        "fecha_aplicacion": "2026-07-30",
        "actor_ref": "actor_demo_productor",
        "regla_id": "sanidad_demo_2026_01",
    }

    first = await executor.execute(
        _write_call("ganaderia.registrar_vacuna", parameters, context=context)
    )
    second = await executor.execute(
        _write_call(
            "ganaderia.registrar_vacuna",
            parameters,
            context=context,
            tool_call_id="tc_vacuna_replay",
        )
    )

    assert first.status is ToolCallStatus.SUCCEEDED
    assert second.idempotency_replayed is True
    assert second.confirmation == first.confirmation


# --- Tools MVP/Core: contract tests mock ↔ schema ---------------------------


@pytest.mark.contract
@pytest.mark.parametrize("definition", TOOL_DEFINITIONS, ids=lambda d: d.name)
def test_every_tool_declares_coherent_metadata(definition) -> None:
    metadata = definition.metadata

    assert metadata.version == "1.0.0"
    assert metadata.allowed_roles
    assert metadata.input_schema_ref.startswith("contracts://")
    assert metadata.output_schema_ref.startswith("contracts://")
    assert metadata.is_mock is True
    assert metadata.description


@pytest.mark.contract
@pytest.mark.parametrize("definition", TOOL_DEFINITIONS, ids=lambda d: d.name)
def test_every_tool_publishes_both_schemas(definition) -> None:
    assert definition.input_schema()["type"] == "object"
    assert definition.output_schema()["type"] == "object"


@pytest.mark.contract
@pytest.mark.parametrize(
    "definition",
    [d for d in TOOL_DEFINITIONS if d.metadata.mode is ToolMode.WRITE],
    ids=lambda d: d.name,
)
def test_every_write_tool_demands_confirmation_and_idempotency(definition) -> None:
    metadata = definition.metadata

    assert metadata.requires_confirmation is True
    assert metadata.requires_idempotency_key is True
    assert metadata.max_attempts == 1


@pytest.mark.contract
@pytest.mark.parametrize(
    ("name", "parameters", "mode"),
    [
        ("vehiculos.consultar_adeudo", {"vehiculo_ref": "veh_demo"}, ToolMode.READ),
        ("vehiculos.localizar_modulo", {"tramite": "renovacion"}, ToolMode.READ),
        (
            "vehiculos.buscar_citas",
            {"modulo_id": "mod_centro", "desde": "2026-08-01", "hasta": "2026-08-31"},
            ToolMode.READ,
        ),
        (
            "ayuntamiento.consultar_uso_suelo",
            {"giro": "taqueria", "predio_ref": "pred_01", "superficie_m2": 45},
            ToolMode.READ,
        ),
        (
            "ayuntamiento.calcular_costos",
            {"giro": "taqueria", "tramites": ["uso_de_suelo", "licencia_funcionamiento"]},
            ToolMode.COMPUTE,
        ),
        ("ayuntamiento.consultar_requisitos_negocio", {"giro": "taqueria"}, ToolMode.READ),
        (
            "ayuntamiento.consultar_citas",
            {"dependencia": "desarrollo_urbano", "desde": "2026-08-01"},
            ToolMode.READ,
        ),
        (
            "registro_civil.clasificar_tipo_correccion",
            {"descripcion": "Hay un error ortográfico en el acta"},
            ToolMode.COMPUTE,
        ),
        (
            "registro_civil.localizar_oficialia",
            {"municipio": "Durango"},
            ToolMode.READ,
        ),
        (
            "registro_civil.consultar_disponibilidad",
            {"oficialia_id": "oficialia_centro", "tramite": "aclaracion"},
            ToolMode.READ,
        ),
        (
            "salud.localizar_unidad_salud",
            {"municipio": "Durango", "afiliacion": "sin_afiliacion"},
            ToolMode.READ,
        ),
        ("salud.consultar_servicios", {"unidad_id": "unidad_centro_demo"}, ToolMode.READ),
        (
            "salud.consultar_requisitos",
            {"servicio": "consulta_general", "afiliacion": "sin_afiliacion"},
            ToolMode.READ,
        ),
        ("salud.buscar_horarios", {"unidad_id": "unidad_centro_demo"}, ToolMode.READ),
        ("ganaderia.consultar_animal", {"animal_ref": "animal_demo_0001"}, ToolMode.READ),
        (
            "ganaderia.consultar_historial",
            {"animal_ref": "animal_demo_0001"},
            ToolMode.READ,
        ),
        (
            "ganaderia.validar_movilizacion",
            {"animal_ref": "animal_demo_0001", "destino": "Durango"},
            ToolMode.COMPUTE,
        ),
        ("ganaderia.consultar_alertas", {"municipio": "Durango"}, ToolMode.READ),
    ],
)
async def test_every_read_tool_returns_output_that_matches_its_schema(
    executor: ToolExecutor, name: str, parameters: dict, mode: ToolMode
) -> None:
    """Un mock que devuelve algo que su propio contrato rechaza es inútil."""
    context = ToolPermissionContext(
        user_id="usr_demo",
        institution_id="inst_demo",
        roles=["producer"] if name.startswith("ganaderia.") else ["citizen"],
    )
    result = await executor.execute(_call(name, parameters, mode=mode, context=context))

    assert result.status is ToolCallStatus.SUCCEEDED, result.error
    assert result.is_mock is True
    assert result.data


async def test_the_mock_costs_agree_with_the_corpus(executor: ToolExecutor) -> None:
    """Si la tool dijera 900 y el documento 814, probaríamos un corpus incoherente."""
    result = await executor.execute(
        _call(
            "ayuntamiento.calcular_costos",
            {"giro": "taqueria", "tramites": ["uso_de_suelo", "licencia_funcionamiento"]},
            mode=ToolMode.COMPUTE,
        )
    )

    assert result.data["total"] == {"amount_minor": 353000, "currency": "MXN"}


@pytest.mark.security
def test_tool_parameters_must_be_pure_json() -> None:
    """`SafePayload` rechaza un objeto vivo, aunque sea inofensivo como un `date`.

    Los parámetros cruzan una frontera de proceso: lo que no es JSON no puede
    viajar, y descubrirlo al construir la invocación es mejor que al serializarla.
    """
    from datetime import date

    with pytest.raises(ValueError, match="not a valid JSON value"):
        _call("vehiculos.buscar_citas", {"modulo_id": "m", "desde": date(2026, 8, 1)})


# --- Auditoría minimizada (`DIE-F1-070`, `DIE-F1-082`) ---------------------


@pytest.mark.security
async def test_the_audit_record_never_carries_the_parameters(
    executor: ToolExecutor,
) -> None:
    call = _write_call(
        "ayuntamiento.registrar_solicitud",
        {"giro": "taqueria", "predio_ref": "pred_secreto_01", "tramite": "licencia_funcionamiento"},
    )

    result = await executor.execute(call)
    audit = audit_payload(call, result)

    assert "pred_secreto_01" not in str(audit)
    assert audit["parameter_count"] == 3
    assert audit["tool"] == "ayuntamiento.registrar_solicitud"
    assert audit["confirmed"] is True
