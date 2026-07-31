-- =============================================================================
-- RAG canónico — campos de paridad con `nexo_contracts.Chunk`
-- =============================================================================

alter table public.sources
  drop constraint if exists sources_status_check;

update public.sources
set status = 'superseded'
where status = 'deprecated';

alter table public.sources
  add constraint sources_status_check
  check (status in ('active', 'expired', 'superseded', 'draft'));

alter table public.sources
  add column if not exists source_key text,
  add column if not exists institution_id text,
  add column if not exists owner text,
  add column if not exists license text,
  add column if not exists verified_at timestamptz,
  add column if not exists is_synthetic boolean not null default true;

alter table public.documents
  add column if not exists document_key text,
  add column if not exists source_key text,
  add column if not exists media_type text,
  add column if not exists original_path text,
  add column if not exists document_version text;

alter table public.chunks
  add column if not exists chunk_key text,
  add column if not exists fragment_key text,
  add column if not exists source_key text,
  add column if not exists document_key text,
  add column if not exists document_version text,
  add column if not exists heading text,
  add column if not exists char_start int,
  add column if not exists char_end int,
  add column if not exists chunk_checksum text,
  add column if not exists source_status text,
  add column if not exists valid_from timestamptz,
  add column if not exists valid_to timestamptz,
  add column if not exists institution_id text,
  add column if not exists embedding_model text,
  add column if not exists embedding_dimension int;

create unique index if not exists sources_tenant_source_key_idx
  on public.sources (tenant_id, source_key)
  where source_key is not null;

create unique index if not exists documents_tenant_document_key_idx
  on public.documents (tenant_id, document_key)
  where document_key is not null;

create unique index if not exists chunks_tenant_chunk_key_idx
  on public.chunks (tenant_id, chunk_key)
  where chunk_key is not null;

create index if not exists idx_chunks_contract_filters
  on public.chunks (tenant_id, institution_id, domain, source_status, source_key);

create or replace function public.match_chunks(
  query_embedding vector(1536),
  match_threshold float default 0.6,
  match_count int default 5,
  filter_domain text default null,
  filter_tenant_id bigint default null,
  filter_valid_at date default current_date,
  filter_status text[] default array['active']::text[],
  allowed_source_ids text[] default null
)
returns table (
  id bigint,
  document_id bigint,
  domain text,
  content text,
  metadata jsonb,
  similarity float,
  source_id text,
  chunk_id text,
  fragment_id text,
  document_version text,
  chunk_checksum text,
  valid_from timestamptz,
  valid_to timestamptz,
  source_status text,
  institution_id text,
  embedding_model text,
  embedding_dimension int
)
language sql stable security definer
set search_path = public
as $$
  select
    c.id,
    c.document_id,
    c.domain,
    c.content,
    c.metadata,
    1 - (c.embedding <=> query_embedding) as similarity,
    coalesce(c.source_key, s.source_key, s.id::text) as source_id,
    coalesce(c.chunk_key, c.id::text) as chunk_id,
    coalesce(c.fragment_key, c.id::text) as fragment_id,
    coalesce(c.document_version, d.document_version, s.version) as document_version,
    coalesce(c.chunk_checksum, c.checksum) as chunk_checksum,
    coalesce(c.valid_from, s.valid_from) as valid_from,
    coalesce(c.valid_to, s.valid_to) as valid_to,
    coalesce(c.source_status, s.status) as source_status,
    coalesce(c.institution_id, s.institution_id, c.tenant_id::text) as institution_id,
    c.embedding_model,
    c.embedding_dimension
  from public.chunks c
  join public.documents d on d.id = c.document_id
  join public.sources s on s.id = d.source_id
  where (filter_tenant_id is null or c.tenant_id = filter_tenant_id)
    and (filter_domain is null or c.domain = filter_domain)
    and coalesce(c.source_status, s.status) = any(filter_status)
    and coalesce(c.valid_from, s.valid_from)::date <= filter_valid_at
    and (
      coalesce(c.valid_to, s.valid_to) is null
      or coalesce(c.valid_to, s.valid_to)::date >= filter_valid_at
    )
    and (
      allowed_source_ids is null
      or coalesce(c.source_key, s.source_key, s.id::text) = any(allowed_source_ids)
    )
    and (1 - (c.embedding <=> query_embedding)) >= match_threshold
  order by c.embedding <=> query_embedding, coalesce(c.fragment_key, c.id::text)
  limit match_count;
$$;
