"""Contrato de clasificación de solicitudes (F1.4).

Fase 0 dejó este hueco anotado: el grafo mínimo validaba contra un
`FakeClassification` local, marcado como andamiaje, porque §5 no define un
contrato de clasificación y el clasificador real es trabajo de F1.4. Este módulo
lo cierra y `FakeClassification` desaparece.

Dos invariantes hacen el trabajo:

1. **Las intenciones no se colapsan.** «Quiero renovar mi licencia y saber si
   debo algo» son *dos* intenciones —`renovar_licencia` y `consultar_adeudo`—
   con rutas, tools y respuestas distintas (`DIE-F1-032`). Fundirlas en una
   pierde la mitad de la solicitud, y es el error que el caso oficial
   `CAP-VEH-01` existe para detectar.
2. **La ambigüedad se declara, no se resuelve inventando.** Un clasificador que
   nunca duda es un clasificador que adivina (`DIE-F1-035`).

El clasificador no consulta RAG, no invoca tools y no redacta la respuesta final
(`DIE-F1-033`). Nada en este contrato le da forma de hacerlo: no transporta
citaciones, ni tools propuestas, ni texto de respuesta.
"""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from .base import NexoModel
from .enums import Audience, Domain, OperationalUrgency
from .primitives import Confidence, Slug
from .safety import SafePayload


class DetectedIntent(NexoModel):
    """Una intención concreta dentro de la solicitud.

    `intent` es un slug estable (`renovar_licencia`, `consultar_adeudo`,
    `abrir_negocio`) y no texto libre: el catálogo, las skills y las
    evaluaciones lo usan como clave.
    """

    intent: Slug
    domain: Domain
    confidence: Confidence
    rationale: str = Field(
        default="",
        max_length=300,
        description="Por qué se detectó, en términos de lo que dijo la persona.",
    )


class Classification(NexoModel):
    """Salida del clasificador (F1.4).

    Es lo único que el supervisor necesita para planificar: qué dominios toca la
    solicitud, qué quiere hacer la persona, qué contexto se pudo extraer y qué
    falta por saber.
    """

    intents: Annotated[list[DetectedIntent], Field(max_length=10)] = Field(
        default_factory=list,
        description="Intenciones detectadas, en orden de relevancia. Nunca se fusionan.",
    )
    location: str | None = Field(
        default=None,
        max_length=200,
        description="Ubicación mencionada, tal cual la dijo la persona.",
    )
    audience: Audience | None = Field(
        default=None, description="Perfil deducido; nulo si el mensaje no lo sugiere."
    )
    urgency: OperationalUrgency = OperationalUrgency.ROUTINE
    entities: SafePayload = Field(
        description="Datos sueltos extraídos del mensaje, sin PII directa.",
    )
    missing_information: Annotated[list[str], Field(max_length=20)] = Field(
        default_factory=list,
        description="Qué haría falta preguntar; el navegador decide si se pregunta.",
    )
    confidence: Confidence = 0.0
    request_kind: Literal["procedure", "capabilities"] = Field(
        default="procedure",
        description=(
            "Tipo de solicitud: un trámite de dominio o una consulta sobre las "
            "capacidades publicadas del asistente."
        ),
    )
    is_ambiguous: bool = Field(
        default=False,
        description="Hay dos lecturas materialmente distintas de la solicitud.",
    )
    ambiguity_reason: str | None = Field(default=None, max_length=300)
    is_out_of_scope: bool = Field(
        default=False,
        description="La solicitud no corresponde a ninguno de los dominios atendidos.",
    )

    @model_validator(mode="after")
    def _ambiguity_is_explained(self) -> Self:
        if self.is_ambiguous and not self.ambiguity_reason:
            raise ValueError(
                "una clasificación ambigua debe decir por qué lo es; sin motivo, "
                "el navegador no puede formular la pregunta mínima"
            )
        return self

    @model_validator(mode="after")
    def _a_classification_commits_to_something(self) -> Self:
        """O hay intenciones, o se declara fuera de alcance o ambigua.

        Devolver cero intenciones sin decir nada más es la forma silenciosa de
        no clasificar: el run continuaría sin dominio y sin explicación.
        """
        if not self.intents and not (
            self.is_out_of_scope or self.is_ambiguous or self.request_kind == "capabilities"
        ):
            raise ValueError(
                "la clasificación no detectó intenciones y tampoco se declara fuera de "
                "alcance ni ambigua; un run sin dominio necesita un motivo"
            )
        return self

    @model_validator(mode="after")
    def _capabilities_query_has_no_domain(self) -> Self:
        if self.request_kind == "capabilities" and (
            self.intents or self.is_out_of_scope or self.is_ambiguous
        ):
            raise ValueError(
                "una consulta de capacidades no puede declarar intenciones, ambigüedad "
                "ni estar fuera de alcance"
            )
        return self

    @model_validator(mode="after")
    def _out_of_scope_claims_no_domain(self) -> Self:
        if self.is_out_of_scope and self.intents:
            raise ValueError(
                "la clasificación se declara fuera de alcance pero propone intenciones "
                "de dominio; las dos cosas no pueden ser ciertas a la vez"
            )
        return self

    @property
    def domains(self) -> tuple[Domain, ...]:
        """Dominios implicados, sin repetir y en orden de aparición."""
        seen: dict[Domain, None] = {}
        for intent in self.intents:
            seen.setdefault(intent.domain, None)
        return tuple(seen)

    @property
    def primary_domain(self) -> Domain | None:
        return self.intents[0].domain if self.intents else None

    def intent_slugs(self) -> tuple[str, ...]:
        return tuple(intent.intent for intent in self.intents)
