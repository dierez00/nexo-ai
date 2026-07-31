"""Webhooks de Twilio (firmados). No usan auth de usuario: la seguridad es la firma."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from nexo_integrations.twilio import normalize_whatsapp, verify_signature

from nexo_api.api.deps import get_orchestrator
from nexo_api.core.config import get_settings
from nexo_api.core.errors import ProblemException, problem_responses
from nexo_api.services.channels import service as channels_service
from nexo_api.services.orchestration import Orchestrator

router = APIRouter(prefix="/webhooks/twilio", tags=["webhooks"])


def _webhook_url(request: Request) -> str:
    # Twilio firma la URL pública exacta; se arma con PUBLIC_BASE_URL + path.
    base = get_settings().public_base_url.rstrip("/")
    return f"{base}{request.url.path}"


async def _read_and_validate(request: Request) -> dict[str, str]:
    form = await request.form()
    params = {key: str(value) for key, value in form.items()}
    signature = request.headers.get("X-Twilio-Signature", "")
    token = get_settings().twilio_auth_token.get_secret_value()
    if not verify_signature(token, _webhook_url(request), params, signature):
        raise ProblemException(
            status=403, code="PERMISSION_DENIED", title="Firma de Twilio inválida"
        )
    return params


@router.post("/whatsapp", summary="Webhook WhatsApp entrante", responses=problem_responses(403))
async def whatsapp(
    request: Request,
    orchestrator: Orchestrator = Depends(get_orchestrator),
) -> Response:
    params = await _read_and_validate(request)
    message = normalize_whatsapp(params)
    trace_id: str = request.state.trace_id
    twiml = await channels_service.handle_inbound_whatsapp(message, trace_id, orchestrator)
    return Response(content=twiml, media_type="application/xml")


@router.post("/status", summary="Callback de estado de entrega", responses=problem_responses(403))
async def status(request: Request) -> Response:
    params = await _read_and_validate(request)
    # Registra la entrega; NO re-ejecuta agentes.
    await channels_service.handle_status_callback(
        params.get("MessageSid", ""), params.get("MessageStatus", "")
    )
    return Response(status_code=204)
