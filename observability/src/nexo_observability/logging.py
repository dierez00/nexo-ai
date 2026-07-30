"""Logging estructurado JSONL con redacción de PII y secretos.

Uso:
    from nexo_observability.logging import get_logger, configure_logging

    configure_logging(level="INFO")
    log = get_logger(__name__)
    log.info("run.started", run_id="run_01", trace_id="trace_01")
"""

from __future__ import annotations

import json
import logging
import re
import sys
from datetime import UTC, datetime
from typing import Any

# ---------------------------------------------------------------------------
# Patrones de redacción — se aplican a valores de string antes de emitir
# ---------------------------------------------------------------------------
_REDACT_KEYS: frozenset[str] = frozenset(
    {
        "password", "passwd", "secret", "token", "api_key", "apikey",
        "authorization", "jwt_secret", "twilio_auth_token", "private_key",
        "client_secret", "access_token", "refresh_token",
    }
)

_PII_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b\d{10}\b"), "[PHONE_REDACTED]"),           # teléfonos MX 10 dígitos
    (re.compile(r"whatsapp:\+\d+"), "whatsapp:[REDACTED]"),
    (re.compile(r"pii_ref:[^\s,\"']+"), "[PII_REF]"),           # referencias PII internas
]

_REDACTED = "[REDACTED]"


def _redact(data: Any, _depth: int = 0) -> Any:
    """Redacta recursivamente claves sensibles y patrones PII en dicts/strings."""
    if _depth > 10:
        return data
    if isinstance(data, dict):
        return {
            k: _REDACTED if k.lower() in _REDACT_KEYS else _redact(v, _depth + 1)
            for k, v in data.items()
        }
    if isinstance(data, list):
        return [_redact(item, _depth + 1) for item in data]
    if isinstance(data, str):
        for pattern, replacement in _PII_PATTERNS:
            data = pattern.sub(replacement, data)
        return data
    return data


# ---------------------------------------------------------------------------
# Formatter JSONL
# ---------------------------------------------------------------------------
class _JsonlFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        # Campos extra añadidos via log.info("msg", run_id=..., trace_id=...)
        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "message",
                "taskName",
            }:
                payload[key] = value

        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)

        return json.dumps(_redact(payload), ensure_ascii=False, default=str)


# ---------------------------------------------------------------------------
# Logger con soporte de kwargs como campos estructurados
# ---------------------------------------------------------------------------
class _StructuredLogger(logging.LoggerAdapter[logging.Logger]):
    def process(
        self, msg: str, kwargs: Any
    ) -> tuple[str, dict[str, Any]]:
        extra = kwargs.pop("extra", {})
        # Campos pasados directamente como kwargs se mueven a extra
        for key in list(kwargs):
            if key not in {"exc_info", "stack_info", "stacklevel"}:
                extra[key] = kwargs.pop(key)
        kwargs["extra"] = extra
        return msg, kwargs


def get_logger(name: str) -> _StructuredLogger:
    return _StructuredLogger(logging.getLogger(name), extra={})


def configure_logging(level: str = "INFO") -> None:
    """Configura el handler raíz con formato JSONL. Llamar una sola vez al iniciar."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonlFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
