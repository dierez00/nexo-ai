-- =============================================================================
-- SaaS v1.3.0 — Embeddings deterministas de demo + unicidad de chunks
-- Prepara el terreno para sembrar chunks reales de Vehículos, Salud y Empresas
-- =============================================================================

create extension if not exists pgcrypto;

-- Vector determinista derivado de sha256(input): mismo texto, mismo vector,
-- siempre. Es el equivalente en SQL de `DeterministicEmbeddings`
-- (rag/src/nexo_rag/testing/embeddings.py) — SOLO sirve para poblar
-- `match_chunks` en datos de demostración. No tiene ninguna propiedad
-- semántica: dos textos con el mismo significado no quedan cerca en este
-- espacio. Usar esto para medir recall o precisión produciría un número sin
-- significado; el proveedor real de embeddings sigue pendiente (rag/README.md).
create or replace function public.fake_embedding(input text)
returns vector(1536)
language sql
immutable
as $$
  select (
    '[' || string_agg((get_byte(digest(input, 'sha256'), i % 32) / 255.0)::text, ',') || ']'
  )::vector(1536)
  from generate_series(0, 1535) as i;
$$;

-- Sin esta unique, sembrar el mismo chunk dos veces lo duplicaría — mismo
-- problema que sources/documents tenían antes de 20260504150000_fix_rag_seed_idempotency.sql.
alter table public.chunks
  add constraint chunks_document_chunk_index_key unique (document_id, chunk_index);
