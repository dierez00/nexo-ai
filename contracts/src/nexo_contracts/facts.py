"""Contratos de hechos y evidencia (§5.2).

Este módulo carga los invariantes que sostienen el gate de alucinación: un hecho
crítico sin citación activa no puede aceptarse, y un `VerifiedFacts` es un
snapshot inmutable (`DIE-F0-016`).
"""

from __future__ import annotations

from typing import Annotated, Any, Self

from pydantic import Field, model_validator

from .base import FrozenNexoModel, NexoModel
from .enums import (
    CRITICAL_FACT_CATEGORIES,
    ContradictionSeverity,
    ContradictionStatus,
    Domain,
    FactCategory,
    FactOrigin,
    VerificationStatus,
)
from .ids import (
    ContradictionId,
    FactId,
    FragmentId,
    SourceId,
    ToolCallId,
)
from .primitives import CalendarDate, Confidence, Money, UtcDatetime


class SourceCitation(FrozenNexoModel):
    """Referencia puntual a un fragmento de una fuente (§5.2).

    Es inmutable a propósito: una citación es evidencia, y la evidencia no se
    edita después de recogerse.
    """

    source_id: SourceId
    fragment_id: FragmentId
    corpus_version: str = Field(
        max_length=120,
        description="Versión de corpus vigente cuando se recuperó el fragmento.",
    )
    source_version: str = Field(max_length=40)
    valid_from: CalendarDate
    valid_to: CalendarDate | None = None
    is_active: bool = Field(
        default=True,
        description="Falso si la fuente fue sustituida o venció; bloquea claims críticos.",
    )
    char_start: int | None = Field(
        default=None, ge=0, description="Inicio del tramo relevante dentro del fragmento."
    )
    char_end: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _check_span(self) -> Self:
        has_span = self.char_start is not None and self.char_end is not None
        if has_span and self.char_end <= self.char_start:  # type: ignore[operator]
            raise ValueError(
                f"tramo de citación inválido: char_end ({self.char_end}) debe ser mayor "
                f"que char_start ({self.char_start})"
            )
        return self


class FactValue(NexoModel):
    """Valor tipado de un hecho.

    Se modela como una unión explícita en lugar de `Any` para que el estimador
    nunca tenga que adivinar el tipo antes de sumar o comparar.
    """

    text: str | None = Field(default=None, max_length=2000)
    money: Money | None = None
    number: float | None = None
    boolean: bool | None = None
    date: CalendarDate | None = None
    items: Annotated[list[str], Field(max_length=100)] | None = None

    @model_validator(mode="after")
    def _exactly_one_value(self) -> Self:
        provided = [
            name
            for name in ("text", "money", "number", "boolean", "date", "items")
            if getattr(self, name) is not None
        ]
        if len(provided) != 1:
            raise ValueError(
                f"un FactValue debe declarar exactamente un tipo de valor; se recibieron "
                f"{len(provided)}: {sorted(provided)}"
            )
        return self


class Deduction(NexoModel):
    """Dato inferido, no afirmado por el usuario ni leído de una fuente (§5.2).

    Una deducción no confirmada nunca alimenta una escritura (`DIE-F2-053`);
    `write_eligible` es la puerta que lo impide.
    """

    value: FactValue
    source: FactOrigin
    confidence: Confidence
    confirmed_by_user: bool = False
    write_eligible: bool = False
    rationale: str = Field(max_length=500)

    @model_validator(mode="after")
    def _write_eligibility_requires_confirmation(self) -> Self:
        if self.write_eligible and not self.confirmed_by_user:
            raise ValueError(
                "una deducción no confirmada por la persona usuaria no puede marcarse "
                "write_eligible: habilitaría una escritura sobre un dato inferido"
            )
        return self


class CandidateFact(NexoModel):
    """Hecho propuesto por un agente, todavía sin verificar (§5.2)."""

    fact_id: FactId
    claim: str = Field(max_length=1000, description="Afirmación en lenguaje natural.")
    value: FactValue
    category: FactCategory
    domain: Domain
    origin: FactOrigin
    confidence: Confidence
    citations: Annotated[list[SourceCitation], Field(max_length=20)] = Field(default_factory=list)
    tool_call_id: ToolCallId | None = Field(
        default=None, description="Presente cuando el hecho proviene de una tool."
    )
    deduction: Deduction | None = None
    depends_on: Annotated[list[FactId], Field(max_length=50)] = Field(
        default_factory=list,
        description="Hechos de los que depende; si uno se rechaza, este se invalida.",
    )

    @property
    def is_critical(self) -> bool:
        return self.category in CRITICAL_FACT_CATEGORIES

    @model_validator(mode="after")
    def _origin_matches_evidence(self) -> Self:
        if self.origin is FactOrigin.TOOL and self.tool_call_id is None:
            raise ValueError(
                "un hecho de origen 'tool' debe referenciar el tool_call_id que lo produjo"
            )
        if self.origin is FactOrigin.DEDUCTION and self.deduction is None:
            raise ValueError("un hecho de origen 'deduction' debe incluir su bloque Deduction")
        if self.origin is FactOrigin.RAG and not self.citations:
            raise ValueError("un hecho de origen 'rag' debe incluir al menos una citación")
        return self


class VerifiedFact(FrozenNexoModel):
    """Hecho tras pasar por el verificador (§5.2).

    Invariante central: si es crítico y fue aceptado, tiene al menos una
    citación activa y es apto para escritura solo si además está aceptado.
    """

    fact_id: FactId
    claim: str = Field(max_length=1000)
    value: FactValue
    category: FactCategory
    domain: Domain
    verification: VerificationStatus
    reason: str = Field(
        max_length=300,
        description="Motivo estable de la decisión. Ejemplo: 'source_expired'.",
    )
    confidence: Confidence
    citations: Annotated[list[SourceCitation], Field(max_length=20)] = Field(default_factory=list)
    supporting_tool_call_id: ToolCallId | None = Field(
        default=None,
        description=(
            "Invocación de tool que respalda el hecho cuando su evidencia no es "
            "documental. Es la otra forma admisible de fundamentar un claim crítico."
        ),
    )
    depends_on: Annotated[list[FactId], Field(max_length=50)] = Field(default_factory=list)
    write_eligible: bool = False

    @property
    def is_critical(self) -> bool:
        return self.category in CRITICAL_FACT_CATEGORIES

    @property
    def has_active_evidence(self) -> bool:
        """Si el hecho está fundamentado, por documento o por tool."""
        return any(c.is_active for c in self.citations) or self.supporting_tool_call_id is not None

    @model_validator(mode="after")
    def _critical_accepted_facts_need_evidence(self) -> Self:
        """Un hecho crítico aceptado debe estar fundamentado.

        La evidencia admisible es de **dos** clases, no una: una citación activa
        o una invocación de tool verificable. Exigir siempre citación documental
        hacía inexpresable el caso más importante del sistema —«la cita quedó
        reservada, folio NEXO-MOCK-01»—, porque `ACTION_RESULT` es crítico por
        definición y jamás procede de un documento. Un adeudo consultado por
        tool tiene el mismo problema.

        Lo que no cambia: sin ninguna de las dos, no hay aceptación.
        """
        if self.verification is VerificationStatus.ACCEPTED and self.is_critical:
            if not self.has_active_evidence:
                raise ValueError(
                    f"el hecho crítico {self.fact_id!r} ({self.category.value}) fue aceptado "
                    f"sin evidencia activa; el gate de grounding exige una citación vigente "
                    f"o el tool_call_id que lo produjo"
                )
        return self

    @model_validator(mode="after")
    def _write_eligibility_requires_acceptance(self) -> Self:
        if self.write_eligible and self.verification is not VerificationStatus.ACCEPTED:
            raise ValueError(
                f"el hecho {self.fact_id!r} está marcado write_eligible con verificación "
                f"'{self.verification.value}'; solo un hecho aceptado puede sustentar una escritura"
            )
        return self


class Contradiction(FrozenNexoModel):
    """Conflicto detectado entre hechos, fuentes o resultados de tools (§5.2)."""

    contradiction_id: ContradictionId
    fact_ids: Annotated[list[FactId], Field(min_length=2, max_length=10)]
    severity: ContradictionSeverity
    status: ContradictionStatus = ContradictionStatus.DETECTED
    rule: str = Field(
        max_length=200,
        description="Regla de precedencia aplicada. Ejemplo: 'newer_source_wins'.",
    )
    explanation: str = Field(max_length=1000)
    conflicting_sources: Annotated[list[SourceId], Field(max_length=20)] = Field(
        default_factory=list
    )
    conflicting_tool_calls: Annotated[list[ToolCallId], Field(max_length=20)] = Field(
        default_factory=list
    )
    resolved_fact_id: FactId | None = None

    @model_validator(mode="after")
    def _resolution_requires_winner(self) -> Self:
        if self.status is ContradictionStatus.RESOLVED and self.resolved_fact_id is None:
            raise ValueError(
                "una contradicción resuelta debe indicar qué hecho prevaleció (resolved_fact_id)"
            )
        if self.resolved_fact_id is not None and self.resolved_fact_id not in self.fact_ids:
            raise ValueError(
                f"el hecho ganador {self.resolved_fact_id!r} no aparece entre los hechos "
                f"implicados en la contradicción"
            )
        return self

    @property
    def blocks_writes(self) -> bool:
        """Una contradicción crítica sin resolver bloquea toda escritura dependiente."""
        return (
            self.severity is ContradictionSeverity.CRITICAL
            and self.status is not ContradictionStatus.RESOLVED
        )


class VerifiedFacts(FrozenNexoModel):
    """Snapshot inmutable que reciben estimación final, A2UI y redactor (§5.2).

    El redactor solo ve esto: no tiene puertos de RAG ni de MCP, así que este
    snapshot es literalmente el universo de hechos del que puede hablar
    (`DIE-F1-094`).
    """

    snapshot_id: str = Field(max_length=120)
    created_at: UtcDatetime
    facts: Annotated[tuple[VerifiedFact, ...], Field(max_length=500)]
    contradictions: Annotated[tuple[Contradiction, ...], Field(max_length=100)] = ()

    @model_validator(mode="after")
    def _unique_fact_ids(self) -> Self:
        seen: set[str] = set()
        for fact in self.facts:
            if fact.fact_id in seen:
                raise ValueError(f"fact_id duplicado en el snapshot: {fact.fact_id!r}")
            seen.add(fact.fact_id)
        return self

    @model_validator(mode="after")
    def _dependencies_are_resolvable(self) -> Self:
        known = {fact.fact_id for fact in self.facts}
        for fact in self.facts:
            missing = [dep for dep in fact.depends_on if dep not in known]
            if missing:
                raise ValueError(
                    f"el hecho {fact.fact_id!r} declara dependencias ausentes del snapshot: "
                    f"{missing}; las dependencias deben ser explícitas y resolubles"
                )
        return self

    @model_validator(mode="after")
    def _rejected_dependencies_invalidate_dependents(self) -> Self:
        """Un hecho aceptado no puede apoyarse en uno rechazado.

        Es el invariante que el merge de Fase 4 debe preservar al consolidar
        ramas paralelas (`DIE-F4-008`).
        """
        status_by_id = {fact.fact_id: fact.verification for fact in self.facts}
        for fact in self.facts:
            if fact.verification is not VerificationStatus.ACCEPTED:
                continue
            broken = [
                dep for dep in fact.depends_on if status_by_id[dep] is VerificationStatus.REJECTED
            ]
            if broken:
                raise ValueError(
                    f"el hecho aceptado {fact.fact_id!r} depende de hechos rechazados {broken}; "
                    f"debe invalidarse en el merge antes de cerrar el snapshot"
                )
        return self

    def accepted(self) -> tuple[VerifiedFact, ...]:
        return tuple(f for f in self.facts if f.verification is VerificationStatus.ACCEPTED)

    def by_id(self, fact_id: str) -> VerifiedFact | None:
        return next((f for f in self.facts if f.fact_id == fact_id), None)

    def has_blocking_contradiction(self) -> bool:
        return any(c.blocks_writes for c in self.contradictions)

    def citation_index(self) -> dict[str, tuple[SourceCitation, ...]]:
        """Citaciones por `fact_id`, para que A2UI y el redactor no las recalculen."""
        return {fact.fact_id: tuple(fact.citations) for fact in self.facts}

    @classmethod
    def empty(cls, *, snapshot_id: str, created_at: Any) -> VerifiedFacts:
        return cls(snapshot_id=snapshot_id, created_at=created_at, facts=(), contradictions=())
