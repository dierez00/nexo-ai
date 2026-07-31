"""Checksums de contenido para ingesta idempotente (`DIE-F1-014`).

El checksum se calcula **antes** de ingerir. Si coincide con el ya registrado,
la versión no cambió y no se vuelve a fragmentar ni a vectorizar: reingerir un
corpus sin cambios no debe crear un solo chunk nuevo (`DIE-F1-019`).

Se normaliza el fin de línea antes de calcularlo. Sin eso, un `git config
core.autocrlf` distinto en otra máquina produciría un checksum diferente para el
mismo contenido, y la ingesta reindexaría el corpus entero sin motivo.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

ALGORITHM = "sha256"


def checksum_of_text(text: str) -> str:
    """Checksum con algoritmo explícito: `sha256:<hex>`."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"{ALGORITHM}:{digest}"


def checksum_of_file(path: Path) -> str:
    return checksum_of_text(path.read_text(encoding="utf-8"))


class ChecksumMismatchError(Exception):
    """El archivo no coincide con el checksum declarado en el manifest.

    Es una condición de integridad, no un detalle: significa que el corpus
    cambió sin que su manifest lo registrara. Ingerirlo produciría respuestas
    distintas sin ninguna explicación en la traza.
    """

    def __init__(self, path: str, declared: str, actual: str) -> None:
        self.path = path
        self.declared = declared
        self.actual = actual
        super().__init__(
            f"{path}: el checksum declarado ({declared}) no coincide con el del archivo "
            f"({actual}); actualiza el manifest o revierte el cambio del documento"
        )
