"""Métricas de calidad del retrieval: recall@k y citation precision (`DIE-F1-029`).

Las dos métricas del gate de §3 miden cosas distintas y ambas hacen falta:

- **recall@k** — de los fragmentos que *deberían* aparecer, ¿cuántos aparecen
  entre los `k` primeros? Responde «¿encontramos la evidencia?».
- **citation precision** — de los fragmentos que devolvimos, ¿cuántos son
  evidencia legítima para la consulta? Responde «¿lo que devolvimos sostiene
  algo?». Un fragmento vencido, de otro dominio o marcado como negativo cuenta
  como fallo aunque el recall sea perfecto.

Los umbrales del gate son recall@5 ≥ 0.80 y citation precision ≥ 0.90.

Todo se calcula con código. Una métrica de calidad evaluada por un modelo es
una opinión, y un gate no puede apoyarse en una opinión (`DIE-F4-054`).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Self

from pydantic import Field, model_validator

from nexo_contracts import (
    Domain,
    NexoModel,
    RetrievalFilters,
    RetrievalMode,
    RetrievalQuery,
    RetrievalResponse,
    SourceStatus,
)
from nexo_contracts.ids import FragmentId, InstitutionId, SourceId
from nexo_contracts.primitives import CalendarDate, Score

from .ports import RetrieverPort
from .retrieval.sufficiency import assess

RECALL_AT_5_TARGET = 0.80
CITATION_PRECISION_TARGET = 0.90


class RetrievalCase(NexoModel):
    """Un caso del dataset de retrieval (`DIE-F1-028`).

    Un caso declara qué debe encontrarse y qué **no** debe encontrarse. Los
    negativos son la mitad importante: un retriever que devuelve todo tiene
    recall perfecto y es inútil.
    """

    case_id: str = Field(max_length=120)
    query: str = Field(min_length=1, max_length=2000)
    domain: Domain
    institution_id: InstitutionId = "inst_demo"
    valid_at: CalendarDate
    top_k: int = Field(default=5, ge=1, le=50)
    retrieval_mode: RetrievalMode = RetrievalMode.HYBRID
    expected_fragments: Annotated[list[FragmentId], Field(max_length=50)] = Field(
        default_factory=list,
        description="Fragmentos que deben aparecer entre los top_k.",
    )
    forbidden_sources: Annotated[list[SourceId], Field(max_length=50)] = Field(
        default_factory=list,
        description="Fuentes que no deben aparecer: vencidas, de otro dominio o negativas.",
    )
    expect_insufficient: bool = Field(
        default=False,
        description=(
            "El caso verifica que una consulta fuera de alcance **no sostenga** claims "
            "críticos. No exige que el retriever devuelva cero resultados: sobre este "
            "corpus las puntuaciones de dentro y fuera de alcance se solapan, así que "
            "quien decide es `assess`, no el umbral."
        ),
    )
    notes: str = Field(default="", max_length=500)

    @model_validator(mode="after")
    def _a_case_asserts_something(self) -> Self:
        if (
            not self.expected_fragments
            and not self.forbidden_sources
            and not self.expect_insufficient
        ):
            raise ValueError(
                f"el caso {self.case_id!r} no afirma nada: debe declarar fragmentos "
                f"esperados, fuentes prohibidas o expect_insufficient"
            )
        return self

    def to_query(self) -> RetrievalQuery:
        return RetrievalQuery(
            query=self.query,
            domain=self.domain,
            filters=RetrievalFilters(
                institution_id=self.institution_id,
                status=[SourceStatus.ACTIVE],
                valid_at=self.valid_at,
            ),
            top_k=self.top_k,
            retrieval_mode=self.retrieval_mode,
        )


class RetrievalDataset(NexoModel):
    """Dataset versionado de retrieval."""

    dataset_version: str = Field(max_length=60)
    cases: Annotated[list[RetrievalCase], Field(min_length=1, max_length=500)]

    @model_validator(mode="after")
    def _case_ids_are_unique(self) -> Self:
        ids = [case.case_id for case in self.cases]
        if len(ids) != len(set(ids)):
            raise ValueError("hay case_id duplicados en el dataset de retrieval")
        return self

    @classmethod
    def load(cls, path: Path) -> RetrievalDataset:
        return cls.model_validate_json(path.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class CaseScore:
    """Resultado de un caso, con lo suficiente para depurarlo sin reejecutarlo."""

    case_id: str
    recall: float
    citation_precision: float
    missing_fragments: tuple[str, ...]
    forbidden_hits: tuple[str, ...]
    returned: int
    unexpected_results: bool = False

    @property
    def passed(self) -> bool:
        """Un caso pasa si encontró lo que debía y **nada** de lo que no debía.

        `unexpected_results` es la tercera condición y se olvida con facilidad:
        un caso fuera de alcance que devuelve cinco fragmentos irrelevantes tiene
        cero fragmentos faltantes y cero fuentes prohibidas, así que sin esta
        comprobación se contaría como aprobado mientras hunde la precisión.
        """
        return (
            not self.missing_fragments and not self.forbidden_hits and not self.unexpected_results
        )


class RetrievalBaseline(NexoModel):
    """Baseline comparable entre commits (`DIE-F1-029`)."""

    dataset_version: str = Field(max_length=60)
    corpus_versions: dict[Domain, str] = Field(default_factory=dict)
    embeddings_model: str = Field(max_length=120)
    retrieval_mode: RetrievalMode = RetrievalMode.HYBRID
    case_count: int = Field(ge=0)
    recall_at_k: Score
    citation_precision: Score
    cases_passed: int = Field(ge=0)

    @property
    def meets_gate(self) -> bool:
        """El gate de §3: recall@5 ≥ 0.80 y citation precision ≥ 0.90."""
        return (
            self.recall_at_k >= RECALL_AT_5_TARGET
            and self.citation_precision >= CITATION_PRECISION_TARGET
        )


def score_case(case: RetrievalCase, response: RetrievalResponse) -> CaseScore:
    """Puntúa un caso contra la respuesta real del retriever."""
    returned_fragments = [result.fragment_id for result in response.results[: case.top_k]]
    returned_sources = [result.source_id for result in response.results[: case.top_k]]

    missing = tuple(
        fragment for fragment in case.expected_fragments if fragment not in returned_fragments
    )
    forbidden = tuple(source for source in case.forbidden_sources if source in returned_sources)

    if case.expected_fragments:
        found = len(case.expected_fragments) - len(missing)
        recall = found / len(case.expected_fragments)
    else:
        # Un caso sin fragmentos esperados solo comprueba exclusiones. Contarlo
        # como recall 0 hundiría la métrica sin que nada haya fallado.
        recall = 1.0

    if returned_fragments:
        legitimate = sum(1 for source in returned_sources if source not in case.forbidden_sources)
        precision = legitimate / len(returned_fragments)
    else:
        # Devolver nada es precisión perfecta cuando eso era lo correcto, y
        # precisión nula cuando había algo que encontrar.
        precision = 1.0 if case.expect_insufficient or not case.expected_fragments else 0.0

    # Fuera de alcance: lo que se comprueba es el veredicto de suficiencia, no
    # que la lista venga vacía.
    unexpected = bool(case.expect_insufficient and assess(response).supports_critical_claims)
    if unexpected:
        precision = 0.0

    return CaseScore(
        case_id=case.case_id,
        recall=recall,
        citation_precision=precision,
        missing_fragments=missing,
        forbidden_hits=forbidden,
        returned=len(response.results),
        unexpected_results=unexpected,
    )


async def measure(
    retriever: RetrieverPort,
    dataset: RetrievalDataset,
    *,
    embeddings_model: str,
    corpus_versions: dict[Domain, str] | None = None,
) -> tuple[RetrievalBaseline, list[CaseScore]]:
    """Ejecuta el dataset completo y devuelve el baseline más el detalle."""
    scores: list[CaseScore] = []
    for case in dataset.cases:
        response = await retriever.retrieve(case.to_query())
        scores.append(score_case(case, response))

    count = len(scores) or 1
    baseline = RetrievalBaseline(
        dataset_version=dataset.dataset_version,
        corpus_versions=corpus_versions or {},
        embeddings_model=embeddings_model,
        case_count=len(scores),
        recall_at_k=sum(score.recall for score in scores) / count,
        citation_precision=sum(score.citation_precision for score in scores) / count,
        cases_passed=sum(1 for score in scores if score.passed),
    )
    return baseline, scores


def render_report(baseline: RetrievalBaseline, scores: list[CaseScore]) -> str:
    """Reporte legible para pegar en un PR, comparable entre commits."""
    lines = [
        f"dataset: {baseline.dataset_version}",
        f"embeddings: {baseline.embeddings_model}",
        f"modo: {baseline.retrieval_mode.value}",
        f"casos: {baseline.case_count} ({baseline.cases_passed} sin fallos)",
        f"recall@k: {baseline.recall_at_k:.3f} (objetivo ≥ {RECALL_AT_5_TARGET})",
        f"citation precision: {baseline.citation_precision:.3f} "
        f"(objetivo ≥ {CITATION_PRECISION_TARGET})",
        f"gate: {'CUMPLE' if baseline.meets_gate else 'NO CUMPLE'}",
        "",
    ]
    for score in scores:
        if score.passed:
            continue
        lines.append(f"  ✗ {score.case_id}")
        if score.missing_fragments:
            lines.append(f"      no recuperó: {', '.join(score.missing_fragments)}")
        if score.forbidden_hits:
            lines.append(f"      devolvió fuente prohibida: {', '.join(score.forbidden_hits)}")
        if score.unexpected_results:
            lines.append(
                f"      consulta fuera de alcance: la evidencia recuperada "
                f"({score.returned} fragmentos) se juzgó suficiente para sostener un claim"
            )
    return "\n".join(lines)


def dump_baseline(baseline: RetrievalBaseline, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(baseline.model_dump(mode="json"), indent=2, ensure_ascii=False, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
