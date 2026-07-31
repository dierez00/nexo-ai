"""Primitivas tipadas compartidas: tiempo, dinero y puntajes (`DIE-F0-014`).

Las tres existen para eliminar clases enteras de error antes de que lleguen a un
agente: fechas sin zona horaria, montos en flotante y puntajes fuera de rango.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Annotated

from pydantic import AfterValidator, Field

from .base import NexoModel


def _to_utc(value: datetime) -> datetime:
    """Exige zona horaria y normaliza a UTC.

    Un `datetime` ingenuo es ambiguo y no se acepta en ninguna frontera: el
    plan fija UTC como representación única (§2.3).
    """
    if value.tzinfo is None:
        raise ValueError(
            "timestamp sin zona horaria: los contratos exigen fechas conscientes de "
            "zona horaria, normalizadas a UTC"
        )
    return value.astimezone(UTC)


UtcDatetime = Annotated[datetime, AfterValidator(_to_utc)]
"""Instante con zona horaria, siempre normalizado a UTC."""

CalendarDate = date
"""Fecha civil sin hora, para vigencias documentales (`valid_from`, `valid_to`)."""

Score = Annotated[float, Field(ge=0.0, le=1.0)]
"""Puntaje acotado a [0, 1]: relevancia, cobertura y métricas de evaluación."""

Confidence = Annotated[float, Field(ge=0.0, le=1.0)]
"""Confianza acotada a [0, 1] declarada por un agente o un retriever."""

PositiveMillis = Annotated[int, Field(ge=0, le=3_600_000)]
"""Duración en milisegundos, tope de una hora para detectar unidades erróneas."""

CurrencyCode = Annotated[str, Field(pattern=r"^[A-Z]{3}$")]
"""Código ISO 4217 en mayúsculas."""

SemanticVersion = Annotated[str, Field(pattern=r"^\d+\.\d+\.\d+$")]
"""Versión semántica de tools, catálogos, prompts y skills."""

Slug = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]{1,62}$")]
"""Identificador legible y estable en `snake_case` para dominios y trámites."""


class Money(NexoModel):
    """Monto en unidades menores más moneda (§2.3).

    Nunca se representa un monto en flotante ni se suma en un prompt: el
    estimador opera sobre `amount_minor` con código determinista.
    """

    amount_minor: int = Field(
        description="Monto en la unidad menor de la moneda; 125000 son 1,250.00 MXN.",
    )
    currency: CurrencyCode = Field(description="Código ISO 4217, por ejemplo 'MXN'.")

    def __add__(self, other: Money) -> Money:
        if other.currency != self.currency:
            raise ValueError(
                f"no se pueden sumar montos de monedas distintas: "
                f"{self.currency} y {other.currency}"
            )
        return Money(amount_minor=self.amount_minor + other.amount_minor, currency=self.currency)


class ValidityWindow(NexoModel):
    """Ventana de vigencia de una fuente o una regla.

    `valid_to` nulo significa vigencia abierta. El retriever filtra por esta
    ventana antes de entregar texto a un agente (`DIE-F1-022`).
    """

    valid_from: CalendarDate
    valid_to: CalendarDate | None = None

    def covers(self, moment: date) -> bool:
        if moment < self.valid_from:
            return False
        return self.valid_to is None or moment <= self.valid_to


def _validate_window(window: ValidityWindow) -> ValidityWindow:
    if window.valid_to is not None and window.valid_to < window.valid_from:
        raise ValueError(
            f"ventana de vigencia inválida: valid_to ({window.valid_to}) es anterior a "
            f"valid_from ({window.valid_from})"
        )
    return window


CheckedValidityWindow = Annotated[ValidityWindow, AfterValidator(_validate_window)]
