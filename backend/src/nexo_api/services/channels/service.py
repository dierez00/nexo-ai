"""Caso de uso: mensaje entrante de WhatsApp → run → respuesta TwiML.

Dedup por `provider_message_id`: un webhook repetido no crea otro run ni mensaje
(§13). El remitente se referencia por `pii_ref`, nunca el teléfono crudo.
"""

from __future__ import annotations

from nexo_integrations.twilio import ChannelMessage, build_ack, build_reply
from nexo_observability.logging import get_logger

from nexo_api.repositories import conversations as conv_repo
from nexo_api.repositories import messages as msg_repo
from nexo_api.repositories import runs as runs_repo
from nexo_api.services.orchestration.port import Orchestrator
from nexo_api.services.runs.service import execute_run
from nexo_contracts import Identity, RunStatus

log = get_logger(__name__)

# Sandbox WhatsApp → tenant demo. En real, mapear por el número destino (`to`).
_DEFAULT_TENANT_ID = 1
_FALLBACK_REPLY = "Estamos procesando tu solicitud; por favor intenta de nuevo en un momento."


async def handle_inbound_whatsapp(
    message: ChannelMessage, trace_id: str, orchestrator: Orchestrator
) -> str:
    tenant_id = _DEFAULT_TENANT_ID

    conversation = await conv_repo.find_by_channel_ref(tenant_id, "whatsapp", message.from_ref)
    if conversation is None:
        conversation = await conv_repo.create(
            tenant_id, None, "whatsapp", None, {"from_ref": message.from_ref}
        )
    conversation_id = int(conversation["id"])

    # Dedup: si ya procesamos este provider_message_id, ack sin re-ejecutar.
    if message.provider_message_id and await msg_repo.exists_provider_message(
        conversation_id, message.provider_message_id
    ):
        return build_ack()

    await msg_repo.create(
        conversation_id,
        "user",
        message.text,
        {"provider_message_id": message.provider_message_id, "from_ref": message.from_ref},
    )
    identity = Identity(
        user_id="usr_anon",
        institution_id="inst_1",
        roles=["citizen"],
        permissions=[],
    )
    # Resiliencia: el webhook debe responder 2xx siempre; ante fallo de la
    # orquestación devolvemos un TwiML de fallback en vez de propagar un 500
    # (que dispararía reintentos de Twilio).
    try:
        run_row = await runs_repo.create(
            tenant_id, conversation_id, trace_id, status=RunStatus.QUEUED.value
        )
        result = await execute_run(
            tenant_id,
            conversation_id,
            message.text,
            "whatsapp",
            identity,
            trace_id,
            orchestrator,
            run_row,
        )
        answer = result.answer or _FALLBACK_REPLY
    except Exception as exc:  # noqa: BLE001 - responder 2xx pase lo que pase
        log.warning("whatsapp.run_failed", trace_id=trace_id, error=type(exc).__name__)
        answer = _FALLBACK_REPLY

    await msg_repo.create(conversation_id, "assistant", answer)
    return build_reply(answer)


async def handle_status_callback(message_sid: str, status: str) -> None:
    """Registra el estado de entrega de un mensaje (best-effort + observable).

    Con respuestas TwiML no capturamos el SID saliente, así que la actualización
    por `provider_message_id` es best-effort; el valor operativo es el log
    estructurado del evento de entrega.
    """
    log.info("whatsapp.delivery_status", message_sid=message_sid, status=status)
    if message_sid:
        await msg_repo.set_delivery_status(message_sid, status)
