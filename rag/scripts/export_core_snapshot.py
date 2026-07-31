"""Exporta el snapshot y reporte de reingesta Core de forma reproducible."""

from __future__ import annotations

import asyncio

from nexo_rag.corpus import build_global_snapshot, export_snapshot, smoke_snapshot
from nexo_rag.corpus.cli import CORE_DOMAINS, repository_root
from nexo_rag.testing import load_corpus


async def main() -> None:
    root = repository_root()
    corpus = await load_corpus(root=root, domains=CORE_DOMAINS)
    snapshot = build_global_snapshot(corpus)
    problems = smoke_snapshot(snapshot)
    if problems:
        raise SystemExit("; ".join(problems))

    target = export_snapshot(snapshot, root / "data/corpus/core_snapshot.json")
    lines = [
        "# Reporte de ingesta Core",
        "",
        f"- Snapshot: `{snapshot.version}`",
        f"- Digest: `{snapshot.digest}`",
        f"- Dominios: {len(snapshot.corpus_versions)}",
        f"- Chunks: {len(snapshot.lineage)}",
        "- Smoke previo a activación: aprobado",
        "- Reingesta idempotente: cubierta por `rag/tests/test_core_snapshot.py`",
        "",
        "## Conteo por dominio",
        "",
        *[
            f"- `{domain.value}`: {snapshot.chunk_counts[domain]} chunks "
            f"(`{snapshot.corpus_versions[domain]}`)"
            for domain in CORE_DOMAINS
        ],
        "",
    ]
    report = root / "data/corpus/core_reingestion_report.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines), encoding="utf-8")
    print(target.relative_to(root))
    print(report.relative_to(root))


if __name__ == "__main__":
    asyncio.run(main())
