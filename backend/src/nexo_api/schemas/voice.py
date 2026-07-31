"""DTOs HTTP del canal de voz (ElevenLabs Conversational AI).

El agente de voz es un front-end delgado: manda la petición y recibe la
respuesta ya verificada por el orquestador, de forma síncrona. A diferencia de
`POST /conversations/{id}/messages` (asíncrono, `202` + SSE), este turno espera
el run hasta estado terminal para poder leerlo en voz alta en la misma llamada.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from nexo_contracts import RunStatus


class VoiceTurnRequest(BaseModel):
    """Un turno de la conversación por voz.

    `conversation_id` es opcional: si falta, se crea una conversación de canal
    `voice` y se devuelve para que el agente lo reenvíe en los turnos siguientes.
    `audience`/`locale` son informativos (perfil declarado por la llamada) y se
    guardan en la conversación al crearla.
    """

    conversation_id: str | None = None
    user_message: str = Field(min_length=1, max_length=8000)
    audience: str | None = Field(default=None, max_length=40)
    locale: str | None = Field(default=None, max_length=20)


class VoicePendingAction(BaseModel):
    """Acción de escritura pendiente de confirmación, en forma apta para voz.

    Solo expone lo que el agente necesita para confirmar; nunca los parámetros
    crudos ni el permiso (el resumen legible viaja en `answer`/`label`).
    """

    action_id: str
    tool_name: str
    expected_version: int
    label: str


class VoiceTurnResponse(BaseModel):
    """Respuesta síncrona de un turno de voz, lista para leerse en voz alta."""

    conversation_id: str
    run_id: str
    status: RunStatus
    answer: str | None = None
    questions: list[str] = Field(default_factory=list)
    pending_action: VoicePendingAction | None = None
    warnings: list[str] = Field(default_factory=list)
