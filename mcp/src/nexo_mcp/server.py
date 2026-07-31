"""Server MCP: `initialize`, `tools/list` y `tools/call` (`DIE-F1-064`).

Usa el SDK oficial en vez de imitar el protocolo. La frontera de MCP es de
proceso y protocolo (ADR 0005), y una imitación divergiría el día que Dani
conecte un cliente MCP de verdad —que es exactamente el día en que uno menos
quiere descubrirlo.

**Lo que este server no hace es tan importante como lo que hace.** No decide el
plan del run, no almacena conocimiento documental y, sobre todo, **la respuesta
de una tool no puede cambiar nada** (`DIE-F1-071`): ni la allowlist, ni los
permisos, ni qué tools existen. El catálogo se construye al arrancar desde
configuración, y una `tool_result` es datos que se devuelven, no instrucciones
que se obedecen.

El identity context viaja fuera del payload de la tool, en el argumento
reservado `_nexo_context`. Si viajara dentro de los parámetros, un modelo que
redacta parámetros podría escribir su propio rol.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from mcp.server import Server

# El SDK no reexporta `ServerRequestContext` en su `__all__`; se importa del
# módulo donde vive porque es el tipo del contexto que recibe cada handler.
from mcp.server.lowlevel.server import ServerRequestContext  # type: ignore[attr-defined]

from mcp import types
from nexo_contracts import ToolCall, ToolMode, ToolPermissionContext, ToolResult

from .catalog import ToolCatalog
from .execution import ToolExecutor

SERVER_NAME = "nexo-ia-mcp"
SERVER_VERSION = "1.0.0"

# Argumento reservado por el que viaja la identidad. Empieza por `_` para que no
# colisione con ningún campo de un input schema.
CONTEXT_ARGUMENT = "_nexo_context"


@dataclass
class NexoMCPServer:
    """Server MCP de Nexo IA sobre el catálogo y el executor configurados."""

    catalog: ToolCatalog
    executor: ToolExecutor
    identity: ToolPermissionContext | None = None

    def __post_init__(self) -> None:
        self.server: Server[ToolPermissionContext | None] = Server(
            SERVER_NAME,
            version=SERVER_VERSION,
            instructions=(
                "Tools de trámites de Nexo IA. Toda escritura exige confirmación "
                "explícita e idempotency key."
            ),
            lifespan=self._lifespan,
            on_list_tools=self._on_list_tools,
            on_call_tool=self._on_call_tool,
        )

    @asynccontextmanager
    async def _lifespan(
        self, server: Server[ToolPermissionContext | None]
    ) -> AsyncIterator[ToolPermissionContext | None]:
        """La identidad de la sesión, negociada fuera del payload de la tool.

        Vive en el lifespan y no en los argumentos porque un modelo que redacta
        parámetros no debe poder escribir su propio rol.
        """
        del server
        yield self.identity

    # -- tools/list ---------------------------------------------------------

    async def _on_list_tools(
        self,
        context: ServerRequestContext[ToolPermissionContext | None],
        params: types.PaginatedRequestParams | None,
    ) -> types.ListToolsResult:
        """Lista las tools visibles para el actor de la sesión.

        Sin identidad no se lista **nada**. Devolver el catálogo completo «para
        que el cliente filtre» sería revelar qué capacidades existen a quien no
        puede usarlas, y ese es el primer paso de un escalamiento.
        """
        identity = _identity_from(context)
        if identity is None:
            return types.ListToolsResult(tools=[])

        metadata = await self.catalog.list_tools(
            institution_id=identity.institution_id, roles=list(identity.roles)
        )
        return types.ListToolsResult(
            tools=[
                types.Tool(
                    name=item.name,
                    description=item.description,
                    inputSchema=self._input_schema(item.name),
                    # El modo y el riesgo viajan como metadata para que un
                    # cliente pueda pedir confirmación por su cuenta. No la
                    # sustituyen: el executor la exige igual.
                    _meta={
                        "nexo/version": item.version,
                        "nexo/domain": item.domain.value,
                        "nexo/mode": item.mode.value,
                        "nexo/risk": item.risk.value,
                        "nexo/requires_confirmation": item.requires_confirmation,
                        "nexo/is_mock": item.is_mock,
                    },
                )
                for item in metadata
            ]
        )

    def _input_schema(self, name: str) -> dict[str, Any]:
        definition = self.catalog.definitions[name]
        return dict(definition.input_schema())

    # -- tools/call ---------------------------------------------------------

    async def _on_call_tool(
        self,
        context: ServerRequestContext[ToolPermissionContext | None],
        params: types.CallToolRequestParams,
    ) -> types.CallToolResult:
        """Ejecuta una tool. Un fallo viaja como resultado, no como excepción."""
        arguments = dict(params.arguments or {})
        raw_context = arguments.pop(CONTEXT_ARGUMENT, None)

        call = _build_call(params.name, arguments, raw_context, self.catalog)
        if call is None:
            return _error_result(
                "la invocación no declara identidad ni versión de tool; no se puede autorizar"
            )

        result = await self.executor.execute(call)
        return _to_mcp_result(result)


def _identity_from(
    context: ServerRequestContext[ToolPermissionContext | None],
) -> ToolPermissionContext | None:
    """Identidad negociada en la sesión, si el cliente la declaró."""
    raw = getattr(context, "lifespan_context", None)
    if isinstance(raw, ToolPermissionContext):
        return raw
    return None


def _build_call(
    name: str,
    arguments: dict[str, Any],
    raw_context: object,
    catalog: ToolCatalog,
) -> ToolCall | None:
    """Construye el `ToolCall` tipado desde el payload MCP.

    Devuelve `None` si el payload no permite construir una invocación
    autorizable. No se rellena nada por defecto: un `confirmed` que se asume
    verdadero es una escritura sin consentimiento.
    """
    if not isinstance(raw_context, dict):
        return None

    definition = catalog.definitions.get(name)
    if definition is None:
        return None

    try:
        identity = ToolPermissionContext.model_validate(raw_context.get("identity", {}))
    except ValueError:
        return None

    mode = definition.metadata.mode
    try:
        return ToolCall(
            tool_call_id=raw_context.get("tool_call_id", "tc_unknown"),
            name=name,
            version=raw_context.get("version", definition.version),
            run_id=raw_context.get("run_id", "run_unknown"),
            trace_id=raw_context.get("trace_id", "trace_unknown"),
            context=identity,
            parameters=arguments,
            action_id=raw_context.get("action_id"),
            idempotency_key=raw_context.get("idempotency_key"),
            confirmed=bool(raw_context.get("confirmed", False)),
            mode=mode,
        )
    except ValueError:
        # El contrato de `ToolCall` impide construir una escritura sin
        # consentimiento, acción e idempotencia. Que falle aquí es correcto.
        return None


def _to_mcp_result(result: ToolResult) -> types.CallToolResult:
    """Proyecta el resultado tipado al formato del protocolo."""
    payload = result.model_dump_wire()
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=json.dumps(payload, ensure_ascii=False))],
        structuredContent=payload,
        isError=result.error is not None,
    )


def _error_result(message: str) -> types.CallToolResult:
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=message)],
        isError=True,
    )


def build_context_argument(
    *,
    identity: ToolPermissionContext,
    tool_call_id: str,
    run_id: str,
    trace_id: str,
    version: str,
    mode: ToolMode = ToolMode.READ,
    action_id: str | None = None,
    idempotency_key: str | None = None,
    confirmed: bool = False,
) -> dict[str, Any]:
    """Arma el argumento reservado que transporta identidad y consentimiento.

    Existe para que el cliente no lo construya a mano: un `confirmed` puesto por
    descuido es la diferencia entre una consulta y una escritura.
    """
    del mode  # el modo lo decide el catálogo, no quien llama
    return {
        "identity": identity.model_dump(mode="json"),
        "tool_call_id": tool_call_id,
        "run_id": run_id,
        "trace_id": trace_id,
        "version": version,
        "action_id": action_id,
        "idempotency_key": idempotency_key,
        "confirmed": confirmed,
    }
