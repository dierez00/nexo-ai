"""Middlewares transversales de la API.

`TraceIdMiddleware` garantiza que cada request tenga un `trace_id` opaco
(prefijo `trace_`), lo expone en `request.state.trace_id` para el logging
estructurado y lo devuelve en el header `X-Trace-Id` de cada respuesta
(convención §9.1: toda respuesta propaga `trace_id`).
"""

from __future__ import annotations

import re
import secrets

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

TRACE_HEADER = "X-Trace-Id"

# El validador canónico de IDs opacos (nexo_contracts) rechaza cuerpos con una
# corrida de >=10 dígitos (posible PII). Un hex aleatorio la produce ~1 de cada 5
# veces, así que regeneramos hasta obtener un cuerpo válido.
_LONG_DIGIT_RUN = re.compile(r"\d{10,}")


def new_trace_id() -> str:
    """Genera un `trace_id` opaco y válido según el contrato (sin corridas de dígitos)."""
    while True:
        body = secrets.token_hex(16)
        if not _LONG_DIGIT_RUN.search(body):
            return f"trace_{body}"


class TraceIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        incoming = request.headers.get(TRACE_HEADER)
        trace_id = incoming if incoming else new_trace_id()
        request.state.trace_id = trace_id

        response = await call_next(request)
        response.headers[TRACE_HEADER] = trace_id
        return response
