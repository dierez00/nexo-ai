"""Contrato y carga del dataset `capstone_v1` (`DIE-F2-063`–`066`)."""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path
from typing import Annotated

from pydantic import Field

from nexo_contracts import Domain, NexoModel


class CaseVariant(StrEnum):
    OFFICIAL = "official"
    PARAPHRASE = "paraphrase"
    NEGATIVE = "negative"
    ADVERSARIAL = "adversarial"


class CapstoneCase(NexoModel):
    case_id: str = Field(pattern=r"^cap_[a-z0-9_]{3,80}$")
    dataset_version: str = Field(default="capstone_v1", max_length=60)
    variant: CaseVariant
    message: str = Field(min_length=1, max_length=4000)
    roles: Annotated[list[str], Field(min_length=1, max_length=10)]
    expected_domain: Domain | None = None
    expected_procedure: str | None = Field(default=None, max_length=100)
    expected_sources: Annotated[list[str], Field(max_length=30)] = Field(default_factory=list)
    expected_tools: Annotated[list[str], Field(max_length=20)] = Field(default_factory=list)
    max_questions: int = Field(default=1, ge=0, le=5)
    write_expected: bool = False
    required_a2ui_components: Annotated[list[str], Field(max_length=20)] = Field(
        default_factory=list
    )
    attack_tags: Annotated[list[str], Field(max_length=20)] = Field(default_factory=list)


def load_capstone(path: Path) -> list[CapstoneCase]:
    cases: list[CapstoneCase] = []
    seen: set[str] = set()
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        case = CapstoneCase.model_validate(json.loads(line))
        if case.case_id in seen:
            raise ValueError(f"{path}:{number}: case_id duplicado: {case.case_id}")
        seen.add(case.case_id)
        cases.append(case)
    if not cases:
        raise ValueError(f"{path}: el dataset está vacío")
    return cases


__all__ = ["CapstoneCase", "CaseVariant", "load_capstone"]
