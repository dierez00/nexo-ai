"""Qué hacer cuando no hay evidencia suficiente (`DIE-F1-027`).

Una búsqueda vacía no es un error del sistema ni una invitación a improvisar:
es información. El navegador de dominio necesita distinguir tres situaciones que
piden respuestas distintas, y ninguna de ellas es «responder igual».

| Veredicto | Qué ocurrió | Qué debe hacer el agente |
|---|---|---|
| `sufficient` | Evidencia activa y relevante | Responder con citaciones |
| `partial` | Algo hay, bajo el umbral de confianza | Responder lo sostenido y advertir del resto |
| `insufficient` | Nada entregable | No afirmar nada; preguntar o derivar |

El veredicto se calcula con código, no lo decide un modelo. Un modelo que juzga
si su propia evidencia le alcanza tiende a decir que sí.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from nexo_contracts import RetrievalResponse

# Puntaje por debajo del cual el mejor resultado no basta para sostener un claim
# crítico por sí solo. Es bastante más alto que el suelo del retriever a
# propósito: **entregar un fragmento y confiar en él son decisiones distintas**,
# y es aquí donde se toma la segunda.
#
# Se barrió entre 0.30 y 0.45 sobre `retrieval_mvp.v1.json` y el resultado no
# cambia en todo el rango. Eso importa más que el valor: significa que la
# separación entre dentro y fuera de alcance la hace el diseño, no un número
# ajustado a este dataset.
CONFIDENT_SCORE = 0.35


class RetrievalVerdict(StrEnum):
    SUFFICIENT = "sufficient"
    PARTIAL = "partial"
    INSUFFICIENT = "insufficient"


@dataclass(frozen=True)
class SufficiencyAssessment:
    """Veredicto más el motivo estable y el warning que debe ver la persona."""

    verdict: RetrievalVerdict
    reason: str
    warning: str | None = None

    @property
    def supports_critical_claims(self) -> bool:
        """Solo evidencia suficiente sostiene requisitos, costos o vigencias."""
        return self.verdict is RetrievalVerdict.SUFFICIENT


def assess(
    response: RetrievalResponse, *, confident_score: float = CONFIDENT_SCORE
) -> SufficiencyAssessment:
    """Clasifica una respuesta de retrieval según lo que permite afirmar."""
    if not response.results:
        return SufficiencyAssessment(
            verdict=RetrievalVerdict.INSUFFICIENT,
            reason="no_active_evidence",
            warning=(
                "No encontré documentación vigente que respalde esta consulta, así que "
                "no puedo confirmar requisitos ni costos."
            ),
        )

    best = response.results[0]
    if best.fused_score < confident_score:
        return SufficiencyAssessment(
            verdict=RetrievalVerdict.PARTIAL,
            reason="low_confidence_evidence",
            warning=(
                "La documentación que encontré solo cubre parcialmente tu consulta; "
                "confirma los datos en la dependencia antes de actuar."
            ),
        )

    # Una evidencia con señales de injection sigue siendo evidencia, pero no se
    # trata como concluyente: alguien alteró el documento en origen.
    if best.injection_signals:
        return SufficiencyAssessment(
            verdict=RetrievalVerdict.PARTIAL,
            reason="evidence_flagged_for_injection",
            warning=(
                "Una de las fuentes recuperadas contiene contenido anómalo y se "
                "descartó como respaldo; la respuesta puede estar incompleta."
            ),
        )

    return SufficiencyAssessment(
        verdict=RetrievalVerdict.SUFFICIENT,
        reason="active_evidence_above_threshold",
    )
