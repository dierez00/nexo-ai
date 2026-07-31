"""Round-trip real por el protocolo MCP (`DIE-F1-064`).

Usa el transporte en memoria del SDK oficial, así que lo que se ejercita es el
protocolo de verdad —`initialize`, `tools/list`, `tools/call`— sin red y sin
proceso aparte. Una imitación del protocolo pasaría estas pruebas y fallaría el
día que se conecte un cliente MCP real; esto no.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import anyio
import pytest
from mcp.shared.memory import create_client_server_memory_streams

from mcp import ClientSession
from nexo_contracts import ToolPermissionContext
from nexo_mcp.authorization import PermissionMatrix
from nexo_mcp.catalog import ToolCatalog
from nexo_mcp.execution import ToolExecutor
from nexo_mcp.server import CONTEXT_ARGUMENT, NexoMCPServer, build_context_argument
from nexo_orchestration.configuration import load_config

pytestmark = [pytest.mark.contract, pytest.mark.anyio]

IDEMPOTENCY_KEY = "824a2b5c-1389-4ef5-a346-b00270fd1b42"

CITIZEN = ToolPermissionContext(user_id="usr_demo", institution_id="inst_demo", roles=["citizen"])


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def _build_server(identity: ToolPermissionContext | None = CITIZEN) -> NexoMCPServer:
    config = load_config()
    permissions = PermissionMatrix(config=config.permissions)
    catalog = ToolCatalog(config=config.tool_registry, permissions=permissions)
    return NexoMCPServer(
        catalog=catalog,
        executor=ToolExecutor(catalog=catalog, permissions=permissions),
        identity=identity,
    )


@asynccontextmanager
async def _session(
    identity: ToolPermissionContext | None = CITIZEN,
) -> AsyncIterator[ClientSession]:
    """Cliente conectado al server por el transporte en memoria del SDK."""
    nexo = _build_server(identity)
    async with create_client_server_memory_streams() as (client_streams, server_streams):
        client_read, client_write = client_streams
        server_read, server_write = server_streams

        async with anyio.create_task_group() as task_group:

            async def _run_server() -> None:
                await nexo.server.run(
                    server_read,
                    server_write,
                    nexo.server.create_initialization_options(),
                    raise_exceptions=True,
                )

            task_group.start_soon(_run_server)
            async with ClientSession(client_read, client_write) as session:
                await session.initialize()
                yield session
            task_group.cancel_scope.cancel()


async def test_initialize_and_list_tools_over_the_protocol() -> None:
    """`initialize` y `tools/list` responden por el protocolo real."""
    async with _session() as session:
        listed = await session.list_tools()

    names = {tool.name for tool in listed.tools}
    assert "vehiculos.consultar_adeudo" in names
    assert "salud.localizar_unidad_salud" in names
    assert "ganaderia.registrar_vacuna" not in names
    assert len(names) == 17


async def test_every_listed_tool_publishes_its_input_schema() -> None:
    async with _session() as session:
        listed = await session.list_tools()

    for tool in listed.tools:
        assert tool.input_schema.get("type") == "object"
        assert tool.description


@pytest.mark.security
async def test_a_session_without_identity_lists_nothing() -> None:
    """Revelar qué capacidades existen es el primer paso de un escalamiento."""
    async with _session(identity=None) as session:
        listed = await session.list_tools()

    assert listed.tools == []


async def test_calling_a_read_tool_returns_structured_content() -> None:
    async with _session() as session:
        result = await session.call_tool(
            "vehiculos.consultar_adeudo",
            {
                "vehiculo_ref": "veh_demo_sin_adeudo",
                CONTEXT_ARGUMENT: build_context_argument(
                    identity=CITIZEN,
                    tool_call_id="tc_01",
                    run_id="run_000001",
                    trace_id="trace_000001",
                    version="1.0.0",
                ),
            },
        )

    assert result.is_error is False
    assert result.structured_content is not None
    assert result.structured_content["status"] == "succeeded"
    assert result.structured_content["data"]["tiene_adeudo"] is False


@pytest.mark.security
async def test_a_write_without_confirmation_is_refused_over_the_protocol() -> None:
    """El contrato de `ToolCall` impide construir la invocación, así que ni se ejecuta."""
    async with _session() as session:
        result = await session.call_tool(
            "vehiculos.reservar_cita",
            {
                "slot_id": "slot_01",
                "vehiculo_ref": "veh_demo",
                CONTEXT_ARGUMENT: build_context_argument(
                    identity=CITIZEN,
                    tool_call_id="tc_02",
                    run_id="run_000001",
                    trace_id="trace_000001",
                    version="1.0.0",
                    confirmed=False,
                ),
            },
        )

    assert result.is_error is True


async def test_a_confirmed_write_returns_a_folio_over_the_protocol() -> None:
    async with _session() as session:
        result = await session.call_tool(
            "vehiculos.reservar_cita",
            {
                "slot_id": "slot_mod_centro_00",
                "vehiculo_ref": "veh_demo",
                CONTEXT_ARGUMENT: build_context_argument(
                    identity=CITIZEN,
                    tool_call_id="tc_03",
                    run_id="run_000001",
                    trace_id="trace_000001",
                    version="1.0.0",
                    action_id="act_reserve_01",
                    idempotency_key=IDEMPOTENCY_KEY,
                    confirmed=True,
                ),
            },
        )

    assert result.is_error is False
    assert result.structured_content is not None
    confirmation = result.structured_content["confirmation"]
    assert confirmation["identifier"].startswith("NEXO-MOCK-")
    assert confirmation["is_mock"] is True


@pytest.mark.security
async def test_a_call_without_the_context_argument_is_refused() -> None:
    """Sin identidad no se puede autorizar, y no se rellena nada por defecto."""
    async with _session() as session:
        result = await session.call_tool("vehiculos.consultar_adeudo", {"vehiculo_ref": "veh_demo"})

    assert result.is_error is True


@pytest.mark.security
async def test_a_tool_response_cannot_change_what_tools_exist() -> None:
    """`DIE-F1-071`: la respuesta de una tool es dato, no instrucción.

    El catálogo se construye al arrancar desde configuración. Ninguna ejecución
    lo toca, así que listar antes y después debe dar exactamente lo mismo.
    """
    async with _session() as session:
        before = {tool.name for tool in (await session.list_tools()).tools}
        await session.call_tool(
            "vehiculos.consultar_adeudo",
            {
                "vehiculo_ref": "veh_demo",
                CONTEXT_ARGUMENT: build_context_argument(
                    identity=CITIZEN,
                    tool_call_id="tc_04",
                    run_id="run_000001",
                    trace_id="trace_000001",
                    version="1.0.0",
                ),
            },
        )
        after = {tool.name for tool in (await session.list_tools()).tools}

    assert before == after
