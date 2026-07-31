"""Prompts versionados y sustitución de variables (`DIE-F1-030`, `DIE-F1-039`).

Un prompt es un artefacto versionado, no una constante de código: su versión
viaja en `ChatRequest.prompt_version`, se registra en el evento y se congela en
cada baseline. Un número medido con otro prompt no es comparable con el
anterior, así que cambiar el texto sin cambiar la versión invalida la medición
sin que nadie lo note.

La sustitución es deliberadamente tonta —`{{variable}}` y nada más— porque un
motor de plantillas con lógica acabaría con condicionales dentro del prompt, y
entonces la versión dejaría de describir lo que el modelo recibió.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_PLACEHOLDER = re.compile(r"\{\{(\w+)\}\}")
_VERSION_IN_NAME = re.compile(r"\.(v\d+)\.md$")

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


class PromptError(Exception):
    """El prompt no existe o se renderizó con variables incompletas."""


@dataclass(frozen=True)
class Prompt:
    """Una plantilla versionada, cargada desde disco."""

    name: str
    version: str
    template: str

    @property
    def ref(self) -> str:
        """Referencia estable que viaja en eventos y evaluaciones."""
        return f"nexo_agents/prompts/{self.name}.{self.version}.md"

    def variables(self) -> frozenset[str]:
        return frozenset(_PLACEHOLDER.findall(self.template))

    def render(self, **values: str) -> str:
        """Sustituye las variables. Una variable sin valor es un error.

        Renderizar con un hueco sin rellenar produciría un prompt con
        `{{user_message}}` literal, que el modelo interpretaría como cualquier
        otra cosa. Es mejor fallar aquí.
        """
        missing = sorted(self.variables() - set(values))
        if missing:
            raise PromptError(f"faltan variables para renderizar '{self.ref}': {missing}")
        return _PLACEHOLDER.sub(lambda match: values[match.group(1)], self.template)


@lru_cache(maxsize=64)
def load_prompt(name: str, version: str = "v1", *, directory: Path | None = None) -> Prompt:
    """Carga `<name>.<version>.md` desde el directorio de prompts."""
    base = directory or PROMPTS_DIR
    path = base / f"{name}.{version}.md"
    if not path.exists():
        available = sorted(p.name for p in base.glob("*.md"))
        raise PromptError(f"no existe el prompt {path.name!r}; disponibles: {available}")
    return Prompt(name=name, version=version, template=path.read_text(encoding="utf-8"))


def load_by_ref(ref: str, *, directory: Path | None = None) -> Prompt:
    """Carga un prompt por la referencia que declara un `domain.yaml`.

    La referencia tiene la forma `nexo_agents/prompts/<name>.<version>.md`, de
    modo que el manifiesto apunta a un archivo concreto y no a un nombre lógico
    que alguien pueda reapuntar sin darse cuenta.
    """
    filename = Path(ref).name
    match = _VERSION_IN_NAME.search(filename)
    if match is None:
        raise PromptError(
            f"referencia de prompt sin versión: {ref!r}; se espera '<nombre>.v<N>.md'"
        )
    version = match.group(1)
    name = filename[: -len(f".{version}.md")]
    return load_prompt(name, version, directory=directory)
