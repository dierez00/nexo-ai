"""Medición del baseline de retrieval (`DIE-F1-029`).

    python -m nexo_rag.baseline            # perfil offline (embeddings falsos)
    python -m nexo_rag.baseline --semantic # embeddings reales, requiere descarga

Los dos perfiles miden cosas distintas y ambos números son útiles:

- **offline** es el que corre en la suite y en CI. Con embeddings sin semántica,
  la mitad vectorial aporta ruido cercano a cero, así que lo que mide es
  esencialmente el comportamiento **léxico** del retriever. Sirve como detector
  de regresión: si baja, algo se rompió en filtros, fusión o chunking.
- **semantic** es el que puede compararse contra el gate de §3 (recall@5 ≥ 0.80,
  citation precision ≥ 0.90), porque es el único con recuperación semántica de
  verdad. Descarga un modelo la primera vez, así que no forma parte del perfil
  offline obligatorio.

Reportar el número offline como si fuera el del gate sería exactamente el error
que TD-02 advierte, así que el reporte siempre dice con qué modelo se midió.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from nexo_contracts import Domain, RetrievalMode, RetrievalQuery, RetrievalResponse

from .corpus.cli import MVP_DOMAINS, repository_root
from .evaluation import (
    CaseScore,
    RetrievalBaseline,
    RetrievalDataset,
    dump_baseline,
    measure,
    render_report,
    score_case,
)
from .ports import EmbeddingsPort, RetrieverPort
from .testing import DeterministicEmbeddings, load_corpus

DATASET_PATH = Path("rag/datasets/retrieval_mvp.v1.json")
BASELINE_PATH = Path("rag/datasets/baseline_retrieval.json")


class _DomainRouter:
    """Enruta cada consulta al retriever del dominio que declara.

    El dataset cruza dominios y cada uno tiene su propia `corpus_version`, que
    viaja en la citación. Un solo retriever para ambos citaría la versión
    equivocada en la mitad de los casos.
    """

    def __init__(self, retrievers: dict[Domain, RetrieverPort]) -> None:
        self._retrievers = retrievers

    async def retrieve(self, query: RetrievalQuery) -> RetrievalResponse:
        return await self._retrievers[query.domain].retrieve(query)


async def run(
    *,
    embeddings: EmbeddingsPort,
    root: Path | None = None,
    dataset_path: Path | None = None,
) -> tuple[RetrievalBaseline, list[CaseScore]]:
    """Ingiere el corpus, ejecuta el dataset y devuelve el baseline."""
    resolved_root = root or repository_root()
    corpus = await load_corpus(root=resolved_root, domains=MVP_DOMAINS, embeddings=embeddings)
    dataset = RetrievalDataset.load(resolved_root / (dataset_path or DATASET_PATH))

    router = _DomainRouter({domain: corpus.retriever(domain) for domain in MVP_DOMAINS})
    baseline, scores = await measure(
        router,
        dataset,
        embeddings_model=embeddings.model_name,
        corpus_versions=corpus.corpus_versions,
    )
    return baseline, scores


async def run_lexical_only(
    *, root: Path | None = None
) -> tuple[RetrievalBaseline, list[CaseScore]]:
    """Baseline con la mitad léxica aislada, para atribuir una regresión.

    Si el número híbrido cae y este no, el problema está en los embeddings o en
    la fusión; si caen los dos, está en el corpus, el chunking o los filtros.
    """
    resolved_root = root or repository_root()
    corpus = await load_corpus(root=resolved_root, domains=MVP_DOMAINS)
    dataset = RetrievalDataset.load(resolved_root / DATASET_PATH)

    scores: list[CaseScore] = []
    for case in dataset.cases:
        query = case.to_query().model_copy(update={"retrieval_mode": RetrievalMode.LEXICAL})
        response = await corpus.retriever(case.domain).retrieve(query)
        scores.append(score_case(case, response))

    count = len(scores) or 1
    baseline = RetrievalBaseline(
        dataset_version=dataset.dataset_version,
        corpus_versions=corpus.corpus_versions,
        embeddings_model="n/a (solo léxico)",
        retrieval_mode=RetrievalMode.LEXICAL,
        case_count=len(scores),
        recall_at_k=sum(score.recall for score in scores) / count,
        citation_precision=sum(score.citation_precision for score in scores) / count,
        cases_passed=sum(1 for score in scores if score.passed),
    )
    return baseline, scores


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Baseline de retrieval del MVP")
    parser.add_argument(
        "--semantic",
        action="store_true",
        help="usa embeddings locales reales; descarga el modelo la primera vez",
    )
    parser.add_argument("--lexical", action="store_true", help="mide solo la mitad léxica (BM25)")
    parser.add_argument("--write", action="store_true", help="guarda el baseline en disco")
    args = parser.parse_args(argv)

    if args.lexical:
        baseline, scores = asyncio.run(run_lexical_only())
    else:
        embeddings: EmbeddingsPort
        if args.semantic:
            from .embeddings import StaticSemanticEmbeddings

            embeddings = StaticSemanticEmbeddings()
        else:
            embeddings = DeterministicEmbeddings()
        baseline, scores = asyncio.run(run(embeddings=embeddings))

    print(render_report(baseline, scores))
    if args.write:
        path = repository_root() / BASELINE_PATH
        dump_baseline(baseline, path)
        print(f"\nbaseline escrito en {BASELINE_PATH}")
    return 0 if baseline.cases_passed == baseline.case_count else 1


if __name__ == "__main__":
    sys.exit(main())
