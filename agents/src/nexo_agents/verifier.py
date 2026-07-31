"""Verificador secuencial (F1.6).

Recibe un snapshot cerrado —hechos candidatos, citaciones y resultados de
tools— y decide, hecho por hecho, si se acepta, se rechaza o queda incierto,
con un motivo estable. No redacta nada (`DIE-F1-055`) y no ejecuta nada.

**Las comprobaciones son deterministas.** No es una preferencia estética: el
verificador es lo último que separa una respuesta fundamentada de una inventada,
y un gate que depende de que un modelo esté de buen humor no es un gate. El
modelo puede *afinar* el juicio de si una citación sostiene un claim concreto
—es lo único genuinamente semántico— pero nunca puede convertir un `rejected` en
un `accepted`: las reglas duras se aplican después de él, no antes.

Motivos de rechazo, todos estables y en `snake_case` para que una evaluación
pueda agruparlos:

| Motivo | Qué ocurrió |
|---|---|
| `source_expired` | La citación apunta a una fuente vencida o sustituida |
| `source_not_retrieved` | El fragmento citado no está en la evidencia recuperada |
| `wrong_institution` | La citación es de otra institución |
| `critical_claim_without_evidence` | Hecho crítico sin ninguna citación activa |
| `contradicted_by_tool` | El documento dice una cosa y la tool otra |
| `unverifiable_action_result` | Una escritura sin identificador verificable |
| `citation_does_not_support_claim` | La citación existe pero no habla del claim |
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date

from nexo_contracts import (
    CRITICAL_FACT_CATEGORIES,
    CandidateFact,
    Contradiction,
    ContradictionSeverity,
    ContradictionStatus,
    FactCategory,
    FactOrigin,
    RetrievalResult,
    SelfCheckResult,
    SourceCitation,
    ToolCallStatus,
    ToolResult,
    VerificationStatus,
    VerifiedFact,
    VerifiedFacts,
)
from nexo_contracts.primitives import UtcDatetime

# Solapamiento léxico mínimo entre el claim y el texto del fragmento para
# considerar que la citación habla de lo que el claim afirma.
#
# Es un proxy grosero de una comprobación semántica y está calibrado bajo a
# propósito: su función es atrapar la citación **descaradamente** ajena —el
# modelo cita el fragmento de horarios para sostener un costo—, no arbitrar
# matices. Rechazar de más aquí sería peor que dejar pasar: un hecho verdadero
# rechazado desaparece de la respuesta sin que nadie se entere.
MIN_CLAIM_SUPPORT = 0.18

# Dos hechos de la misma categoría no necesariamente hablan del mismo asunto:
# el costo de una licencia y un adeudo vehicular son ambos ``cost``. Antes de
# comparar valores exigimos un solapamiento suficiente entre ambos claims.
MIN_CONFLICT_SUBJECT_SUPPORT = 0.40


def _support(claim: str, evidence: str) -> float:
    """Fracción de los términos del claim presentes en el fragmento citado."""
    from nexo_rag.retrieval.lexical import tokenize

    claim_terms = set(tokenize(claim))
    if not claim_terms:
        return 0.0
    return len(claim_terms & set(tokenize(evidence))) / len(claim_terms)


@dataclass(frozen=True)
class VerificationOutcome:
    """Resultado completo de la verificación de un run."""

    verified_facts: VerifiedFacts
    self_check: SelfCheckResult
    warnings: tuple[str, ...] = ()

    @property
    def blocks_writes(self) -> bool:
        """Si alguna contradicción crítica impide ejecutar una escritura."""
        return self.verified_facts.has_blocking_contradiction()


@dataclass
class Verifier:
    """Verificación determinista de hechos candidatos.

    No recibe puertos: opera sobre el snapshot que se le entrega. Si necesitara
    volver a consultar la evidencia, la evidencia no sería un snapshot y dos
    verificaciones del mismo run podrían discrepar.
    """

    institution_id: str
    now: UtcDatetime
    valid_at: date
    min_claim_support: float = MIN_CLAIM_SUPPORT
    _contradictions: list[Contradiction] = field(default_factory=list, init=False)

    def verify(
        self,
        candidates: Sequence[CandidateFact],
        *,
        evidence: Sequence[RetrievalResult] = (),
        tool_results: Sequence[ToolResult] = (),
        snapshot_id: str,
        contradiction_id: str | None = None,
    ) -> VerificationOutcome:
        """Verifica todos los hechos y cierra el snapshot inmutable."""
        self._contradictions = []
        by_fragment = {result.fragment_id: result for result in evidence}
        tools = {result.tool_call_id: result for result in tool_results}

        verified: list[VerifiedFact] = []
        warnings: list[str] = []
        for candidate in candidates:
            fact = self._verify_one(candidate, by_fragment, tools)
            verified.append(fact)

        verified = self._invalidate_dependents(verified)
        if contradiction_id is not None:
            self.detect_tool_document_conflicts(
                verified,
                contradiction_id=contradiction_id,
            )

        rejected = sum(fact.verification is VerificationStatus.REJECTED for fact in verified)
        if rejected:
            warnings.append(f"{rejected} afirmación(es) no superaron la verificación y no se usan")
        for contradiction in self._contradictions:
            warnings.append(f"Contradicción detectada: {contradiction.explanation}")

        snapshot = VerifiedFacts(
            snapshot_id=snapshot_id,
            created_at=self.now,
            facts=tuple(verified),
            contradictions=tuple(self._contradictions),
        )
        return VerificationOutcome(
            verified_facts=snapshot,
            self_check=SelfCheckResult(
                schema_valid=True,
                unsupported_claims=rejected,
                out_of_scope_sources=0,
                forbidden_tool_requests=0,
                notes=["verification_completed"],
            ),
            warnings=tuple(warnings),
        )

    # -- un hecho -----------------------------------------------------------

    def _verify_one(
        self,
        candidate: CandidateFact,
        by_fragment: dict[str, RetrievalResult],
        tools: dict[str, ToolResult],
    ) -> VerifiedFact:
        is_critical = candidate.category in CRITICAL_FACT_CATEGORIES

        if candidate.origin is FactOrigin.TOOL:
            return self._verify_tool_fact(candidate, tools, is_critical=is_critical)

        active = self._usable_citations(candidate, by_fragment)
        if active.rejection is not None:
            return self._reject(candidate, active.rejection)

        # `DIE-F1-053`: un hecho crítico sin evidencia se bloquea, y con él
        # cualquier escritura que dependiera de él.
        if is_critical and not active.citations:
            return self._reject(candidate, "critical_claim_without_evidence")

        if is_critical and not self._supports_claim(candidate, active.citations, by_fragment):
            return self._reject(candidate, "citation_does_not_support_claim")

        return VerifiedFact(
            fact_id=candidate.fact_id,
            claim=candidate.claim,
            value=candidate.value,
            category=candidate.category,
            domain=candidate.domain,
            verification=VerificationStatus.ACCEPTED,
            reason="citation_supports_claim" if active.citations else "no_evidence_required",
            confidence=candidate.confidence,
            citations=list(active.citations),
            depends_on=list(candidate.depends_on),
            # Solo un hecho crítico, aceptado y citado puede sustentar una
            # escritura. Los demás informan, no autorizan.
            write_eligible=is_critical and bool(active.citations),
        )

    def _verify_tool_fact(
        self, candidate: CandidateFact, tools: dict[str, ToolResult], *, is_critical: bool
    ) -> VerifiedFact:
        """Un hecho que viene de una tool se verifica contra su resultado."""
        result = tools.get(candidate.tool_call_id or "")
        if result is None:
            return self._reject(candidate, "tool_result_missing")
        if result.status is not ToolCallStatus.SUCCEEDED:
            return self._reject(candidate, "tool_call_failed")

        # `DIE-F1-054`: el resultado de una acción solo es un hecho si trae
        # identificador verificable. Un mock explícito cuenta; una respuesta sin
        # folio, no.
        if candidate.category is FactCategory.ACTION_RESULT and result.confirmation is None:
            return self._reject(candidate, "unverifiable_action_result")

        return VerifiedFact(
            fact_id=candidate.fact_id,
            claim=candidate.claim,
            value=candidate.value,
            category=candidate.category,
            domain=candidate.domain,
            verification=VerificationStatus.ACCEPTED,
            reason="tool_result_confirms_claim",
            confidence=candidate.confidence,
            citations=list(candidate.citations),
            # La evidencia de este hecho es la invocación, no un documento.
            supporting_tool_call_id=candidate.tool_call_id,
            depends_on=list(candidate.depends_on),
            write_eligible=is_critical,
        )

    # -- citaciones ---------------------------------------------------------

    @dataclass(frozen=True)
    class _Citations:
        citations: tuple[SourceCitation, ...] = ()
        rejection: str | None = None

    def _usable_citations(
        self, candidate: CandidateFact, by_fragment: dict[str, RetrievalResult]
    ) -> Verifier._Citations:
        """Filtra las citaciones y devuelve el primer motivo de rechazo duro."""
        usable: list[SourceCitation] = []
        for citation in candidate.citations:
            if not citation.is_active:
                return Verifier._Citations(rejection="source_expired")
            if citation.valid_to is not None and citation.valid_to < self.valid_at:
                return Verifier._Citations(rejection="source_expired")
            retrieved = by_fragment.get(citation.fragment_id)
            if retrieved is None:
                # La citación apunta a algo que no está en la evidencia de este
                # run. O el modelo la inventó, o la evidencia cambió a mitad.
                return Verifier._Citations(rejection="source_not_retrieved")
            if retrieved.source_id != citation.source_id:
                return Verifier._Citations(rejection="wrong_institution")
            usable.append(citation)
        return Verifier._Citations(citations=tuple(usable))

    def _supports_claim(
        self,
        candidate: CandidateFact,
        citations: Sequence[SourceCitation],
        by_fragment: dict[str, RetrievalResult],
    ) -> bool:
        """`DIE-F1-049`: la citación debe hablar del claim, no solo existir."""
        for citation in citations:
            retrieved = by_fragment.get(citation.fragment_id)
            if retrieved is None:
                continue
            if _support(candidate.claim, retrieved.text) >= self.min_claim_support:
                return True
        return False

    # -- contradicciones ----------------------------------------------------

    def detect_tool_document_conflicts(
        self, facts: Sequence[VerifiedFact], *, contradiction_id: str
    ) -> list[Contradiction]:
        """`DIE-F1-051`: compara documento y tool cuando ambos hablan de lo mismo.

        Solo se compara lo comparable: dos hechos de la misma categoría y el
        mismo dominio, uno con citación documental y otro con resultado de tool.
        Si sus valores discrepan, se registra la contradicción **sin resolverla**:
        elegir un ganador es de las reglas de precedencia de Fase 4.
        """
        conflicts: list[Contradiction] = []
        for index, left in enumerate(facts):
            for right in facts[index + 1 :]:
                if left.category is not right.category or left.domain is not right.domain:
                    continue
                if left.value == right.value:
                    continue
                if bool(left.citations) == bool(right.citations):
                    continue
                if (
                    max(_support(left.claim, right.claim), _support(right.claim, left.claim))
                    < MIN_CONFLICT_SUBJECT_SUPPORT
                ):
                    continue
                conflict_id = (
                    contradiction_id
                    if not conflicts
                    else f"{contradiction_id}_{len(conflicts) + 1}"
                )
                conflicts.append(
                    Contradiction(
                        contradiction_id=conflict_id,
                        fact_ids=[left.fact_id, right.fact_id],
                        severity=(
                            ContradictionSeverity.CRITICAL
                            if left.category in CRITICAL_FACT_CATEGORIES
                            else ContradictionSeverity.MATERIAL
                        ),
                        status=ContradictionStatus.DETECTED,
                        rule="document_and_tool_disagree",
                        explanation=(
                            f"la evidencia documental y el resultado de la tool difieren "
                            f"sobre {left.category.value}"
                        ),
                    )
                )
        self._contradictions.extend(conflicts)
        return conflicts

    # -- dependencias -------------------------------------------------------

    def _invalidate_dependents(self, facts: list[VerifiedFact]) -> list[VerifiedFact]:
        """Un hecho aceptado no puede apoyarse en uno rechazado.

        Se propaga hasta punto fijo: si A depende de B y B de C, rechazar C
        invalida los tres. Sin la propagación, el contrato de `VerifiedFacts`
        rechazaría el snapshot entero al cerrarlo, y con razón.
        """
        by_id = {fact.fact_id: fact for fact in facts}
        changed = True
        while changed:
            changed = False
            for fact_id, fact in list(by_id.items()):
                if fact.verification is not VerificationStatus.ACCEPTED:
                    continue
                broken = [
                    dependency
                    for dependency in fact.depends_on
                    if dependency in by_id
                    and by_id[dependency].verification is VerificationStatus.REJECTED
                ]
                if broken:
                    by_id[fact_id] = fact.model_copy(
                        update={
                            "verification": VerificationStatus.REJECTED,
                            "reason": "depends_on_rejected_fact",
                            "write_eligible": False,
                        }
                    )
                    changed = True
        return [by_id[fact.fact_id] for fact in facts]

    # -- utilidades ---------------------------------------------------------

    def _reject(self, candidate: CandidateFact, reason: str) -> VerifiedFact:
        return VerifiedFact(
            fact_id=candidate.fact_id,
            claim=candidate.claim,
            value=candidate.value,
            category=candidate.category,
            domain=candidate.domain,
            verification=VerificationStatus.REJECTED,
            reason=reason,
            confidence=candidate.confidence,
            # Un hecho rechazado conserva sus citaciones: son la evidencia de
            # *por qué* se rechazó, y una auditoría las necesita.
            citations=list(candidate.citations),
            depends_on=list(candidate.depends_on),
            write_eligible=False,
        )
