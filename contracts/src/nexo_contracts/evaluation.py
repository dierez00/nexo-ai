"""Contratos de autoverificación y evaluación (§5.6).

El judge mide; no autoriza. Ningún contrato de este módulo puede alterar un
hecho, cambiar el estado de una acción ni sustituir un gate determinista
(`DIE-F4-049`, `DIE-F4-054`).
"""

from __future__ import annotations

from typing import Annotated, Self

from pydantic import Field, model_validator

from .base import NexoModel
from .enums import Domain
from .ids import EvaluationId, FactId, RunId
from .model_gateway import ModelAlias
from .primitives import Score, UtcDatetime


class SelfCheckResult(NexoModel):
    """Autoverificación tipada que cada agente ejecuta sobre su propia salida (§5.6)."""

    schema_valid: bool
    unsupported_claims: int = Field(default=0, ge=0)
    out_of_scope_sources: int = Field(default=0, ge=0)
    forbidden_tool_requests: int = Field(default=0, ge=0)
    notes: Annotated[list[str], Field(max_length=20)] = Field(default_factory=list)

    @property
    def passed(self) -> bool:
        return (
            self.schema_valid
            and self.unsupported_claims == 0
            and self.out_of_scope_sources == 0
            and self.forbidden_tool_requests == 0
        )


class DeterministicEvaluationResult(NexoModel):
    """Métricas calculadas con código, no con un modelo (§5.6).

    Estas son las que constituyen un gate. El judge nunca las reemplaza.
    """

    case_id: str = Field(max_length=120)
    dataset_version: str = Field(max_length=60)
    domain_match: bool
    procedure_match: bool
    source_coverage: Score
    citation_precision: Score
    unsupported_critical_claims: int = Field(ge=0)
    tool_selection_correct: bool
    permission_compliance: bool
    a2ui_schema_valid: bool
    write_verifiable: bool | None = Field(
        default=None, description="Nulo si el caso no incluye escritura."
    )
    questions_asked: int = Field(default=0, ge=0)
    max_questions_allowed: int = Field(default=0, ge=0)

    @property
    def passed(self) -> bool:
        return (
            self.domain_match
            and self.procedure_match
            and self.unsupported_critical_claims == 0
            and self.tool_selection_correct
            and self.permission_compliance
            and self.a2ui_schema_valid
            and self.write_verifiable is not False
            and self.questions_asked <= self.max_questions_allowed
        )


class JudgeRequest(NexoModel):
    """Entrada minimizada del judge (§5.6).

    Recibe la solicitud, la respuesta, los hechos y las citas; no recibe puertos,
    ni credenciales, ni la capacidad de invocar nada.
    """

    evaluation_id: EvaluationId
    run_id: RunId
    rubric_version: str = Field(max_length=60)
    user_request: str = Field(max_length=4000)
    answer: str = Field(max_length=20000)
    fact_ids: Annotated[list[FactId], Field(max_length=200)] = Field(default_factory=list)
    domain: Domain
    generator_model: ModelAlias
    judge_model: ModelAlias

    @model_validator(mode="after")
    def _judge_differs_from_generator(self) -> Self:
        if self.judge_model == self.generator_model:
            raise ValueError(
                f"el judge usa el mismo alias que el generador ({self.judge_model!r}); "
                f"la rúbrica exige un modelo distinto para evitar autoevaluación"
            )
        return self


class JudgeScores(NexoModel):
    """Rúbrica versionada, toda en [0, 1]."""

    domain_accuracy: Score
    tool_selection: Score
    faithfulness: Score
    completeness: Score
    clarity: Score
    a2ui_quality: Score
    permission_compliance: Score


class JudgeResult(NexoModel):
    """Salida tipada del judge (§5.6). Es un dato analítico, nunca una autorización."""

    evaluation_id: EvaluationId
    run_id: RunId
    rubric_version: str = Field(max_length=60)
    generator_model: ModelAlias
    judge_model: ModelAlias
    scores: JudgeScores
    unsupported_claims: Annotated[list[str], Field(max_length=50)] = Field(default_factory=list)
    evidence: str = Field(default="", max_length=2000)
    passed: bool
    evaluated_at: UtcDatetime

    @model_validator(mode="after")
    def _unsupported_claims_cannot_pass(self) -> Self:
        if self.passed and self.unsupported_claims:
            raise ValueError(
                "el judge no puede aprobar una respuesta que él mismo marcó con claims "
                "sin fundamento"
            )
        return self


class EvaluationReport(NexoModel):
    """Reporte comparable entre commits (§5.6).

    Congela todo lo que hace reproducible una medición: dataset, rúbrica,
    aliases, corpus, configuración y semilla.
    """

    report_id: EvaluationId
    dataset_version: str = Field(max_length=60)
    rubric_version: str = Field(max_length=60)
    corpus_versions: dict[Domain, str] = Field(default_factory=dict)
    config_version: str = Field(max_length=60)
    seed: int | None = None
    deterministic_results: Annotated[
        list[DeterministicEvaluationResult], Field(max_length=500)
    ] = Field(default_factory=list)
    judge_results: Annotated[list[JudgeResult], Field(max_length=500)] = Field(
        default_factory=list
    )
    generated_at: UtcDatetime

    @property
    def deterministic_pass_rate(self) -> float:
        if not self.deterministic_results:
            return 0.0
        passed = sum(1 for result in self.deterministic_results if result.passed)
        return passed / len(self.deterministic_results)
