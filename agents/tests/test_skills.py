"""Skills operativas: coherencia con el dominio y no ampliación de permisos.

Cubre `DIE-F1-110`…`DIE-F1-113`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from nexo_agents.domain_manifest import DomainManifest
from nexo_agents.skills import (
    is_activatable,
    load_domain_skills,
    validate_domain_skills,
    validate_skill,
)
from nexo_contracts import AgentName, Domain, SkillManifest
from nexo_rag.corpus.cli import CORE_DOMAINS

pytestmark = pytest.mark.unit


@pytest.fixture(scope="module")
def veh_skill(root: Path) -> SkillManifest:
    return load_domain_skills(root, Domain.VEHICULOS)["skill_veh_renovacion"]


# --- DIE-F1-110: existen y son coherentes -----------------------------------


@pytest.mark.parametrize("domain", CORE_DOMAINS, ids=lambda d: d.value)
def test_every_core_domain_has_valid_skills(root: Path, core_manifests, domain: Domain) -> None:
    results = validate_domain_skills(root, core_manifests[domain], check_a2ui=True)

    assert results, f"{domain.value} no declara ninguna skill"
    for result in results:
        assert result.is_valid, f"{result.skill_id}: {result.problems}"


@pytest.mark.parametrize("domain", CORE_DOMAINS, ids=lambda d: d.value)
def test_every_core_skill_declares_budgets_retries_and_safe_fallback(
    root: Path, domain: Domain
) -> None:
    skills = load_domain_skills(root, domain)

    assert skills
    for skill in skills.values():
        assert skill.budgets.max_questions <= 1
        assert skill.budgets.deadline_ms > 0
        assert skill.escalation_policy
        assert skill.success_criteria
        assert all(step.deadline_ms > 0 for step in skill.steps)
        assert all(step.max_attempts <= 2 for step in skill.steps)


def test_both_official_journeys_have_a_skill(root: Path) -> None:
    vehiculos = load_domain_skills(root, Domain.VEHICULOS)
    empresas = load_domain_skills(root, Domain.AYUNTAMIENTO_EMPRESAS)

    assert "skill_veh_renovacion" in vehiculos
    assert "skill_emp_apertura" in empresas


# --- DIE-F1-111: paralelismo y preguntas declarados -------------------------


def test_parallelisable_steps_are_declared_explicitly(veh_skill: SkillManifest) -> None:
    """En MVP el grafo es secuencial, pero la skill ya dice qué podrá solaparse.

    El fan-out de F4.1 debe poder activarse sin reescribir la skill.
    """
    grouped = [step for step in veh_skill.steps if step.parallel_group]

    assert len(grouped) >= 2
    assert len({step.parallel_group for step in grouped}) == 1


def test_parallel_steps_do_not_depend_on_each_other(veh_skill: SkillManifest) -> None:
    """Dos pasos en el mismo grupo no pueden depender uno del otro."""
    groups: dict[str, list[str]] = {}
    for step in veh_skill.steps:
        if step.parallel_group:
            groups.setdefault(step.parallel_group, []).append(step.step_id)

    for members in groups.values():
        for step in veh_skill.steps:
            if step.step_id in members:
                assert not set(step.depends_on) & set(members)


def test_a_skill_declares_when_it_may_ask(veh_skill: SkillManifest) -> None:
    assert veh_skill.question_conditions
    assert veh_skill.budgets.max_questions <= 1


def test_reusable_inputs_are_declared(veh_skill: SkillManifest) -> None:
    """`DIE-F2-051` se apoyará en esto: no volver a preguntar lo ya sabido."""
    assert veh_skill.reusable_inputs


# --- DIE-F1-113: una skill no amplía permisos -------------------------------


@pytest.mark.security
def test_a_skill_cannot_reference_a_tool_its_domain_forbids(
    root: Path, manifests, veh_skill: SkillManifest
) -> None:
    widened = veh_skill.model_copy(
        update={"allowed_tools": [*veh_skill.allowed_tools, "vehiculos.tool_prohibida"]}
    )

    result = validate_skill(widened, manifests[Domain.VEHICULOS], root=root)

    assert not result.is_valid
    assert any("tools que su dominio no autoriza" in problem for problem in result.problems)


@pytest.mark.security
def test_a_skill_cannot_reference_a_source_its_domain_forbids(
    root: Path, manifests, veh_skill: SkillManifest
) -> None:
    widened = veh_skill.model_copy(
        update={"allowed_sources": [*veh_skill.allowed_sources, "src_ayto_tarifas"]}
    )

    result = validate_skill(widened, manifests[Domain.VEHICULOS], root=root)

    assert not result.is_valid
    assert any("fuentes que su dominio no autoriza" in problem for problem in result.problems)


@pytest.mark.security
def test_a_write_tool_without_declared_confirmation_is_rejected(
    root: Path, manifests, veh_skill: SkillManifest
) -> None:
    """Una escritura dentro de una skill sigue exigiendo confirmación explícita."""
    lax = veh_skill.model_copy(update={"confirmation_required_for": []})

    result = validate_skill(lax, manifests[Domain.VEHICULOS], root=root)

    assert not result.is_valid
    assert any("sin exigir confirmación" in problem for problem in result.problems)


def test_the_contract_itself_rejects_confirming_an_undeclared_tool(
    veh_skill: SkillManifest,
) -> None:
    """La primera barrera es el contrato, antes de llegar al validador."""
    with pytest.raises(ValueError, match="no puede ampliar permisos"):
        veh_skill.model_copy(
            update={"confirmation_required_for": ["vehiculos.tool_fantasma"]}
        ).model_validate(
            {
                **veh_skill.model_dump(mode="json"),
                "confirmation_required_for": ["vehiculos.tool_fantasma"],
            }
        )


# --- DIE-F1-113: versión incompatible no se activa --------------------------


@pytest.mark.parametrize(
    ("version", "activatable"),
    [("1.0.0", True), ("1.4.2", True), ("2.0.0", False), ("0.9.0", False)],
)
def test_only_compatible_major_versions_activate(
    veh_skill: SkillManifest, version: str, activatable: bool
) -> None:
    assert is_activatable(veh_skill.model_copy(update={"version": version})) is activatable


def test_an_incompatible_version_is_reported_as_a_problem(
    root: Path, manifests, veh_skill: SkillManifest
) -> None:
    result = validate_skill(
        veh_skill.model_copy(update={"version": "2.0.0"}), manifests[Domain.VEHICULOS], root=root
    )

    assert not result.is_valid
    assert any("incompatible" in problem for problem in result.problems)


# --- DIE-F1-112: referencias resolubles -------------------------------------


def test_a_dangling_prompt_reference_is_detected(
    root: Path, manifests, veh_skill: SkillManifest
) -> None:
    broken = veh_skill.model_copy(update={"prompt_refs": ["nexo_agents/prompts/inexistente.v1.md"]})

    result = validate_skill(broken, manifests[Domain.VEHICULOS], root=root)

    assert not result.is_valid
    assert any("no existe el prompt" in problem for problem in result.problems)


def test_an_intent_pointing_at_a_missing_skill_is_detected(root: Path, manifests) -> None:
    """Una referencia huérfana haría que el supervisor delegue a un plan inexistente."""
    manifest = manifests[Domain.VEHICULOS]
    payload = manifest.model_dump(mode="json")
    payload["intents"][0]["skill_id"] = "skill_que_nadie_escribio"

    results = validate_domain_skills(root, DomainManifest.model_validate(payload))

    assert any(not result.is_valid for result in results)


def test_a_skill_from_another_domain_is_rejected(
    root: Path, manifests, veh_skill: SkillManifest
) -> None:
    result = validate_skill(veh_skill, manifests[Domain.AYUNTAMIENTO_EMPRESAS], root=root)

    assert not result.is_valid


def test_transversal_agents_do_not_need_to_be_declared_per_domain(
    root: Path, manifests, veh_skill: SkillManifest
) -> None:
    """El dominio declara sus agentes propios; el resto existe para todos.

    Exigir que cada `domain.yaml` repitiera los nueve agentes transversales
    convertiría el manifiesto en ruido idéntico por dominio.
    """
    assert manifests[Domain.VEHICULOS].agents == [AgentName.DOMAIN_NAVIGATOR]
    assert {step.agent for step in veh_skill.steps} > {AgentName.DOMAIN_NAVIGATOR}
    assert validate_skill(veh_skill, manifests[Domain.VEHICULOS], root=root).is_valid
