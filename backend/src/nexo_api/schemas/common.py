"""Tipos de wire compartidos (§9.1)."""

from __future__ import annotations

from pydantic import BaseModel


class Money(BaseModel):
    """Monto en unidades menores (centavos). Ej.: 125000 = $1,250.00 MXN."""

    amount_minor: int
    currency: str = "MXN"
