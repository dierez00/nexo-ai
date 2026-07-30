-- =============================================================================
-- SaaS v1.3.0 — Seeds de Demostración (Vehículos y Apertura de Empresas)
-- =============================================================================

insert into public.tenants (name, slug, status)
values ('Gobierno del Estado (Demo)', 'gobierno-demo', 'active')
on conflict (slug) do update set name = excluded.name;

insert into public.plans (code, name, description, max_users, max_modules, is_default)
values ('enterprise', 'Plan Institucional Enterprise', 'Acceso a los 5 dominios y capacidades MCP', null, null, true)
on conflict (code) do update set name = excluded.name;

insert into public.modules (code, name, description, is_core)
values 
  ('vehiculos', 'Control Vehicular', 'Renovación de licencias, adeudos y citas de trámite', true),
  ('ayuntamiento_empresas', 'Apertura de Empresas', 'Licencias de funcionamiento y permiso de suelo', true),
  ('registro_civil', 'Registro Civil', 'Actas de nacimiento, matrimonio y aclaraciones', false),
  ('salud', 'Servicios de Salud', 'Ubicación de unidades de salud y orientación', false),
  ('ganaderia', 'Gestión Ganadera', 'Movilización y registros sanitarios', false)
on conflict (code) do update set name = excluded.name;
