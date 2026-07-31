"""Adapter de webhooks de Twilio: verificación de firma, normalización y TwiML.

- Verifica `X-Twilio-Signature` con `RequestValidator` (auth token).
- Normaliza el form de WhatsApp a `ChannelMessage`; el remitente se guarda como
  `pii_ref:` (hash estable), nunca el teléfono crudo (§9.11).
- Construye la respuesta TwiML.
"""

from __future__ import annotations

import hashlib

from pydantic import BaseModel
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse


class ChannelMessage(BaseModel):
    provider_message_id: str
    channel: str
    from_ref: str
    to: str
    text: str


def verify_signature(auth_token: str, url: str, params: dict[str, str], signature: str) -> bool:
    return bool(RequestValidator(auth_token).validate(url, params, signature))


def _pii_ref(raw: str) -> str:
    digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return f"pii_ref:{digest}"


def normalize_whatsapp(params: dict[str, str]) -> ChannelMessage:
    return ChannelMessage(
        provider_message_id=params.get("MessageSid", ""),
        channel="whatsapp",
        from_ref=_pii_ref(params.get("From", "")),
        to=params.get("To", ""),
        text=params.get("Body", ""),
    )


def build_reply(text: str) -> str:
    """Devuelve el XML TwiML con un mensaje de respuesta."""
    response = MessagingResponse()
    response.message(text)
    return str(response)


def build_ack() -> str:
    """TwiML vacío (ack sin responder), p.ej. para mensajes duplicados."""
    return str(MessagingResponse())
