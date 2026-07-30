-- =============================================================================
-- SaaS v1.3.0 — Schema
-- Auth: delegado a Supabase Auth (auth.users)
-- Emails: delegado a Supabase Auth (invites vía auth.inviteUserByEmail)
-- Ejecutar antes que seed.sql
-- =============================================================================


-- =============================================================================
-- SECCIÓN 1: CORE MULTI-TENANT
-- =============================================================================

create table public.tenants (
  id          bigint primary key generated always as identity,
  name        text        not null,
  slug        text        not null unique,
  status      text        not null default 'active'
                          check (status in ('active', 'trial', 'suspended', 'canceled')),
  metadata    jsonb       not null default '{}',
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

create table public.tenant_domains (
  id          bigint primary key generated always as identity,
  tenant_id   bigint      not null references public.tenants (id) on delete cascade,
  domain      text        not null unique,
  is_primary  boolean     not null default false,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);


-- =============================================================================
-- SECCIÓN 2: PLANES Y MÓDULOS
-- =============================================================================

create table public.plans (
  id              bigint primary key generated always as identity,
  code            text          not null unique,
  name            text          not null,
  description     text,
  max_users       int,                            -- null = unlimited
  max_modules     int,                            -- null = unlimited
  price_monthly   numeric(10,2) not null default 0,
  price_yearly    numeric(10,2) not null default 0,
  is_default      boolean       not null default false,
  metadata        jsonb         not null default '{}',
  created_at      timestamptz   not null default now(),
  updated_at      timestamptz   not null default now()
);

create table public.modules (
  id              bigint primary key generated always as identity,
  code            text        not null unique,
  name            text        not null,
  description     text,
  is_core         boolean     not null default false,
  config_schema   jsonb       not null default '{}',
  metadata        jsonb       not null default '{}',
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

create table public.plan_modules (
  plan_id       bigint  not null references public.plans   (id) on delete cascade,
  module_id     bigint  not null references public.modules (id) on delete cascade,
  is_required   boolean not null default false,
  primary key (plan_id, module_id)
);


-- =============================================================================
-- SECCIÓN 3: SUSCRIPCIONES
-- =============================================================================

create table public.subscriptions (
  id            bigint primary key generated always as identity,
  tenant_id     bigint      not null references public.tenants (id) on delete cascade,
  plan_id       bigint      not null references public.plans   (id),
  status        text        not null default 'trialing'
                            check (status in ('active', 'trialing', 'canceled', 'past_due', 'unpaid')),
  period_start  timestamptz not null default now(),
  period_end    timestamptz,
  renews_at     timestamptz,
  canceled_at   timestamptz,
  seats         int         not null default 1 check (seats > 0),
  metadata      jsonb       not null default '{}',
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

-- Solo una suscripción activa/trialing por tenant a la vez
create unique index subscriptions_tenant_active_idx
  on public.subscriptions (tenant_id)
  where status in ('active', 'trialing');


-- =============================================================================
-- SECCIÓN 4: MÓDULOS POR TENANT
-- =============================================================================

create table public.tenant_modules (
  id              bigint primary key generated always as identity,
  tenant_id       bigint      not null references public.tenants (id) on delete cascade,
  module_id       bigint      not null references public.modules (id) on delete cascade,
  status          text        not null default 'enabled'
                              check (status in ('enabled', 'disabled', 'pending_config')),
  activated_at    timestamptz not null default now(),
  deactivated_at  timestamptz,
  config          jsonb       not null default '{}',
  metadata        jsonb       not null default '{}',
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now(),
  unique (tenant_id, module_id)
);


-- =============================================================================
-- SECCIÓN 5: RBAC — ROLES Y PERMISOS
-- =============================================================================

create table public.roles (
  id          bigint primary key generated always as identity,
  tenant_id   bigint      references public.tenants (id) on delete cascade, -- null = rol de sistema
  code        text        not null,
  name        text        not null,
  description text,
  is_system   boolean     not null default false,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

-- Roles de sistema: code único global
create unique index roles_system_code_idx
  on public.roles (code)
  where tenant_id is null;

-- Roles de tenant: code único por tenant
create unique index roles_tenant_code_idx
  on public.roles (tenant_id, code)
  where tenant_id is not null;

create table public.permissions (
  id          bigint primary key generated always as identity,
  code        text        not null unique,  -- formato: {module_code}.{action}
  description text,
  module_id   bigint      not null references public.modules (id) on delete cascade,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

create table public.role_permissions (
  role_id       bigint not null references public.roles       (id) on delete cascade,
  permission_id bigint not null references public.permissions (id) on delete cascade,
  primary key (role_id, permission_id)
);


-- =============================================================================
-- SECCIÓN 6: SUCURSALES
-- =============================================================================

create table public.branches (
  id          bigint primary key generated always as identity,
  tenant_id   bigint      not null references public.tenants (id) on delete cascade,
  code        text        not null,
  name        text        not null,
  address     text,
  status      text        not null default 'active'
                          check (status in ('active', 'inactive')),
  metadata    jsonb       not null default '{}',
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now(),
  unique (tenant_id, code)
);


-- =============================================================================
-- SECCIÓN 7: USUARIOS
-- Referencia auth.users de Supabase. El perfil de negocio vive aquí.
-- =============================================================================

create table public.users (
  id            bigint primary key generated always as identity,
  auth_user_id  uuid        not null unique references auth.users (id) on delete cascade,
  tenant_id     bigint      not null references public.tenants  (id) on delete cascade,
  branch_id     bigint      references public.branches (id) on delete set null,
  role_id       bigint      not null references public.roles    (id),
  email         text        not null,
  name          text        not null,
  status        text        not null default 'active'
                            check (status in ('active', 'invited', 'suspended')),
  is_owner      boolean     not null default false,
  last_login_at timestamptz,
  metadata      jsonb       not null default '{}',
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now(),
  unique (tenant_id, email)
);

-- Función helper: obtiene el public.users.id del usuario autenticado actual
create or replace function public.current_user_id()
returns bigint
language sql stable security definer
set search_path = public
as $$
  select id from public.users where auth_user_id = auth.uid()
$$;

-- Función helper: obtiene el tenant_id del usuario autenticado actual
create or replace function public.current_tenant_id()
returns bigint
language sql stable security definer
set search_path = public
as $$
  select tenant_id from public.users where auth_user_id = auth.uid()
$$;

-- Función helper: verifica si el usuario actual tiene un permiso específico
create or replace function public.has_permission(permission_code text)
returns boolean
language sql stable security definer
set search_path = public
as $$
  select exists (
    select 1
    from public.users u
    join public.role_permissions rp on rp.role_id = u.role_id
    join public.permissions p       on p.id = rp.permission_id
    where u.auth_user_id = auth.uid()
      and p.code = permission_code
  )
$$;

-- Trigger: sincroniza last_login_at cuando Supabase Auth actualiza el usuario
create or replace function public.handle_auth_user_updated()
returns trigger
language plpgsql security definer
set search_path = public
as $$
begin
  update public.users
  set last_login_at = now(),
      updated_at    = now()
  where auth_user_id = new.id
    and new.last_sign_in_at is distinct from old.last_sign_in_at;
  return new;
end;
$$;

create trigger on_auth_user_updated
  after update on auth.users
  for each row execute procedure public.handle_auth_user_updated();


-- =============================================================================
-- SECCIÓN 8: INVITACIONES
-- Supabase Auth maneja el envío del email (auth.inviteUserByEmail).
-- Esta tabla registra metadata de la invitación y el rol asignado.
-- Flujo: crear fila aquí → llamar auth.inviteUserByEmail desde backend →
--        al aceptar, el trigger on_auth_user_created crea el public.users.
-- =============================================================================

create table public.invites (
  id          bigint primary key generated always as identity,
  tenant_id   bigint      not null references public.tenants  (id) on delete cascade,
  email       text        not null,
  role_id     bigint      not null references public.roles    (id),
  branch_id   bigint      references public.branches (id) on delete set null,
  token       text        not null unique default gen_random_uuid()::text,
  expires_at  timestamptz not null default now() + interval '7 days',
  accepted_at timestamptz,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

-- Trigger: cuando un usuario acepta la invitación de Supabase Auth,
-- busca su invite pendiente y crea el registro en public.users
create or replace function public.handle_auth_user_created()
returns trigger
language plpgsql security definer
set search_path = public
as $$
declare
  v_invite public.invites%rowtype;
begin
  -- Buscar invitación pendiente para este email
  select * into v_invite
  from public.invites
  where email       = new.email
    and accepted_at is null
    and expires_at  > now()
  order by created_at desc
  limit 1;

  if v_invite.id is not null then
    -- Marcar invitación como aceptada
    update public.invites
    set accepted_at = now(),
        updated_at  = now()
    where id = v_invite.id;

    -- Crear perfil de usuario
    insert into public.users (auth_user_id, tenant_id, branch_id, role_id, email, name, status)
    values (
      new.id,
      v_invite.tenant_id,
      v_invite.branch_id,
      v_invite.role_id,
      new.email,
      coalesce(new.raw_user_meta_data->>'full_name', new.email),
      'active'
    );
  end if;

  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_auth_user_created();


-- =============================================================================
-- SECCIÓN 9: AUDITORÍA Y ARCHIVOS
-- =============================================================================

create table public.audit_logs (
  id          bigint primary key generated always as identity,
  tenant_id   bigint      not null references public.tenants (id) on delete cascade,
  user_id     bigint      references public.users (id) on delete set null,
  module_code text        not null,
  entity      text        not null,
  entity_id   text        not null,
  action      text        not null check (action in ('create', 'update', 'delete', 'login', 'other')),
  data_before jsonb,
  data_after  jsonb,
  metadata    jsonb       not null default '{}',
  created_at  timestamptz not null default now()
);

create table public.files (
  id                bigint primary key generated always as identity,
  tenant_id         bigint      not null references public.tenants (id) on delete cascade,
  uploader_id       bigint      references public.users (id) on delete set null,
  storage_provider  text        not null default 'supabase',
  path              text        not null,
  original_name     text        not null,
  mime_type         text        not null,
  type              text,
  category          text,
  size              bigint      not null check (size >= 0),
  hash              text,
  metadata          jsonb       not null default '{}',
  created_at        timestamptz not null default now()
);


-- =============================================================================
-- SECCIÓN 10: FACTURACIÓN
-- tenant_id eliminado — siempre derivado de subscription_id
-- =============================================================================

create table public.invoices (
  id              bigint primary key generated always as identity,
  subscription_id bigint        not null references public.subscriptions (id) on delete restrict,
  status          text          not null default 'draft'
                                check (status in ('draft', 'pending', 'paid', 'canceled')),
  amount          numeric(10,2) not null check (amount >= 0),
  issued_at       timestamptz,
  paid_at         timestamptz,
  metadata        jsonb         not null default '{}',
  created_at      timestamptz   not null default now(),
  updated_at      timestamptz   not null default now()
);

create table public.payments (
  id              bigint primary key generated always as identity,
  invoice_id      bigint        not null references public.invoices (id) on delete restrict,
  provider        text          not null,
  transaction_id  text          not null unique,
  amount          numeric(10,2) not null check (amount > 0),
  status          text          not null check (status in ('pending', 'succeeded', 'failed', 'refunded')),
  processed_at    timestamptz,
  metadata        jsonb         not null default '{}',
  created_at      timestamptz   not null default now(),
  updated_at      timestamptz   not null default now()
);


-- =============================================================================
-- SECCIÓN 11: ÍNDICES DE PERFORMANCE
-- =============================================================================

create index on public.tenant_domains   (tenant_id);
create index on public.subscriptions    (tenant_id);
create index on public.subscriptions    (plan_id);
create index on public.tenant_modules   (tenant_id);
create index on public.tenant_modules   (module_id);
create index on public.users            (tenant_id);
create index on public.users            (auth_user_id);
create index on public.users            (role_id);
create index on public.users            (branch_id);
create index on public.branches         (tenant_id);
create index on public.roles            (tenant_id);
create index on public.role_permissions (role_id);
create index on public.role_permissions (permission_id);
create index on public.permissions      (module_id);
create index on public.audit_logs       (tenant_id, created_at desc);
create index on public.audit_logs       (user_id);
create index on public.files            (tenant_id, created_at desc);
create index on public.files            (uploader_id);
create index on public.invoices         (subscription_id);
create index on public.payments         (invoice_id);
create index on public.invites          (tenant_id);
create index on public.invites          (email, accepted_at) where accepted_at is null;


-- =============================================================================
-- SECCIÓN 12: TRIGGERS updated_at AUTOMÁTICOS
-- =============================================================================

create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger set_updated_at before update on public.tenants
  for each row execute procedure public.set_updated_at();
create trigger set_updated_at before update on public.tenant_domains
  for each row execute procedure public.set_updated_at();
create trigger set_updated_at before update on public.plans
  for each row execute procedure public.set_updated_at();
create trigger set_updated_at before update on public.modules
  for each row execute procedure public.set_updated_at();
create trigger set_updated_at before update on public.subscriptions
  for each row execute procedure public.set_updated_at();
create trigger set_updated_at before update on public.tenant_modules
  for each row execute procedure public.set_updated_at();
create trigger set_updated_at before update on public.roles
  for each row execute procedure public.set_updated_at();
create trigger set_updated_at before update on public.permissions
  for each row execute procedure public.set_updated_at();
create trigger set_updated_at before update on public.users
  for each row execute procedure public.set_updated_at();
create trigger set_updated_at before update on public.branches
  for each row execute procedure public.set_updated_at();
create trigger set_updated_at before update on public.invoices
  for each row execute procedure public.set_updated_at();
create trigger set_updated_at before update on public.payments
  for each row execute procedure public.set_updated_at();
create trigger set_updated_at before update on public.invites
  for each row execute procedure public.set_updated_at();


-- =============================================================================
-- SECCIÓN 13: ROW LEVEL SECURITY (RLS)
-- Patrón base: cada usuario solo ve datos de su propio tenant.
-- Las funciones helper (current_tenant_id, has_permission) se usan en políticas
-- complejas desde el backend con service_role cuando se necesita bypass.
-- =============================================================================

alter table public.tenants          enable row level security;
alter table public.tenant_domains   enable row level security;
alter table public.plans            enable row level security;
alter table public.modules          enable row level security;
alter table public.plan_modules     enable row level security;
alter table public.subscriptions    enable row level security;
alter table public.tenant_modules   enable row level security;
alter table public.roles            enable row level security;
alter table public.permissions      enable row level security;
alter table public.role_permissions enable row level security;
alter table public.users            enable row level security;
alter table public.branches         enable row level security;
alter table public.audit_logs       enable row level security;
alter table public.files            enable row level security;
alter table public.invoices         enable row level security;
alter table public.payments         enable row level security;
alter table public.invites          enable row level security;

-- tenants: un usuario solo ve su propio tenant
create policy "tenant: select own"
  on public.tenants for select to authenticated
  using (id = (select public.current_tenant_id()));

-- tenant_domains
create policy "tenant_domains: select own"
  on public.tenant_domains for select to authenticated
  using (tenant_id = (select public.current_tenant_id()));

-- plans: catálogo público
create policy "plans: select all"
  on public.plans for select to authenticated
  using (true);

-- modules: catálogo público
create policy "modules: select all"
  on public.modules for select to authenticated
  using (true);

-- plan_modules: catálogo público
create policy "plan_modules: select all"
  on public.plan_modules for select to authenticated
  using (true);

-- subscriptions: solo las del propio tenant
create policy "subscriptions: select own"
  on public.subscriptions for select to authenticated
  using (tenant_id = (select public.current_tenant_id()));

-- tenant_modules: solo las del propio tenant
create policy "tenant_modules: select own"
  on public.tenant_modules for select to authenticated
  using (tenant_id = (select public.current_tenant_id()));

-- roles: ver roles de sistema (tenant_id null) y los del propio tenant
create policy "roles: select own and system"
  on public.roles for select to authenticated
  using (
    tenant_id is null
    or tenant_id = (select public.current_tenant_id())
  );

-- permissions: catálogo público
create policy "permissions: select all"
  on public.permissions for select to authenticated
  using (true);

-- role_permissions: catálogo público
create policy "role_permissions: select all"
  on public.role_permissions for select to authenticated
  using (true);

-- users: solo usuarios del mismo tenant
create policy "users: select own tenant"
  on public.users for select to authenticated
  using (tenant_id = (select public.current_tenant_id()));

-- users: cada usuario puede actualizar su propio perfil
create policy "users: update own profile"
  on public.users for update to authenticated
  using     (auth_user_id = auth.uid())
  with check (auth_user_id = auth.uid());

-- branches: solo las del propio tenant
create policy "branches: select own"
  on public.branches for select to authenticated
  using (tenant_id = (select public.current_tenant_id()));

-- audit_logs: select y insert del propio tenant
create policy "audit_logs: select own"
  on public.audit_logs for select to authenticated
  using (tenant_id = (select public.current_tenant_id()));

create policy "audit_logs: insert own"
  on public.audit_logs for insert to authenticated
  with check (tenant_id = (select public.current_tenant_id()));

-- files: solo los del propio tenant
create policy "files: select own"
  on public.files for select to authenticated
  using (tenant_id = (select public.current_tenant_id()));

create policy "files: insert own"
  on public.files for insert to authenticated
  with check (tenant_id = (select public.current_tenant_id()));

-- invoices: derivar tenant desde subscription
create policy "invoices: select own"
  on public.invoices for select to authenticated
  using (
    exists (
      select 1 from public.subscriptions s
      where s.id = subscription_id
        and s.tenant_id = (select public.current_tenant_id())
    )
  );

-- payments: derivar tenant desde invoice → subscription
create policy "payments: select own"
  on public.payments for select to authenticated
  using (
    exists (
      select 1
      from public.invoices i
      join public.subscriptions s on s.id = i.subscription_id
      where i.id = invoice_id
        and s.tenant_id = (select public.current_tenant_id())
    )
  );

-- invites: solo las del propio tenant
create policy "invites: select own"
  on public.invites for select to authenticated
  using (tenant_id = (select public.current_tenant_id()));
