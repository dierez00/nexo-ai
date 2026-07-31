"""Gate determinista para el alcance administrativo de salud (`DIE-F2-034`–`040`)."""

from __future__ import annotations

import re
from dataclasses import dataclass

HEALTH_SAFETY_WARNING = (
    "[salud-seguridad] No puedo diagnosticar, prescribir, interpretar síntomas ni "
    "clasificar urgencia clínica. Sí puedo orientar hacia una unidad y sus canales "
    "administrativos verificados."
)

_CLINICAL_REQUEST = re.compile(
    r"\b("
    r"diagn[oó]stic|qu[eé]\s+tengo|rec[eé]t|prescrib|medicament|pastilla|antibi[oó]tic|"
    r"dosis|cu[aá]nt[oa]\s+(?:debo|puedo)\s+tomar|interpreta(?:r)?\s+(?:mis\s+)?"
    r"(?:s[ií]ntomas|estudios|an[aá]lisis)|es\s+una\s+urgencia|triage"
    r")",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class HealthSafetyDecision:
    blocked_clinical_request: bool
    warning: str | None = None


def assess_health_message(message: str) -> HealthSafetyDecision:
    """Bloquea consejo clínico sin intentar inferir gravedad o enfermedad."""
    if _CLINICAL_REQUEST.search(message):
        return HealthSafetyDecision(True, HEALTH_SAFETY_WARNING)
    return HealthSafetyDecision(False)


__all__ = [
    "HEALTH_SAFETY_WARNING",
    "HealthSafetyDecision",
    "assess_health_message",
]
