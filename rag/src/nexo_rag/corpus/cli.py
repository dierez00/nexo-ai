"""Utilidades de línea de comandos del corpus.

    python -m nexo_rag.corpus.cli checksums [dominio ...]
    python -m nexo_rag.corpus.cli verify [dominio ...]

`checksums` recalcula y reescribe los hashes declarados en cada `sources.yaml`.
Es el único punto donde un checksum se escribe: copiarlos a mano acaba en un
manifest que dice una cosa y un archivo que dice otra.

`verify` comprueba sin escribir. Es lo que corre la suite y lo que debería
correr CI: un corpus modificado sin actualizar su manifest tiene que romper
algo, y mejor que rompa aquí que en una respuesta al público.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from nexo_contracts import Domain

from .checksums import checksum_of_file
from .manifest import load_domain_manifest, manifest_path

MVP_DOMAINS = (Domain.VEHICULOS, Domain.AYUNTAMIENTO_EMPRESAS)


def repository_root() -> Path:
    """Raíz del repositorio, deducida desde la ubicación de este paquete."""
    return Path(__file__).resolve().parents[4]


def _domains(names: list[str]) -> tuple[Domain, ...]:
    return tuple(Domain(name) for name in names) if names else MVP_DOMAINS


def verify(root: Path, domains: tuple[Domain, ...]) -> list[str]:
    """Discrepancias entre manifest y archivos, como texto accionable."""
    problems: list[str] = []
    for domain in domains:
        manifest = load_domain_manifest(root, domain)
        for source in manifest.sources:
            for entry in source.documents:
                path = root / entry.path
                if not path.exists():
                    problems.append(f"{domain.value}/{entry.document_id}: falta {entry.path}")
                    continue
                actual = checksum_of_file(path)
                if actual != entry.checksum:
                    problems.append(
                        f"{domain.value}/{entry.document_id}: declarado {entry.checksum} "
                        f"≠ real {actual}"
                    )
    return problems


def rewrite_checksums(root: Path, domains: tuple[Domain, ...]) -> int:
    """Reescribe los `checksum:` del manifest con el valor real de cada archivo.

    Edita el YAML por línea en lugar de reserializarlo: volcar el modelo
    borraría los comentarios, que en un manifest de corpus explican por qué una
    fuente está vencida o sustituida.
    """
    updated = 0
    for domain in domains:
        path = manifest_path(root, domain)
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        current: Path | None = None
        for index, line in enumerate(lines):
            path_match = re.match(r"^(\s*)path:\s*(\S+)\s*$", line)
            if path_match:
                current = root / path_match.group(2)
                continue
            checksum_match = re.match(r"^(\s*)checksum:\s*(\S+)\s*$", line)
            if checksum_match and current is not None and current.exists():
                actual = checksum_of_file(current)
                if checksum_match.group(2) != actual:
                    lines[index] = f"{checksum_match.group(1)}checksum: {actual}\n"
                    updated += 1
                current = None
        path.write_text("".join(lines), encoding="utf-8")
    return updated


def main(argv: list[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    if not args or args[0] not in {"checksums", "verify"}:
        print(__doc__)
        return 2

    command, names = args[0], args[1:]
    root = repository_root()
    domains = _domains(names)

    if command == "checksums":
        updated = rewrite_checksums(root, domains)
        print(f"{updated} checksums actualizados en {len(domains)} manifests")
        return 0

    problems = verify(root, domains)
    for problem in problems:
        print(problem, file=sys.stderr)
    print(f"{len(problems)} discrepancias en {len(domains)} manifests")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
