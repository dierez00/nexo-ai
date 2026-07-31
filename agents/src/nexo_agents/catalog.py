"""Catálogo central Core construido desde artefactos versionados (`DIE-F2-001`–`009`).

No duplica los manifests: los proyecta a una vista única y valida sus
referencias. Un dominio, source, tool, prompt, skill o componente huérfano
detiene el arranque antes de que el supervisor pueda delegar.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Annotated

from pydantic import Field, model_validator

from nexo_contracts import AgentName, Domain, NexoModel, SkillManifest
from nexo_contracts.config import ModelRouterConfig, PoliciesConfig
from nexo_mcp.catalog import ToolCatalog
from nexo_rag.corpus.manifest import load_domain_manifest

from .domain_manifest import DomainManifest, load_domains
from .prompts import load_by_ref
from .skills import load_domain_skills, validate_skill


class CatalogLifecycle(StrEnum):
    DRAFT = "draft"
    REVIEW = "review"
    ACTIVE = "active"
    DEPRECATED = "deprecated"


_CATALOG_TRANSITIONS: dict[CatalogLifecycle, frozenset[CatalogLifecycle]] = {
    CatalogLifecycle.DRAFT: frozenset({CatalogLifecycle.REVIEW}),
    CatalogLifecycle.REVIEW: frozenset({CatalogLifecycle.DRAFT, CatalogLifecycle.ACTIVE}),
    CatalogLifecycle.ACTIVE: frozenset({CatalogLifecycle.DEPRECATED}),
    CatalogLifecycle.DEPRECATED: frozenset(),
}


class CatalogEntityKind(StrEnum):
    DEPENDENCY = "dependency"
    DOMAIN = "domain"
    MODULE = "module"
    SERVICE = "service"
    PROCEDURE = "procedure"
    SOURCE = "source"
    AGENT = "agent"
    TOOL = "tool"
    SKILL = "skill"
    POLICY = "policy"
    MODEL = "model"
    A2UI_COMPONENT = "a2ui_component"


class CatalogEntity(NexoModel):
    entity_id: str = Field(pattern=r"^[a-z][a-z0-9:._-]{2,199}$")
    kind: CatalogEntityKind
    version: str = Field(max_length=80)
    domain: Domain | None = None
    title: str = Field(max_length=300)
    references: Annotated[list[str], Field(max_length=100)] = Field(default_factory=list)


class CatalogRelation(NexoModel):
    source_id: str
    relation: str = Field(pattern=r"^[a-z][a-z0-9_]{1,79}$")
    target_id: str


class CentralCatalogSnapshot(NexoModel):
    version: str = Field(max_length=80)
    lifecycle: CatalogLifecycle
    entities: Annotated[list[CatalogEntity], Field(min_length=1, max_length=2_000)]
    relations: Annotated[list[CatalogRelation], Field(max_length=5_000)] = Field(
        default_factory=list
    )

    @model_validator(mode="after")
    def _references_resolve(self) -> CentralCatalogSnapshot:
        known = {entity.entity_id for entity in self.entities}
        if len(known) != len(self.entities):
            raise ValueError("el catálogo central contiene entity_id duplicados")
        dangling = sorted(
            {
                value
                for relation in self.relations
                for value in (relation.source_id, relation.target_id)
                if value not in known
            }
        )
        if dangling:
            raise ValueError(f"el catálogo central contiene referencias huérfanas: {dangling}")
        return self

    def transition(self, target: CatalogLifecycle) -> CentralCatalogSnapshot:
        """Aplica el lifecycle cerrado draft → review → active → deprecated."""
        if target not in _CATALOG_TRANSITIONS[self.lifecycle]:
            raise ValueError(
                f"transición de catálogo no permitida: {self.lifecycle.value} → {target.value}"
            )
        return self.model_copy(update={"lifecycle": target})


@dataclass(frozen=True)
class CentralCatalog:
    """Vista ejecutable que consulta el supervisor antes de delegar."""

    snapshot: CentralCatalogSnapshot
    manifests: dict[Domain, DomainManifest]
    skills: dict[Domain, dict[str, SkillManifest]]
    tools: ToolCatalog

    @classmethod
    def load(
        cls,
        root: Path,
        *,
        domains: tuple[Domain, ...],
        tools: ToolCatalog,
        models: ModelRouterConfig,
        policies: PoliciesConfig,
        a2ui_components: frozenset[str],
    ) -> CentralCatalog:
        manifests = load_domains(root, domains)
        entities: list[CatalogEntity] = []
        relations: list[CatalogRelation] = []
        loaded_skills: dict[Domain, dict[str, SkillManifest]] = {}

        entities.append(
            CatalogEntity(
                entity_id="dependency:inst_demo",
                kind=CatalogEntityKind.DEPENDENCY,
                version="1.0.0",
                title="Institución demostrativa",
            )
        )
        entities.extend(
            CatalogEntity(
                entity_id=f"agent:{agent.value}",
                kind=CatalogEntityKind.AGENT,
                version="1.0.0",
                title=agent.value,
            )
            for agent in AgentName
        )
        entities.append(
            CatalogEntity(
                entity_id=f"policy:{policies.version}",
                kind=CatalogEntityKind.POLICY,
                version=policies.version,
                title="Políticas de ejecución",
            )
        )
        for alias in models.aliases:
            entities.append(
                CatalogEntity(
                    entity_id=f"model:{alias.alias}",
                    kind=CatalogEntityKind.MODEL,
                    version=models.version,
                    title=alias.alias,
                )
            )
        for component in sorted(a2ui_components):
            entities.append(
                CatalogEntity(
                    entity_id=f"a2ui:{component.lower()}",
                    kind=CatalogEntityKind.A2UI_COMPONENT,
                    version="citizen-v1",
                    title=component,
                )
            )

        for domain, manifest in manifests.items():
            load_by_ref(manifest.prompt_ref)
            source_manifest = load_domain_manifest(root, domain)
            source_ids = {source.source_id for source in source_manifest.sources}
            missing_sources = sorted(set(manifest.allowed_sources) - source_ids)
            if missing_sources:
                raise ValueError(
                    f"{domain.value}: sources del dominio inexistentes: {missing_sources}"
                )

            domain_id = f"domain:{domain.value}"
            module_id = f"module:{domain.value}"
            entities.extend(
                [
                    CatalogEntity(
                        entity_id=domain_id,
                        kind=CatalogEntityKind.DOMAIN,
                        version=manifest.version,
                        domain=domain,
                        title=manifest.title,
                    ),
                    CatalogEntity(
                        entity_id=module_id,
                        kind=CatalogEntityKind.MODULE,
                        version=manifest.version,
                        domain=domain,
                        title=manifest.title,
                    ),
                ]
            )
            relations.extend(
                [
                    CatalogRelation(
                        source_id=module_id,
                        relation="belongs_to",
                        target_id=domain_id,
                    ),
                    CatalogRelation(
                        source_id=domain_id,
                        relation="served_by",
                        target_id="dependency:inst_demo",
                    ),
                ]
            )

            for source in source_manifest.sources:
                entity_id = f"source:{source.source_id}"
                entities.append(
                    CatalogEntity(
                        entity_id=entity_id,
                        kind=CatalogEntityKind.SOURCE,
                        version=source_manifest.corpus_version,
                        domain=domain,
                        title=source.title,
                    )
                )
                relations.append(
                    CatalogRelation(
                        source_id=domain_id, relation="allows_source", target_id=entity_id
                    )
                )

            domain_skills = load_domain_skills(root, domain)
            loaded_skills[domain] = dict(domain_skills)
            for skill in domain_skills.values():
                validation = validate_skill(skill, manifest, root=root, check_a2ui=True)
                if not validation.is_valid:
                    raise ValueError(
                        f"{domain.value}/{skill.skill_id}: " + "; ".join(validation.problems)
                    )
                skill_entity = f"skill:{skill.skill_id}"
                entities.append(
                    CatalogEntity(
                        entity_id=skill_entity,
                        kind=CatalogEntityKind.SKILL,
                        version=skill.version,
                        domain=domain,
                        title=skill.title,
                    )
                )
                relations.append(
                    CatalogRelation(
                        source_id=domain_id, relation="offers_skill", target_id=skill_entity
                    )
                )

            for intent in manifest.intents:
                service_id = f"service:{domain.value}:{intent.slug}"
                procedure_id = f"procedure:{domain.value}:{intent.slug}"
                entities.extend(
                    [
                        CatalogEntity(
                            entity_id=service_id,
                            kind=CatalogEntityKind.SERVICE,
                            version=manifest.version,
                            domain=domain,
                            title=intent.title,
                        ),
                        CatalogEntity(
                            entity_id=procedure_id,
                            kind=CatalogEntityKind.PROCEDURE,
                            version=manifest.version,
                            domain=domain,
                            title=intent.title,
                        ),
                    ]
                )
                relations.extend(
                    [
                        CatalogRelation(
                            source_id=domain_id, relation="offers", target_id=service_id
                        ),
                        CatalogRelation(
                            source_id=service_id, relation="implements", target_id=procedure_id
                        ),
                    ]
                )
                if intent.skill_id:
                    relations.append(
                        CatalogRelation(
                            source_id=procedure_id,
                            relation="uses_skill",
                            target_id=f"skill:{intent.skill_id}",
                        )
                    )

            for tool_name in manifest.allowed_tools:
                definition = tools.definition(tool_name)
                if definition is None or definition.metadata.domain is not domain:
                    raise ValueError(
                        f"{domain.value}: tool ausente, deshabilitada o incompatible: {tool_name}"
                    )
                entity_id = f"tool:{tool_name}"
                entities.append(
                    CatalogEntity(
                        entity_id=entity_id,
                        kind=CatalogEntityKind.TOOL,
                        version=definition.version,
                        domain=domain,
                        title=tool_name,
                    )
                )
                relations.append(
                    CatalogRelation(
                        source_id=domain_id, relation="allows_tool", target_id=entity_id
                    )
                )

            for component in manifest.a2ui_components:
                if component not in a2ui_components:
                    raise ValueError(f"{domain.value}: componente A2UI no registrado: {component}")
                relations.append(
                    CatalogRelation(
                        source_id=domain_id,
                        relation="recommends_component",
                        target_id=f"a2ui:{component.lower()}",
                    )
                )

        snapshot = CentralCatalogSnapshot(
            version="core-catalog-2026-07-30",
            lifecycle=CatalogLifecycle.ACTIVE,
            entities=entities,
            relations=relations,
        )
        return cls(snapshot=snapshot, manifests=manifests, skills=loaded_skills, tools=tools)

    def domain(self, domain: Domain) -> DomainManifest | None:
        return self.manifests.get(domain)

    def select_skill(self, domain: Domain, intent_slugs: tuple[str, ...]) -> tuple[str, str] | None:
        manifest = self.manifests.get(domain)
        if manifest is None:
            return None
        for slug in intent_slugs:
            intent = manifest.intent(slug)
            if intent is None or intent.skill_id is None:
                continue
            skill = self.skills[domain].get(intent.skill_id)
            if skill is not None:
                return intent.skill_id, str(skill.version)
        return None

    async def visible_tools(
        self, *, institution_id: str, roles: list[str], domain: Domain
    ) -> frozenset[str]:
        visible = await self.tools.list_tools(
            institution_id=institution_id, roles=roles, domain=domain.value
        )
        return frozenset(tool.name for tool in visible)


__all__ = [
    "CatalogEntity",
    "CatalogEntityKind",
    "CatalogLifecycle",
    "CatalogRelation",
    "CentralCatalog",
    "CentralCatalogSnapshot",
]
