-- =============================================================================
-- SaaS v1.3.0 — Módulo Citas (Appointments) & Control GiST
-- Prevención estricta de empalmes con btree_gist en PostgreSQL y Holds temporales
-- =============================================================================

create extension if not exists btree_gist;

create table if not exists public.appointments (
  id              bigint primary key generated always as identity,
  tenant_id       bigint      not null references public.tenants (id) on delete cascade,
  branch_id       bigint      not null references public.branches (id) on delete cascade,
  user_id         bigint      references public.users (id) on delete set null,
  module_code     text        not null,
  service_name    text        not null,
  time_range      tstzrange   not null,
  status          text        not null default 'hold' check (status in ('hold', 'confirmed', 'canceled', 'expired')),
  hold_expires_at timestamptz default (now() + interval '15 minutes'),
  confirmation_folio text,
  metadata        jsonb       not null default '{}',
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now(),
  
  -- Constraint de exclusión GiST que impide citas solapadas por sucursal y tenant mientras estén activas ('hold' o 'confirmed')
  constraint appointments_no_overlap exclude using gist (
    tenant_id with =,
    branch_id with =,
    time_range with &&
  ) where (status in ('hold', 'confirmed'))
);

-- Índices para búsquedas de disponibilidad
create index if not exists idx_appointments_tenant_branch on public.appointments (tenant_id, branch_id);
create index if not exists idx_appointments_status        on public.appointments (status, hold_expires_at);
create index if not exists idx_appointments_user          on public.appointments (user_id);

-- Trigger updated_at
drop trigger if exists set_updated_at on public.appointments;
create trigger set_updated_at before update on public.appointments for each row execute procedure public.set_updated_at();

-- Función para limpiar automáticamente los holds expirados
create or replace function public.cleanup_expired_holds()
returns int
language plpgsql security definer
set search_path = public
as $$
declare
  v_updated_count int;
begin
  update public.appointments
  set status = 'expired',
      updated_at = now()
  where status = 'hold'
    and hold_expires_at <= now();
  
  get diagnostics v_updated_count = row_count;
  return v_updated_count;
end;
$$;

-- RLS
alter table public.appointments enable row level security;

drop policy if exists "appointments: select own" on public.appointments;
create policy "appointments: select own" on public.appointments for select to authenticated using (tenant_id = (select public.current_tenant_id()));

drop policy if exists "appointments: insert own" on public.appointments;
create policy "appointments: insert own" on public.appointments for insert to authenticated with check (tenant_id = (select public.current_tenant_id()));

drop policy if exists "appointments: update own" on public.appointments;
create policy "appointments: update own" on public.appointments for update to authenticated using (tenant_id = (select public.current_tenant_id())) with check (tenant_id = (select public.current_tenant_id()));
