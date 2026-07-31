"""IDs opacos con prefijo (§9.1) sobre los `bigint` de la base.

Wire expone `conv_123`, `run_45`, etc.; internamente son claves `bigint`.
`decode` lanza `ValueError` si el formato no corresponde (el caller lo mapea a 404/400).
"""

from __future__ import annotations

from typing import Final

CONVERSATION: Final = "conv"
MESSAGE: Final = "msg"
RUN: Final = "run"
ACTION: Final = "act"
APPOINTMENT: Final = "apt"
USER: Final = "usr"


def encode(prefix: str, raw: int) -> str:
    return f"{prefix}_{raw}"


def decode(prefix: str, value: str) -> int:
    head = f"{prefix}_"
    if not value.startswith(head):
        raise ValueError(f"id inválido: se esperaba prefijo '{prefix}_'")
    try:
        return int(value[len(head) :])
    except ValueError as exc:
        raise ValueError(f"id inválido: '{value}'") from exc
