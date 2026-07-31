"""Frontera entre el gateway y un proveedor concreto (`DIE-F1-002`).

Un adapter sabe hablar con **un** proveedor y no sabe nada más: ni de aliases,
ni de políticas, ni de presupuesto, ni de fallback. Recibe el nombre del modelo
ya resuelto y devuelve datos crudos más su contabilidad de tokens.

Todo lo que decide —qué alias, cuánto cuesta, qué pasa si falla— vive en el
gateway. Es lo que permite que añadir un proveedor sea escribir un adapter de
treinta líneas en `integrations/models` (responsabilidad de Dani) sin tocar
routing, telemetría ni guardrails.
"""

from __future__ import annotations

from typing import Annotated, Protocol, runtime_checkable

from pydantic import Field, JsonValue

from nexo_contracts import NexoModel, PositiveMillis

from ..ports.model import ChatRequest


class AdapterResult(NexoModel):
    """Lo que devuelve un proveedor: datos crudos y consumo real.

    El costo **no** aparece aquí a propósito. Lo calcula el gateway desde las
    capabilities configuradas, de modo que exista un solo lugar donde el precio
    de un modelo esté escrito y un adapter no pueda reportar un costo distinto
    del que dice la configuración.
    """

    data: Annotated[dict[str, JsonValue], Field(default_factory=dict)]
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    duration_ms: PositiveMillis = 0


@runtime_checkable
class ChatAdapterPort(Protocol):
    """Generación estructurada contra un proveedor concreto.

    Las condiciones de error se expresan como `ModelPortError`, nunca como
    excepciones del SDK: cambiar de proveedor no cambia el manejo de errores de
    ningún agente ni del gateway.
    """

    @property
    def provider(self) -> str:
        """Nombre del proveedor, tal como aparece en `allowed_providers`."""
        ...

    async def generate(
        self,
        request: ChatRequest,
        *,
        model: str,
        output_contract: type[NexoModel] | None,
        max_output_tokens: int,
        timeout_ms: int,
    ) -> AdapterResult:
        """Genera una respuesta con el modelo indicado por la configuración."""
        ...


@runtime_checkable
class EmbeddingsAdapterPort(Protocol):
    """Vectorización contra un proveedor concreto.

    Es el segundo brazo de la «interfaz única para chat estructurado y
    embeddings» (`DIE-F1-001`): mismo mecanismo de aliases, mismo registro de
    consumo, misma normalización de errores.
    """

    @property
    def provider(self) -> str: ...

    @property
    def dimension(self) -> int: ...

    async def embed(self, texts: list[str], *, model: str) -> list[list[float]]:
        """Vectores en el mismo orden que los textos recibidos."""
        ...
