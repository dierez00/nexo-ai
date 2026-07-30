# RAG

## Objetivo

Ingerir y recuperar evidencia institucional vigente, verificable y autorizada.

## Debe contener

Metadata, hashing, chunking, embeddings, búsqueda híbrida, filtros por dominio/institución/vigencia y `SourceCitation`.

## No debe contener

Tools, secretos, respuestas finales ni documentos sin procedencia.

## Convenciones

Todo documento registra `source_id`, dominio, versión, vigencia, estado, responsable y checksum. La ingesta es idempotente y conserva el texto original.

## Dependencias y responsable

Consume repositorios y `data/documents`; expone contratos, no detalles de pgvector. Diego es responsable; Daher apoya schema e índices.

## Ejemplos y tareas

`ingestion.py`, `retriever.py`, `metadata.py`. Crear corpus MVP, búsqueda híbrida y evaluaciones recall@5/citation precision.

## Terminado

Toda recuperación incluye citas activas, nunca cruza namespaces no autorizados y reingerir no duplica chunks.
