"""Recuperación híbrida y evaluación de suficiencia (F1.3)."""

from .hybrid import (
    LEXICAL_WEIGHT,
    MIN_FUSED_SCORE,
    MIN_LEXICAL_SCORE,
    VECTOR_WEIGHT,
    HybridRetriever,
    cosine,
)
from .lexical import BM25Index, normalize, tokenize
from .sufficiency import (
    CONFIDENT_SCORE,
    RetrievalVerdict,
    SufficiencyAssessment,
    assess,
)

__all__ = [
    "CONFIDENT_SCORE",
    "LEXICAL_WEIGHT",
    "MIN_FUSED_SCORE",
    "MIN_LEXICAL_SCORE",
    "VECTOR_WEIGHT",
    "BM25Index",
    "HybridRetriever",
    "RetrievalVerdict",
    "SufficiencyAssessment",
    "assess",
    "cosine",
    "normalize",
    "tokenize",
]
