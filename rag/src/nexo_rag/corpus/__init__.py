"""Ingesta de corpus: manifests, checksums, fragmentación e indexado (F1.2)."""

from .checksums import ChecksumMismatchError, checksum_of_file, checksum_of_text
from .chunking import MAX_CHUNK_CHARS, MIN_CHUNK_CHARS, TextChunk, chunk_document, chunk_markdown
from .ids import chunk_id, fragment_id, stable_suffix
from .ingestion import CorpusIngestion, IngestionReport
from .manifest import (
    MANIFEST_FILENAME,
    DocumentEntry,
    SourceEntry,
    SourceManifest,
    load_domain_manifest,
    load_manifest,
    manifest_path,
)

__all__ = [
    "MANIFEST_FILENAME",
    "MAX_CHUNK_CHARS",
    "MIN_CHUNK_CHARS",
    "ChecksumMismatchError",
    "CorpusIngestion",
    "DocumentEntry",
    "IngestionReport",
    "SourceEntry",
    "SourceManifest",
    "TextChunk",
    "checksum_of_file",
    "checksum_of_text",
    "chunk_document",
    "chunk_id",
    "chunk_markdown",
    "fragment_id",
    "load_domain_manifest",
    "load_manifest",
    "manifest_path",
    "stable_suffix",
]
