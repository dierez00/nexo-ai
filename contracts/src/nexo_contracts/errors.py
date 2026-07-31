"""Errores normalizados (`DIE-F0-008`).

Todo fallo que cruza una frontera se representa igual: código estable,
reintentabilidad explícita, certeza sobre el efecto y detalles seguros. Ningún
consumidor decide leyendo el texto del mensaje.
"""

from __future__ import annotations

from typing import Annotated, Any, Self

from pydantic import Field, model_validator

from .base import NexoModel
from .enums import RETRYABLE_ERROR_CODES, ErrorCode, Outcome

HTTP_STATUS_BY_ERROR_CODE: dict[ErrorCode, int] = {
    ErrorCode.VALIDATION_ERROR: 400,
    ErrorCode.CONTRACT_INVALID: 400,
    ErrorCode.AUTHENTICATION_REQUIRED: 401,
    ErrorCode.PERMISSION_DENIED: 403,
    ErrorCode.RESOURCE_NOT_FOUND: 404,
    ErrorCode.TOOL_NOT_FOUND: 404,
    ErrorCode.APPOINTMENT_CONFLICT: 409,
    ErrorCode.VERSION_CONFLICT: 409,
    ErrorCode.ACTION_CONFIRMATION_REQUIRED: 422,
    ErrorCode.RATE_LIMITED: 429,
    ErrorCode.BUDGET_EXCEEDED: 429,
    ErrorCode.PROVIDER_ERROR: 502,
    ErrorCode.MODEL_OUTPUT_INVALID: 502,
    ErrorCode.MODEL_UNAVAILABLE: 503,
    ErrorCode.CONFIGURATION_INVALID: 503,
    ErrorCode.UNKNOWN_OUTCOME: 503,
    ErrorCode.TOOL_TIMEOUT: 504,
    ErrorCode.RUN_TIMEOUT: 504,
    ErrorCode.RUN_CANCELLED: 499,
}
"""Traducción a HTTP para que Dani construya Problem Details sin reinterpretar códigos."""


class ErrorDetail(NexoModel):
    """Detalle accionable de un error, sin contenido sensible."""

    field: str | None = Field(
        default=None,
        description="Ruta del campo que falló, en notación de puntos.",
        max_length=200,
    )
    reason: str = Field(
        description="Motivo estable y corto, en snake_case. Ejemplo: 'conflict'.",
        max_length=200,
    )


class NormalizedError(NexoModel):
    """Error normalizado que cruza cualquier frontera de Nexo IA.

    `outcome` es el campo que impide reintentos peligrosos: un `UNKNOWN`
    significa que no sabemos si la operación tuvo efecto, y por tanto nunca se
    reintenta de forma automática (`DIE-F0-035`).
    """

    code: ErrorCode
    message: str = Field(
        max_length=500,
        description="Mensaje para operadores. Nunca incluye prompts, secretos ni PII.",
    )
    retryable: bool = Field(
        description="Si la operación puede reintentarse tal cual, sin intervención.",
    )
    outcome: Outcome = Field(
        default=Outcome.KNOWN_FAILURE,
        description="Certeza sobre el efecto producido antes del fallo.",
    )
    details: Annotated[list[ErrorDetail], Field(max_length=50)] = Field(default_factory=list)
    retry_after_ms: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _reject_retryable_unknown_outcome(self) -> Self:
        if self.retryable and self.outcome is Outcome.UNKNOWN:
            raise ValueError(
                "un error con outcome desconocido no puede marcarse reintentable: "
                "reintentarlo podría duplicar un efecto ya aplicado"
            )
        return self

    @property
    def http_status(self) -> int:
        return HTTP_STATUS_BY_ERROR_CODE.get(self.code, 500)

    @classmethod
    def from_code(
        cls,
        code: ErrorCode,
        message: str,
        *,
        outcome: Outcome = Outcome.KNOWN_FAILURE,
        details: list[ErrorDetail] | None = None,
        **extra: Any,
    ) -> NormalizedError:
        """Construye el error derivando `retryable` de la tabla canónica."""
        retryable = code in RETRYABLE_ERROR_CODES and outcome is not Outcome.UNKNOWN
        return cls(
            code=code,
            message=message,
            retryable=retryable,
            outcome=outcome,
            details=details or [],
            **extra,
        )


class ConfigurationError(Exception):
    """Configuración inválida detectada en el arranque (`DIE-F0-036`).

    Lleva ruta, campo y motivo para que el fallo sea accionable sin depurar.
    """

    def __init__(self, path: str, field: str, reason: str) -> None:
        self.path = path
        self.field = field
        self.reason = reason
        super().__init__(f"{path}: campo '{field}' inválido — {reason}")
