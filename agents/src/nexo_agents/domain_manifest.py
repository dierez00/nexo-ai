"""Manifiesto de dominio: `domains/<slug>/domain.yaml` (`DIE-F1-038`).

Un dominio declara qué sabe hacer y con qué. Todo lo que un navegador puede
tocar —intenciones, fuentes, tools, prompts, presupuesto de preguntas— está
aquí, en datos versionados, y no repartido por el código.

Tres reglas que el schema hace cumplir en vez de confiar en la disciplina:

1. **La allowlist de tools es cerrada y coherente con el prefijo del dominio.**
   Un dominio no puede declarar una tool de otro (`DIE-F1-040`).
2. **Una intención que exige escritura debe nombrar la tool exacta.** No existe
   forma de declarar «este dominio puede escribir».
3. **Las fuentes referenciadas deben existir en el `sources.yaml` del dominio.**
   Se valida al cargar; una referencia huérfana detiene el arranque.

En Fase 2 este manifiesto se absorbe en el catálogo central (`DIE-F2-003`), que
añade relaciones entre trámites y dependencias. La forma de los datos está
pensada para que esa absorción sea aditiva.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Self

import yaml
from pydantic import Field, ValidationError, model_validator

from nexo_contracts import AgentName, ConfigurationError, Domain, NexoModel
from nexo_contracts.ids import SourceId
from nexo_contracts.primitives import PositiveMillis, Slug
from nexo_contracts.tools import ToolName

MANIFEST_FILENAME = "domain.yaml"

# Prefijo de tool por dominio. Duplica deliberadamente la tabla de
# `nexo_contracts.tools`: aquí se valida configuración, allí el contrato, y las
# dos deben coincidir. Si divergen, la prueba de coherencia lo detecta.
_TOOL_PREFIX: dict[Domain, str] = {
    Domain.VEHICULOS: "vehiculos",
    Domain.AYUNTAMIENTO_EMPRESAS: "ayuntamiento",
    Domain.REGISTRO_CIVIL: "registro_civil",
    Domain.SALUD: "salud",
    Domain.GANADERIA: "ganaderia",
}


class IntentDeclaration(NexoModel):
    """Una intención que el dominio sabe atender.

    `keywords` no es para que el modelo clasifique —eso lo hace el prompt— sino
    para el **fallback determinista** (`DIE-F1-034`): cuando la salida del
    modelo no cumple el contrato, los casos oficiales deben seguir clasificando
    sin él. Un MVP que solo funciona con el proveedor disponible no es un MVP
    demostrable.
    """

    slug: Slug
    title: str = Field(max_length=200)
    description: str = Field(default="", max_length=500)
    keywords: Annotated[list[str], Field(min_length=1, max_length=40)]
    write_tool: ToolName | None = Field(
        default=None,
        description="Tool de escritura que cierra esta intención, si la tiene.",
    )
    skill_id: str | None = Field(default=None, max_length=80)


class DomainPolicies(NexoModel):
    """Límites operativos del dominio."""

    max_questions: int = Field(
        default=1,
        ge=0,
        le=5,
        description="Preguntas máximas antes de responder (`DIE-F1-044`).",
    )
    retrieval_top_k: int = Field(default=5, ge=1, le=20)
    navigator_deadline_ms: PositiveMillis = 8000


class DomainManifest(NexoModel):
    """`domains/<slug>/domain.yaml`."""

    version: str = Field(max_length=80, pattern=r"^[a-z0-9][a-z0-9._-]{2,79}$")
    domain: Domain
    title: str = Field(max_length=200)
    owner: str = Field(max_length=200)

    intents: Annotated[list[IntentDeclaration], Field(min_length=1, max_length=30)]
    agents: Annotated[list[AgentName], Field(min_length=1, max_length=10)]
    allowed_sources: Annotated[list[SourceId], Field(min_length=1, max_length=100)]
    allowed_tools: Annotated[list[ToolName], Field(max_length=50)] = Field(default_factory=list)

    prompt_ref: str = Field(
        max_length=200, description="Prompt versionado del navegador de este dominio."
    )
    policies: DomainPolicies = Field(default_factory=DomainPolicies)
    a2ui_components: Annotated[list[str], Field(max_length=30)] = Field(
        default_factory=list,
        description="Componentes del catálogo ciudadano que puede usar el dominio.",
    )

    @model_validator(mode="after")
    def _tools_belong_to_this_domain(self) -> Self:
        """`DIE-F1-040`: un dominio no puede declarar la tool de otro."""
        expected = _TOOL_PREFIX[self.domain]
        foreign = sorted({tool for tool in self.allowed_tools if tool.split(".", 1)[0] != expected})
        if foreign:
            raise ValueError(
                f"el dominio '{self.domain.value}' declara tools ajenas {foreign}; "
                f"su prefijo es '{expected}'"
            )
        return self

    @model_validator(mode="after")
    def _write_tools_are_in_the_allowlist(self) -> Self:
        unknown = sorted(
            {
                intent.write_tool
                for intent in self.intents
                if intent.write_tool is not None and intent.write_tool not in self.allowed_tools
            }
        )
        if unknown:
            raise ValueError(
                f"hay intenciones que apuntan a tools de escritura fuera de la allowlist: "
                f"{unknown}; una intención no puede ampliar permisos"
            )
        return self

    @model_validator(mode="after")
    def _intent_slugs_are_unique(self) -> Self:
        slugs = [intent.slug for intent in self.intents]
        if len(slugs) != len(set(slugs)):
            raise ValueError("hay intenciones duplicadas en el manifiesto de dominio")
        return self

    @model_validator(mode="after")
    def _the_navigator_is_declared(self) -> Self:
        if AgentName.DOMAIN_NAVIGATOR not in self.agents:
            raise ValueError(
                f"el dominio '{self.domain.value}' no declara un navegador; sin él nadie "
                f"puede resolver sus intenciones"
            )
        return self

    def intent(self, slug: str) -> IntentDeclaration | None:
        return next((item for item in self.intents if item.slug == slug), None)

    def intent_slugs(self) -> tuple[str, ...]:
        return tuple(intent.slug for intent in self.intents)

    def write_tools(self) -> tuple[str, ...]:
        return tuple(sorted({intent.write_tool for intent in self.intents if intent.write_tool}))


def manifest_path(root: Path, domain: Domain) -> Path:
    return root / "domains" / domain.value / MANIFEST_FILENAME


def load_domain(root: Path, domain: Domain) -> DomainManifest:
    """Carga y valida un manifiesto. Falla con ruta, campo y motivo."""
    path = manifest_path(root, domain)
    if not path.exists():
        raise ConfigurationError(str(path), "<archivo>", "el manifiesto de dominio no existe")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigurationError(str(path), "<yaml>", f"YAML mal formado: {exc}") from exc
    if not isinstance(raw, dict):
        raise ConfigurationError(str(path), "<raíz>", "se esperaba un mapeo en la raíz")

    try:
        manifest = DomainManifest.model_validate(raw)
    except ValidationError as exc:
        first = exc.errors()[0]
        location = ".".join(str(part) for part in first["loc"]) or "<raíz>"
        raise ConfigurationError(str(path), location, first["msg"]) from exc

    if manifest.domain is not domain:
        raise ConfigurationError(
            str(path),
            "domain",
            f"declara el dominio '{manifest.domain.value}' pero vive en la carpeta de "
            f"'{domain.value}'",
        )
    return manifest


def load_domains(root: Path, domains: tuple[Domain, ...]) -> dict[Domain, DomainManifest]:
    return {domain: load_domain(root, domain) for domain in domains}
