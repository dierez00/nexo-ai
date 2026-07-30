"""Middlewares transversales de la API.

`TraceIdMiddleware` garantiza que cada request tenga un `trace_id` opaco
(prefijo `trace_`), lo expone en `request.state.trace_id` para el logging
estructurado y lo devuelve en el header `X-Trace-Id` de cada respuesta
(convención §9.1: toda respuesta propaga `trace_id`).
"""

from __future__ import annotations

import secrets

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

TRACE_HEADER = "X-Trace-Id"


def new_trace_id() -> str:
    """Genera un ID opaco con prefijo `trace_`."""
    return f"trace_{secrets.token_hex(16)}"


class TraceIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        incoming = request.headers.get(TRACE_HEADER)
        trace_id = incoming if incoming else new_trace_id()
        request.state.trace_id = trace_id

        response = await call_next(request)
        response.headers[TRACE_HEADER] = trace_id
        return response
