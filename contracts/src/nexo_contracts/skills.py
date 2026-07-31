"""Contrato de skills operativas (§5.7).

Una skill describe *cómo* se resuelve un trámite: qué pasos, en qué orden, con
qué fuentes y tools, cuándo se puede preguntar y qué exige confirmación. Es
declarativa y versionada: una skill nunca amplía permisos por sí misma
(`DIE-F1-113`).
"""

from __future__ import annotations

from typing import Annotated, Self

from pydantic import Field, model_validator

from .base import NexoModel
from .enums import AgentName, Domain
from .ids import SkillId, SourceId
from .primitives import PositiveMillis, SemanticVersion, Slug


class SkillStep(NexoModel):
    """Paso de una skill, con su paralelizabilidad declarada explícitamente."""

    step_id: Slug
    agent: AgentName
    objective: str = Field(max_length=300)
    depends_on: Annotated[list[Slug], Field(max_length=20)] = Field(default_factory=list)
    parallel_group: str | None = Field(
        default=None,
        max_length=40,
        description="Pasos con el mismo grupo pueden ejecutarse en paralelo.",
    )
    deadline_ms: PositiveMillis = 6000
    max_attempts: int = Field(default=1, ge=1, le=5)


class SkillBudgets(NexoModel):
    """Presupuestos de la skill completa."""

    deadline_ms: PositiveMillis = 20000
    max_cost_usd: float = Field(default=0.20, ge=0.0)
    max_questions: int = Field(
        default=1,
        ge=0,
        le=5,
        description="Preguntas máximas admitidas; el gate de preguntas mínimas lo verifica.",
    )
    max_concurrency: int = Field(default=2, ge=1, le=10)


class SkillManifest(NexoModel):
    """Manifiesto versionado de una skill operativa (§5.7)."""

    skill_id: SkillId
    version: SemanticVersion
    title: str = Field(max_length=200)
    domain: Domain
    objective: str = Field(max_length=500)
    owner: str = Field(max_length=200)

    steps: Annotated[list[SkillStep], Field(min_length=1, max_length=50)]
    allowed_sources: Annotated[list[SourceId], Field(max_length=200)] = Field(default_factory=list)
    allowed_tools: Annotated[list[str], Field(max_length=50)] = Field(default_factory=list)

    reusable_inputs: Annotated[list[Slug], Field(max_length=50)] = Field(default_factory=list)
    question_conditions: Annotated[list[str], Field(max_length=20)] = Field(default_factory=list)
    confirmation_required_for: Annotated[list[str], Field(max_length=20)] = Field(
        default_factory=list,
        description="Tools de escritura que exigen confirmación dentro de esta skill.",
    )

    budgets: SkillBudgets = Field(default_factory=SkillBudgets)
    success_criteria: Annotated[list[str], Field(min_length=1, max_length=20)]
    escalation_policy: str = Field(max_length=500)

    prompt_refs: Annotated[list[str], Field(max_length=20)] = Field(default_factory=list)
    schema_refs: Annotated[list[str], Field(max_length=20)] = Field(default_factory=list)
    a2ui_components: Annotated[list[str], Field(max_length=30)] = Field(default_factory=list)

    @model_validator(mode="after")
    def _step_dependencies_resolve(self) -> Self:
        known = {step.step_id for step in self.steps}
        if len(known) != len(self.steps):
            raise ValueError("hay step_id duplicados en la skill")
        for step in self.steps:
            missing = [dep for dep in step.depends_on if dep not in known]
            if missing:
                raise ValueError(
                    f"el paso {step.step_id!r} depende de pasos inexistentes: {missing}"
                )
        return self

    @model_validator(mode="after")
    def _no_cycles(self) -> Self:
        """Un ciclo en las dependencias haría irresoluble el plan; falla al validar."""
        dependencies = {step.step_id: set(step.depends_on) for step in self.steps}
        resolved: set[str] = set()
        pending = dict(dependencies)
        while pending:
            ready = {name for name, deps in pending.items() if deps <= resolved}
            if not ready:
                raise ValueError(
                    f"ciclo de dependencias entre los pasos {sorted(pending)}; "
                    f"una skill debe ser un grafo acíclico"
                )
            resolved |= ready
            pending = {name: deps for name, deps in pending.items() if name not in ready}
        return self

    @model_validator(mode="after")
    def _confirmations_are_declared_tools(self) -> Self:
        unknown = [
            tool for tool in self.confirmation_required_for if tool not in self.allowed_tools
        ]
        if unknown:
            raise ValueError(
                f"la skill exige confirmación para tools que no están en su allowlist: "
                f"{unknown}; una skill no puede ampliar permisos"
            )
        return self
