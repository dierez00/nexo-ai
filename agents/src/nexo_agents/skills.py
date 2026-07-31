"""Carga y validación de skills operativas (`DIE-F1-110`…`DIE-F1-113`).

Una skill describe *cómo* se resuelve un trámite: qué pasos, en qué orden, qué
puede ir en paralelo, cuándo se permite preguntar y qué exige confirmación. El
contrato `SkillManifest` ya impone su forma; este módulo impone su **coherencia
con el resto del sistema**, que es lo que el contrato no puede saber.

Dos reglas cargan todo el peso:

1. **Una skill nunca amplía permisos** (`DIE-F1-113`). Sus fuentes y sus tools
   tienen que ser un subconjunto de las que el dominio ya declara. Si una skill
   pudiera añadir una tool, la allowlist del dominio dejaría de ser una
   allowlist y pasaría a ser una sugerencia.
2. **Una versión incompatible no se activa** (`DIE-F1-113`). La compatibilidad
   se decide por versión mayor: una skill `2.x` no puede activarse en un sistema
   que soporta `1.x`, porque sus pasos, sus contratos y sus criterios de éxito
   cambiaron de significado.

La validación de componentes A2UI está declarada pero **inactiva**: el catálogo
está diferido por decisión, y comprobar contra un catálogo que no existe daría
falsos negativos. Cuando llegue F1.13, se enciende.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml
from pydantic import ValidationError

from nexo_contracts import ConfigurationError, Domain, SkillManifest

from .domain_manifest import DomainManifest
from .prompts import PromptError, load_by_ref

SKILLS_DIRNAME = "skills"

# Versión mayor de skill que este sistema sabe ejecutar.
SUPPORTED_MAJOR_VERSION = 1

# Agentes transversales: existen para todos los dominios y no se declaran en
# ningún `domain.yaml`. Lo que un dominio declara son sus agentes *propios* —hoy
# solo el navegador—, porque son los que se instancian con su manifiesto, su
# prompt y su allowlist. Exigir que cada dominio repitiera la lista completa
# convertiría el manifiesto en siete líneas idénticas por dominio.
TRANSVERSAL_AGENTS = frozenset(
    {
        "supervisor",
        "classifier",
        "verifier",
        "estimator",
        "transactional",
        "writer",
        "signal_analyst",
        "judge",
        "prompt_assistant",
    }
)


@dataclass
class SkillValidation:
    """Resultado de validar una skill contra su dominio."""

    skill_id: str
    problems: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.problems


def skills_dir(root: Path, domain: Domain) -> Path:
    return root / "domains" / domain.value / SKILLS_DIRNAME


def load_skill(path: Path) -> SkillManifest:
    """Carga y valida la forma de una skill. Falla con ruta, campo y motivo."""
    if not path.exists():
        raise ConfigurationError(str(path), "<archivo>", "la skill no existe")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigurationError(str(path), "<yaml>", f"YAML mal formado: {exc}") from exc
    if not isinstance(raw, dict):
        raise ConfigurationError(str(path), "<raíz>", "se esperaba un mapeo en la raíz")
    try:
        return SkillManifest.model_validate(raw)
    except ValidationError as exc:
        first = exc.errors()[0]
        location = ".".join(str(part) for part in first["loc"]) or "<raíz>"
        raise ConfigurationError(str(path), location, first["msg"]) from exc


def load_domain_skills(root: Path, domain: Domain) -> dict[str, SkillManifest]:
    """Todas las skills declaradas por un dominio, por `skill_id`."""
    directory = skills_dir(root, domain)
    if not directory.exists():
        return {}
    skills: dict[str, SkillManifest] = {}
    for path in sorted(directory.glob("*.yaml")):
        skill = load_skill(path)
        if skill.skill_id in skills:
            raise ConfigurationError(
                str(path), "skill_id", f"skill_id duplicado: {skill.skill_id!r}"
            )
        skills[skill.skill_id] = skill
    return skills


def is_activatable(skill: SkillManifest, *, supported_major: int = SUPPORTED_MAJOR_VERSION) -> bool:
    """Si la versión de la skill es compatible con este sistema (`DIE-F1-113`)."""
    major = int(skill.version.split(".", 1)[0])
    return major == supported_major


def validate_skill(
    skill: SkillManifest,
    domain_manifest: DomainManifest,
    *,
    root: Path | None = None,
    check_a2ui: bool = False,
) -> SkillValidation:
    """Comprueba la coherencia de una skill con su dominio (`DIE-F1-112`)."""
    problems: list[str] = []

    if skill.domain is not domain_manifest.domain:
        problems.append(
            f"la skill declara el dominio '{skill.domain.value}' y vive en "
            f"'{domain_manifest.domain.value}'"
        )

    if not is_activatable(skill):
        problems.append(
            f"versión {skill.version} incompatible: este sistema ejecuta skills "
            f"{SUPPORTED_MAJOR_VERSION}.x"
        )

    # `DIE-F1-113`: subconjunto estricto de lo que el dominio ya autoriza.
    extra_sources = sorted(set(skill.allowed_sources) - set(domain_manifest.allowed_sources))
    if extra_sources:
        problems.append(f"la skill referencia fuentes que su dominio no autoriza: {extra_sources}")

    extra_tools = sorted(set(skill.allowed_tools) - set(domain_manifest.allowed_tools))
    if extra_tools:
        problems.append(f"la skill referencia tools que su dominio no autoriza: {extra_tools}")

    # Toda tool de escritura de la skill debe exigir confirmación explícita.
    writes = set(domain_manifest.write_tools())
    unconfirmed = sorted((set(skill.allowed_tools) & writes) - set(skill.confirmation_required_for))
    if unconfirmed:
        problems.append(
            f"la skill admite tools de escritura sin exigir confirmación: {unconfirmed}"
        )

    # Los agentes de cada paso deben estar declarados por el dominio.
    declared = {agent.value for agent in domain_manifest.agents} | TRANSVERSAL_AGENTS
    unknown_agents = sorted({step.agent.value for step in skill.steps} - declared)
    if unknown_agents:
        problems.append(f"la skill delega en agentes que el dominio no declara: {unknown_agents}")

    for ref in skill.prompt_refs:
        try:
            # La referencia es relativa al paquete de agentes, no a la raíz del
            # repositorio: `load_by_ref` resuelve contra `prompts/` por defecto.
            load_by_ref(ref)
        except PromptError as exc:
            problems.append(str(exc))

    if check_a2ui:
        unknown_components = sorted(
            set(skill.a2ui_components) - set(domain_manifest.a2ui_components)
        )
        if unknown_components:
            problems.append(
                f"la skill usa componentes A2UI que el dominio no recomienda: {unknown_components}"
            )

    return SkillValidation(skill_id=skill.skill_id, problems=problems)


def validate_domain_skills(
    root: Path, domain_manifest: DomainManifest, *, check_a2ui: bool = False
) -> list[SkillValidation]:
    """Valida todas las skills de un dominio y comprueba que las declaradas existan.

    Una intención que apunta a una `skill_id` inexistente es una referencia
    huérfana: el supervisor delegaría a un plan que nadie escribió.
    """
    skills = load_domain_skills(root, domain_manifest.domain)
    results = [
        validate_skill(skill, domain_manifest, root=root, check_a2ui=check_a2ui)
        for skill in skills.values()
    ]

    dangling = sorted(
        {
            intent.skill_id
            for intent in domain_manifest.intents
            if intent.skill_id is not None and intent.skill_id not in skills
        }
    )
    if dangling:
        results.append(
            SkillValidation(
                skill_id="<referencias del manifiesto>",
                problems=[f"intenciones que apuntan a skills inexistentes: {dangling}"],
            )
        )
    return results
