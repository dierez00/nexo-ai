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

## Estado tras Fase 1

Solo puertos y dobles: `RetrieverPort`, `EmbeddingsPort` y `ChunkRepositoryPort`
en `ports.py`, con implementaciones en memoria en `testing/`.

El doble de retrieval aplica los mismos filtros lógicos que aplicará el
repositorio real —institución, dominio, estado y vigencia antes de puntuar— para
que una prueba que pasa con él siga significando algo con PostgreSQL.

Implementados corpus versionado de vehículos/empresas, ingesta idempotente,
chunking Markdown, BM25, embeddings, fusión híbrida, filtros de vigencia y
suficiencia de evidencia. El baseline semántico versionado obtiene
recall@5/citation precision **1.000/1.000** sobre los 15 casos sintéticos del
MVP; los límites de esa medición están en
[`docs/team/fase1_hallazgos.md`](../docs/team/fase1_hallazgos.md).
