"""Caso de uso: mensaje entrante de WhatsApp → run → respuesta TwiML.

Dedup por `provider_message_id`: un webhook repetido no crea otro run ni mensaje
(§13). El remitente se referencia por `pii_ref`, nunca el teléfono crudo.
"""

from __future__ import annotations

from nexo_integrations.twilio import ChannelMessage, build_ack, build_reply

from nexo_api.repositories import conversations as conv_repo
from nexo_api.repositories import messages as msg_repo
from nexo_api.repositories import runs as runs_repo
from nexo_api.services.orchestration.port import Orchestrator
from nexo_api.services.runs.service import execute_run
from nexo_contracts import Identity, RunStatus

# Sandbox WhatsApp → tenant demo. En real, mapear por el número destino (`to`).
_DEFAULT_TENANT_ID = 1


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
    answer = result.answer or "No fue posible generar una respuesta."
    await msg_repo.create(conversation_id, "assistant", answer)
    return build_reply(answer)
