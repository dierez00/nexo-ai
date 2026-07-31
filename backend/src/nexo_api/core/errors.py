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
from nexo_contracts import HTTP_STATUS_BY_ERROR_CODE, RETRYABLE_ERROR_CODES, ErrorCode


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
        code: ErrorCode | str,
        title: str,
        detail: str | None = None,
        retryable: bool | None = None,
        errors: list[dict[str, Any]] | None = None,
        status: int | None = None,
    ) -> None:
        # La tabla de contratos es la autoridad: los callers no pueden escoger
        # un HTTP/retryable incompatible con el código que publican.
        # `status` se mantiene transitoriamente para no romper routers que aún
        # lo pasen; nunca se usa para construir la respuesta.
        del status, retryable
        try:
            canonical_code = ErrorCode(code)
        except ValueError:
            # Un adapter externo no controla la taxonomía HTTP. Evitamos que un
            # texto arbitrario escape al cliente como código de contrato.
            canonical_code = ErrorCode.PROVIDER_ERROR
        derived_retryable = canonical_code in RETRYABLE_ERROR_CODES
        self.problem = ProblemDetail(
            title=title,
            status=HTTP_STATUS_BY_ERROR_CODE.get(canonical_code, 500),
            code=canonical_code.value,
            detail=detail,
            retryable=derived_retryable,
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
