"""Métricas deterministas del capstone (`DIE-F2-067`–`071`)."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from nexo_contracts import DeterministicEvaluationResult, Domain, NexoModel

from .dataset import CapstoneCase


class EvaluationObservation(NexoModel):
    case_id: str
    domain: Domain | None = None
    procedure: str | None = None
    source_ids: Annotated[list[str], Field(max_length=100)] = Field(default_factory=list)
    citation_source_ids: Annotated[list[str], Field(max_length=100)] = Field(default_factory=list)
    unsupported_critical_claims: int = Field(default=0, ge=0)
    selected_tools: Annotated[list[str], Field(max_length=50)] = Field(default_factory=list)
    permission_compliance: bool = True
    a2ui_schema_valid: bool = True
    a2ui_components: Annotated[list[str], Field(max_length=100)] = Field(default_factory=list)
    write_verifiable: bool | None = None
    questions_asked: int = Field(default=0, ge=0)
    catalog_version: str = Field(max_length=80)
    skill_id: str | None = Field(default=None, max_length=80)
    skill_version: str | None = Field(default=None, max_length=40)


def evaluate_case(
    case: CapstoneCase,
    observation: EvaluationObservation,
) -> DeterministicEvaluationResult:
    if observation.case_id != case.case_id:
        raise ValueError(
            f"observación {observation.case_id!r} no corresponde al caso {case.case_id!r}"
        )

    expected_sources = set(case.expected_sources)
    observed_sources = set(observation.source_ids)
    citations = observation.citation_source_ids
    coverage = (
        len(expected_sources & observed_sources) / len(expected_sources)
        if expected_sources
        else 1.0
    )
    precision = (
        sum(source in expected_sources for source in citations) / len(citations)
        if citations
        else (1.0 if not expected_sources else 0.0)
    )
    tools_match = set(observation.selected_tools) == set(case.expected_tools)
    components_present = set(case.required_a2ui_components) <= set(observation.a2ui_components)
    write_verifiable = observation.write_verifiable if case.write_expected else None

    return DeterministicEvaluationResult(
        case_id=case.case_id,
        dataset_version=case.dataset_version,
        domain_match=observation.domain is case.expected_domain,
        procedure_match=observation.procedure == case.expected_procedure,
        source_coverage=coverage,
        citation_precision=precision,
        unsupported_critical_claims=observation.unsupported_critical_claims,
        tool_selection_correct=tools_match,
        permission_compliance=observation.permission_compliance,
        a2ui_schema_valid=observation.a2ui_schema_valid and components_present,
        write_verifiable=write_verifiable,
        questions_asked=observation.questions_asked,
        max_questions_allowed=case.max_questions,
    )


__all__ = ["EvaluationObservation", "evaluate_case"]
