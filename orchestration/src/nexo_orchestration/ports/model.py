"""Puerto del gateway de modelos (`DIE-F0-021`).

Un agente pide un modelo por **alias** y declara qué contrato debe cumplir la
salida. Nunca conoce el proveedor, el SDK ni el nombre comercial del modelo: eso
lo resuelve el gateway leyendo configuración (§2.3).

La petición incluye `purpose`, una clave de escenario estable. Es lo que permite
que un modelo falso responda de forma programada sin hacer matching frágil sobre
el texto completo del prompt (`DIE-F0-022`).
"""

from __future__ import annotations

from typing import Annotated, Protocol, runtime_checkable

from pydantic import Field, JsonValue

from nexo_contracts import (
    ModelAlias,
    ModelDecision,
    ModelInvocation,
    ModelTaskKind,
    NexoModel,
    NormalizedError,
    PositiveMillis,
    SafePayload,
    Slug,
)


class ChatRequest(NexoModel):
    """Solicitud de generación estructurada dirigida al gateway."""

    purpose: Slug = Field(
        description=(
            "Clave estable del punto de invocación, por ejemplo 'classify_request'. "
            "Los dobles de prueba responden por esta clave, no por el texto del prompt."
        )
    )
    task_kind: ModelTaskKind
    alias: ModelAlias
    output_contract: str = Field(
        max_length=120,
        description="Nombre del contrato publicado que debe cumplir la salida.",
    )
    prompt: str = Field(max_length=100_000)
    prompt_version: str = Field(default="v1", max_length=40)
    variables: SafePayload
    deadline_ms: PositiveMillis = 8000
    max_cost_usd: float = Field(default=0.05, ge=0.0)
    attempt: int = Field(default=1, ge=1, le=5)


class ChatResponse(NexoModel):
    """Respuesta del gateway: datos crudos más la contabilidad de la invocación.

    `data` es JSON puro. Validarlo contra `output_contract` es responsabilidad
    de quien llama, no del puerto: así el gateway no necesita conocer el registro
    de contratos y el fallback por salida inválida se decide en un solo lugar.
    """

    data: Annotated[dict[str, JsonValue], Field(default_factory=dict)]
    decision: ModelDecision
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    estimated_cost_usd: float = Field(default=0.0, ge=0.0)
    duration_ms: PositiveMillis = 0


@runtime_checkable
class ChatModelPort(Protocol):
    """Generación estructurada detrás de un alias.

    Las condiciones de error se expresan como `ModelPortError`, nunca como
    excepciones del SDK de un proveedor: cambiar de proveedor no debe cambiar el
    manejo de errores de ningún agente.
    """

    async def generate(self, request: ChatRequest) -> ChatResponse:
        """Genera una respuesta estructurada para la solicitud dada."""
        ...


class ModelPortError(Exception):
    """Fallo normalizado del puerto de modelos.

    Transporta un `NormalizedError` para que el router decida el fallback con el
    mismo código estable que después registrará en el evento.
    """

    def __init__(
        self,
        error: NormalizedError,
        *,
        invocations: tuple[ModelInvocation, ...] = (),
        input_tokens: int = 0,
        output_tokens: int = 0,
        duration_ms: int = 0,
    ) -> None:
        self.error = error
        self.invocations = invocations
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.duration_ms = duration_ms
        super().__init__(f"{error.code.value}: {error.message}")
