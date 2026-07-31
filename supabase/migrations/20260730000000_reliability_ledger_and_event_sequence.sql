-- =============================================================================
-- Fiabilidad MVP: ledger compartido de idempotencia y secuencia por run.
-- Migración aditiva para demo/preproducción; no hace backfill de replays.
-- =============================================================================

create table if not exists public.idempotency_records (
  id              bigint primary key generated always as identity,
  tenant_id       bigint      not null references public.tenants (id) on delete cascade,
  operation       text        not null,
  idempotency_key text        not null,
  request_hash    text        not null,
  status          text        not null check (status in ('processing', 'succeeded', 'failed', 'unknown')),
  response_status integer,
  response_body   jsonb,
  resource_id     text,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now(),
  unique (tenant_id, operation, idempotency_key)
);

create index if not exists idx_idempotency_records_processing
  on public.idempotency_records (status, created_at)
  where status = 'processing';

drop trigger if exists set_updated_at on public.idempotency_records;
create trigger set_updated_at before update on public.idempotency_records
  for each row execute procedure public.set_updated_at();

alter table public.idempotency_records enable row level security;
drop policy if exists "idempotency_records: select own" on public.idempotency_records;
create policy "idempotency_records: select own" on public.idempotency_records
  for select to authenticated
  using (tenant_id = (select public.current_tenant_id()));

-- `actions` deja de ser la fuente de exclusión. Permite la misma clave para
-- operaciones distintas, mientras el ledger conserva la clave de request.
do $$
declare
  existing_constraint text;
begin
  select conname into existing_constraint
  from pg_constraint
  where conrelid = 'public.actions'::regclass
    and contype = 'u'
    and conkey = array[
      (select attnum from pg_attribute where attrelid = 'public.actions'::regclass and attname = 'idempotency_key')
    ];
  if existing_constraint is not null then
    execute format('alter table public.actions drop constraint %I', existing_constraint);
  end if;
end $$;

create unique index if not exists actions_tenant_name_key_idx
  on public.actions (tenant_id, action_name, idempotency_key);

-- Fase A: los nuevos eventos se guardan ya con la forma canónica. Las bases
-- demo usadas antes de esta migración pueden contener `node_start`/`node_end`;
-- se normalizan primero para poder activar el contrato sin perder trazabilidad.
alter table public.run_events add column if not exists event_id text;
alter table public.run_events add column if not exists sequence integer;
alter table public.run_events add column if not exists actor_type text;
alter table public.run_events add column if not exists actor_name text;
alter table public.run_events add column if not exists event_status text;
alter table public.run_events add column if not exists duration_ms integer;
alter table public.run_events add column if not exists error jsonb;
alter table public.run_events add column if not exists policy_version text;

with legacy_events as (
  select id, row_number() over (partition by run_id order by created_at, id)::integer as sequence
  from public.run_events
  where sequence is null
)
update public.run_events as event
set
  event_id = coalesce(event.event_id, format('evt_legacy_%s', event.id)),
  sequence = coalesce(event.sequence, legacy_events.sequence),
  event_type = case event.event_type
    when 'node_start' then 'agent.started'
    when 'node_end' then 'agent.completed'
    else event.event_type
  end,
  actor_type = coalesce(event.actor_type, 'agent'),
  actor_name = coalesce(nullif(event.actor_name, ''), nullif(event.node_name, ''), 'legacy'),
  event_status = coalesce(
    event.event_status,
    case event.event_type
      when 'node_start' then 'started'
      else 'succeeded'
    end
  )
from legacy_events
where event.id = legacy_events.id;

-- Una instalación que hubiese añadido las columnas en una ejecución interrumpida
-- puede tener valores nulos fuera del CTE anterior; complételos también.
update public.run_events
set
  event_id = coalesce(event_id, format('evt_legacy_%s', id)),
  actor_type = coalesce(actor_type, 'agent'),
  actor_name = coalesce(nullif(actor_name, ''), nullif(node_name, ''), 'legacy'),
  event_status = coalesce(event_status, 'succeeded');

alter table public.run_events alter column event_id set not null;
alter table public.run_events alter column sequence set not null;
alter table public.run_events alter column actor_type set not null;
alter table public.run_events alter column actor_name set not null;
alter table public.run_events alter column event_status set not null;
alter table public.run_events alter column node_name set default 'canonical';
create unique index if not exists run_events_event_id_idx on public.run_events (event_id);
create unique index if not exists run_events_run_sequence_idx on public.run_events (run_id, sequence);

-- El POST de mensaje reserva primero un run y su worker lo cambia a running.
alter table public.runs drop constraint if exists runs_status_check;

update public.runs
set status = case status
  when 'completed' then 'succeeded'
  when 'requires_action' then 'waiting_confirmation'
  else status
end
where status in ('completed', 'requires_action');

alter table public.runs add constraint runs_status_check
  check (status in ('queued', 'planning', 'running', 'waiting_confirmation', 'succeeded', 'partial', 'failed', 'cancelled'));

-- Una propuesta no es una ejecución: se almacena inmutable antes de mostrarla
-- al cliente y se completa con el ActionResult canónico tras confirmación.
create table if not exists public.pending_actions (
  action_id  text primary key,
  tenant_id  bigint not null references public.tenants (id) on delete cascade,
  run_id     bigint not null references public.runs (id) on delete cascade,
  request    jsonb not null,
  status     text not null check (status in ('pending_confirmation', 'confirmed', 'succeeded', 'failed', 'partial', 'cancelled')),
  result     jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists pending_actions_tenant_run_idx on public.pending_actions (tenant_id, run_id);
alter table public.pending_actions enable row level security;
drop policy if exists "pending_actions: select own" on public.pending_actions;
create policy "pending_actions: select own" on public.pending_actions
  for select to authenticated using (tenant_id = (select public.current_tenant_id()));
drop trigger if exists set_updated_at on public.pending_actions;
create trigger set_updated_at before update on public.pending_actions
  for each row execute procedure public.set_updated_at();
