"""Pol\u00edtica com\u00fan de replay para escrituras HTTP."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy import RowMapping

from nexo_api.core.errors import ProblemException
from nexo_api.repositories import idempotency as repo


def request_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


async def claim(
    tenant_id: int, operation: str, key: str, payload: dict[str, Any]
) -> tuple[RowMapping, bool]:
    record, owned = await repo.claim(tenant_id, operation, key, request_hash(payload))
    if owned:
        return record, True

    if record["request_hash"] != request_hash(payload):
        raise ProblemException(
            status=409,
            code="VERSION_CONFLICT",
            title="Idempotency-Key reutilizada con otro request",
            detail="Usa una nueva clave para un payload diferente.",
        )
    status = str(record["status"])
    if status == "processing":
        raise ProblemException(
            status=409,
            code="VERSION_CONFLICT",
            title="La operaci\u00f3n sigue en curso",
            detail="Reintenta con la misma Idempotency-Key cuando termine.",
            retryable=True,
        )
    if status == "unknown":
        body = repo.response_body(record)
        raise ProblemException(
            status=409,
            code="UNKNOWN_OUTCOME",
            title=str(body.get("title", "Resultado de escritura indeterminado")),
            detail=str(body.get("detail", "No se reintenta autom\u00e1ticamente.")),
        )
    return record, False
