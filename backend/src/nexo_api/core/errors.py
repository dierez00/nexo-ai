"""Errores en formato Problem Details (§9, RFC 7807-like).

Toda respuesta de error de la API sale con esta forma para que el frontend
nunca tenga que parsear texto: decide por `type/code/status/retryable`.
"""

from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from nexo_api.core.middleware import TRACE_HEADER


class ProblemDetail(BaseModel):
    type: str = "about:blank"
    title: str
    status: int
    code: str
    detail: str | None = None
    trace_id: str | None = None
    retryable: bool = False
    errors: list[dict[str, Any]] = Field(default_factory=list)


class ProblemException(Exception):
    """Excepción que se serializa como ProblemDetail."""

    def __init__(
        self,
        *,
        status: int,
        code: str,
        title: str,
        detail: str | None = None,
        retryable: bool = False,
        errors: list[dict[str, Any]] | None = None,
    ) -> None:
        self.problem = ProblemDetail(
            title=title,
            status=status,
            code=code,
            detail=detail,
            retryable=retryable,
            errors=errors or [],
        )
        super().__init__(detail or title)


async def problem_exception_handler(request: Request, exc: ProblemException) -> JSONResponse:
    problem = exc.problem
    problem.trace_id = getattr(request.state, "trace_id", None)
    return JSONResponse(
        status_code=problem.status,
        content=problem.model_dump(),
        headers={TRACE_HEADER: problem.trace_id} if problem.trace_id else None,
    )


# Descripciones por código para documentar los errores en OpenAPI (§9.1).
_PROBLEM_DESCRIPTIONS: dict[int, str] = {
    400: "Error de validación (VALIDATION_ERROR)",
    401: "Autenticación requerida (AUTHENTICATION_REQUIRED)",
    403: "Permiso denegado (PERMISSION_DENIED)",
    404: "Recurso no encontrado (RESOURCE_NOT_FOUND)",
    409: "Conflicto (APPOINTMENT_CONFLICT / VERSION_CONFLICT)",
    422: "Confirmación requerida (ACTION_CONFIRMATION_REQUIRED)",
    429: "Límite excedido (RATE_LIMITED / BUDGET_EXCEEDED)",
}


def problem_responses(*codes: int) -> dict[int | str, dict[str, Any]]:
    """Genera el `responses=` de una ruta documentando errores Problem Details."""
    return {
        code: {"model": ProblemDetail, "description": _PROBLEM_DESCRIPTIONS.get(code, "Error")}
        for code in codes
    }
