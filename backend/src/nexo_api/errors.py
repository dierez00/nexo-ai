"""Errores en formato Problem Details (§9, RFC 7807-like).

Toda respuesta de error de la API sale con esta forma para que el frontend
nunca tenga que parsear texto: decide por `type/code/status/retryable`.
"""

from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from nexo_api.middleware import TRACE_HEADER


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
