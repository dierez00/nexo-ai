"""Manifests de fuentes documentales (`DIE-F1-009`, `DIE-F1-010`, `DIE-F1-011`).

Un `sources.yaml` por dominio declara de dónde viene cada documento y bajo qué
condiciones puede citarse. Los metadatos obligatorios no son burocracia: son
exactamente lo que hace auditable una respuesta. Sin institución, responsable,
licencia, vigencia y checksum, una fuente no puede activarse, y una fuente que
no puede activarse no alimenta el retrieval.

La distinción entre contenido sintético e institucional autorizado
(`DIE-F1-011`) viaja en `is_synthetic` y se propaga hasta la respuesta: mientras
todo el corpus del MVP sea sintético, la persona usuaria debe poder saberlo.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Self

import yaml
from pydantic import Field, model_validator

from nexo_contracts import (
    ConfigurationError,
    Document,
    Domain,
    NexoModel,
    Source,
    SourceStatus,
)
from nexo_contracts.ids import DocumentId, InstitutionId, SourceId
from nexo_contracts.primitives import CheckedValidityWindow, UtcDatetime
from nexo_contracts.rag import Checksum

MANIFEST_FILENAME = "sources.yaml"


class DocumentEntry(NexoModel):
    """Un archivo concreto de una fuente, en una versión concreta.

    `checksum` se declara en el manifest y la ingesta lo **verifica** contra el
    archivo. No es redundancia: es lo que convierte una modificación silenciosa
    del corpus en un rechazo con motivo en vez de en una respuesta distinta sin
    explicación (`DIE-F1-014`).
    """

    document_id: DocumentId
    title: str = Field(max_length=300)
    version: str = Field(max_length=40, pattern=r"^v\d+$")
    media_type: str = Field(default="text/markdown", max_length=100)
    path: str = Field(
        max_length=500,
        description="Ruta relativa a la raíz del repositorio; la ingesta nunca la sobrescribe.",
    )
    checksum: Checksum
    supersedes: str | None = Field(default=None, max_length=40, pattern=r"^v\d+$")


class SourceEntry(NexoModel):
    """Una fuente documental con toda su procedencia (`DIE-F1-010`)."""

    source_id: SourceId
    title: str = Field(max_length=300)
    institution_id: InstitutionId
    publisher: str = Field(max_length=200)
    owner: str = Field(max_length=200, description="Responsable interno de mantenerla al día.")
    license: str = Field(max_length=200)
    origin_url: str | None = Field(default=None, max_length=1000)
    status: SourceStatus = SourceStatus.DRAFT
    validity: CheckedValidityWindow
    verified_at: UtcDatetime | None = None
    is_synthetic: bool = True
    superseded_by: SourceId | None = Field(
        default=None,
        description="Fuente que la reemplaza; obligatorio cuando el estado es 'superseded'.",
    )
    documents: Annotated[list[DocumentEntry], Field(min_length=1, max_length=50)]

    @model_validator(mode="after")
    def _active_sources_are_verified(self) -> Self:
        """Refleja la invariante de `Source`: activa exige `verified_at`."""
        if self.status is SourceStatus.ACTIVE and self.verified_at is None:
            raise ValueError(
                f"la fuente {self.source_id!r} se declara activa sin verified_at; "
                f"el retrieval solo entrega evidencia verificada"
            )
        return self

    @model_validator(mode="after")
    def _superseded_sources_name_their_successor(self) -> Self:
        if self.status is SourceStatus.SUPERSEDED and self.superseded_by is None:
            raise ValueError(
                f"la fuente {self.source_id!r} está sustituida pero no dice por cuál; "
                f"sin sucesor no se puede explicar por qué dejó de citarse"
            )
        return self

    @model_validator(mode="after")
    def _document_versions_are_unique(self) -> Self:
        keys = [(doc.document_id, doc.version) for doc in self.documents]
        if len(keys) != len(set(keys)):
            raise ValueError(f"la fuente {self.source_id!r} declara documentos duplicados")
        return self

    def to_contract(self, domain: Domain) -> Source:
        """Proyecta la entrada del manifest al contrato publicado `Source`."""
        return Source(
            source_id=self.source_id,
            title=self.title,
            institution_id=self.institution_id,
            domain=domain,
            origin_url=self.origin_url,
            publisher=self.publisher,
            owner=self.owner,
            license=self.license,
            status=self.status,
            validity=self.validity,
            verified_at=self.verified_at,
            is_synthetic=self.is_synthetic,
        )

    def document_contract(self, entry: DocumentEntry) -> Document:
        return Document(
            document_id=entry.document_id,
            source_id=self.source_id,
            title=entry.title,
            media_type=entry.media_type,
            original_path=entry.path,
        )


class SourceManifest(NexoModel):
    """`domains/<slug>/sources.yaml`: el corpus declarado de un dominio."""

    version: str = Field(max_length=80, pattern=r"^[a-z0-9][a-z0-9._-]{2,79}$")
    domain: Domain
    corpus_version: str = Field(max_length=120)
    sources: Annotated[list[SourceEntry], Field(min_length=1, max_length=200)]

    @model_validator(mode="after")
    def _source_ids_are_unique(self) -> Self:
        ids = [source.source_id for source in self.sources]
        if len(ids) != len(set(ids)):
            raise ValueError("hay source_id duplicados en el manifest")
        return self

    @model_validator(mode="after")
    def _successors_exist_in_the_manifest(self) -> Self:
        """Una fuente no puede ser sustituida por otra que el corpus no conoce."""
        known = {source.source_id for source in self.sources}
        dangling = sorted(
            {
                source.superseded_by
                for source in self.sources
                if source.superseded_by is not None and source.superseded_by not in known
            }
        )
        if dangling:
            raise ValueError(f"fuentes sucesoras que no existen en el manifest: {dangling}")
        return self

    @model_validator(mode="after")
    def _at_least_one_source_is_active(self) -> Self:
        if not any(source.status is SourceStatus.ACTIVE for source in self.sources):
            raise ValueError(
                f"el manifest de {self.domain.value} no tiene ninguna fuente activa; "
                f"un dominio sin evidencia vigente no puede responder nada"
            )
        return self

    def active(self) -> list[SourceEntry]:
        return [source for source in self.sources if source.status is SourceStatus.ACTIVE]

    def by_id(self, source_id: str) -> SourceEntry | None:
        return next((s for s in self.sources if s.source_id == source_id), None)


def manifest_path(root: Path, domain: Domain) -> Path:
    return root / "domains" / domain.value / MANIFEST_FILENAME


def load_manifest(path: Path) -> SourceManifest:
    """Carga y valida un manifest. Un manifest inválido detiene la ingesta.

    Falla igual que la configuración del arranque: con ruta, campo y motivo. Un
    corpus mal declarado que se ingiere a medias es peor que uno que no se
    ingiere (`DIE-F0-036`).
    """
    if not path.exists():
        raise ConfigurationError(str(path), "<archivo>", "el manifest no existe")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigurationError(str(path), "<yaml>", f"YAML mal formado: {exc}") from exc
    if not isinstance(raw, dict):
        raise ConfigurationError(str(path), "<raíz>", "se esperaba un mapeo en la raíz")

    from pydantic import ValidationError

    try:
        return SourceManifest.model_validate(raw)
    except ValidationError as exc:
        first = exc.errors()[0]
        location = ".".join(str(part) for part in first["loc"]) or "<raíz>"
        raise ConfigurationError(str(path), location, first["msg"]) from exc


def load_domain_manifest(root: Path, domain: Domain) -> SourceManifest:
    manifest = load_manifest(manifest_path(root, domain))
    if manifest.domain is not domain:
        raise ConfigurationError(
            str(manifest_path(root, domain)),
            "domain",
            f"el manifest declara el dominio {manifest.domain.value!r} pero vive en la "
            f"carpeta de {domain.value!r}",
        )
    return manifest
