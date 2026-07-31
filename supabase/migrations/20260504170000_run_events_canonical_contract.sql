-- =============================================================================
-- Run events canónicos — expand para `nexo_contracts.RunEvent`
-- =============================================================================

alter table public.run_events
  add column if not exists event_id text,
  add column if not exists sequence int,
  add column if not exists actor_type text,
  add column if not exists actor_name text,
  add column if not exists status text,
  add column if not exists visibility text,
  add column if not exists correlation_id text,
  add column if not exists parent_event_id text,
  add column if not exists duration_ms int,
  add column if not exists public_data jsonb,
  add column if not exists error jsonb,
  add column if not exists policy_version text,
  add column if not exists catalog_version text,
  add column if not exists skill_id text,
  add column if not exists skill_version text,
  add column if not exists canonical_event jsonb;

update public.run_events
set
  event_type = case event_type
    when 'node_start' then 'agent.started'
    when 'node_end' then 'agent.completed'
    when 'rag_retrieval' then 'rag.completed'
    when 'mcp_call' then 'tool.completed'
    when 'error' then 'agent.failed'
    else event_type
  end,
  event_id = coalesce(event_id, 'evt_' || id::text),
  sequence = coalesce(sequence, id::int),
  actor_type = coalesce(actor_type, 'system'),
  actor_name = coalesce(actor_name, node_name),
  status = coalesce(status, 'succeeded'),
  visibility = coalesce(visibility, 'public'),
  correlation_id = coalesce(correlation_id, trace_id),
  public_data = coalesce(public_data, payload)
where event_id is null
   or sequence is null
   or actor_type is null
   or actor_name is null
   or status is null
   or visibility is null
   or correlation_id is null
   or public_data is null;

create unique index if not exists run_events_run_sequence_idx
  on public.run_events (run_id, sequence)
  where sequence is not null;

create unique index if not exists run_events_run_event_id_idx
  on public.run_events (run_id, event_id)
  where event_id is not null;

create index if not exists idx_run_events_run_sequence
  on public.run_events (run_id, sequence);
