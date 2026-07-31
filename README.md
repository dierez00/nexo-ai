# Nexo IA

## Objetivo

Hub omnicanal de asistentes e integración institucional. El repositorio contiene
un núcleo de contratos/orquestación de las Fases 0 y 1, ejecutable offline, y
una API FastAPI MVP con auth, conversaciones, citas, acciones idempotentes,
webhooks Twilio y SSE. Las aplicaciones web e integraciones externas avanzan
en módulos separados.

## Documentos principales

- [`Nexo_IA_Propuesta_Completa.md`](./Nexo_IA_Propuesta_Completa.md): problema, alcance y rúbrica.
- [`Nexo_IA_Arquitectura_y_Plan.md`](./Nexo_IA_Arquitectura_y_Plan.md): arquitectura, contratos, fases, pruebas y despliegue.
- [`docs/team/`](./docs/team/): división de trabajo para Cris, Dani, Daher y Diego.

## Alcance acordado

- MVP: vehículos y apertura de empresas de extremo a extremo, con transacciones mock, WhatsApp Twilio Sandbox y una sola app web con `/portal` y `/admin`.
- Core: cinco dominios, workflow, dashboard y catálogo.
- Pro: voz, MCP Mapper, model router y A2UI dinámico.
- Extremo: paralelismo, mini-RAGs, LLM-as-judge y personalización avanzada.

## Estado de ejecución

Implementado: `docker compose up --build api`, healthchecks, CI, logging JSONL,
OpenAPI, runbook, login proxy Supabase Auth, JWT por JWKS y chat web con SSE
autenticado. El streaming SSE del MVP se ejecuta en proceso; un reinicio cancela
runs activos. Worker/cola durable y adapters institucionales reales siguen
pendientes.

### Setup Supabase cloud

1. Aplica todas las migraciones en `supabase/migrations/` al proyecto cloud.
2. En Supabase Dashboard → Project Settings → API, copia:
   - Project URL → `SUPABASE_URL` y `NEXT_PUBLIC_SUPABASE_URL`.
   - Publishable key → `SUPABASE_PUBLISHABLE_KEY`.
   - Secret key → `SUPABASE_SECRET_KEY` solo en backend.
3. Define `SUPABASE_JWKS_URL=https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json`.
4. En Project Settings → Database → Connect, copia el connection string. Para el
   backend persistente usa direct connection si tu entorno soporta IPv6; si no,
   usa session pooler. Adáptalo a SQLAlchemy async:
   `postgresql+asyncpg://usuario:password@host:puerto/postgres`.
5. En el backend local configura `WEB_ORIGIN=http://localhost:3000` y en
   `apps/web/.env.local` configura `NEXT_PUBLIC_NEXO_API_URL=http://localhost:8000`.
6. Antes de invitar un usuario, crea el invite de negocio para que el trigger
   genere `public.users` cuando acepte la invitación:

```sql
insert into public.invites (tenant_id, email, role_id, branch_id)
select t.id, 'TU_EMAIL_ADMIN', r.id, b.id
from public.tenants t
join public.roles r on r.code = 'admin' and r.tenant_id is null
left join public.branches b on b.tenant_id = t.id and b.code = 'MOD-CENTRO'
where t.slug = 'gobierno-demo';
```

7. En Authentication → Users → Add user → Send invitation, invita ese email,
   acepta el enlace, define contraseña y entra en `/login`.

### Núcleo Python (Fases 0 y 1 — `implementadas`)

Existe un workspace Python con contratos tipados, puertos, dobles de prueba,
configuración validada y un grafo mínimo verificable. Corre **sin red, sin base
de datos y sin credenciales**.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e ./contracts -e ./rag -e ./mcp \
  -e ./orchestration -e ./agents -e ./a2ui
.venv/bin/python -m pip install pytest pytest-asyncio ruff
uv sync --all-packages --frozen
uv run pytest
```

Regenerar los artefactos derivados de `contracts/` tras cambiar un modelo:

```sh
.venv/bin/python -m nexo_contracts.export
```

Alcance actual: contratos versionados, corpus y retrieval híbrido, agentes
cerrados, server/tools MCP mock, grafo MVP reanudable con confirmación,
estimación determinista y A2UI ciudadano con fallback. Los recorridos
`CAP-VEH-01` y `CAP-EMP-01` se prueban de extremo a extremo sin credenciales.
Ver [`docs/team/fase1_hallazgos.md`](./docs/team/fase1_hallazgos.md).

## Convenciones

- Marcar capacidades como `planeada`, `mock` o `implementada`.
- No versionar secretos ni PII real.
- Cambiar contratos mediante revisión conjunta.
- Mantener documentación y estado real sincronizados.

## Dependencias, ejemplos y tareas

La raíz coordina el workspace Python. Requiere `uv >= 0.12`; en PowerShell usa
`./scripts/lint.ps1` y `./scripts/test.ps1`. `docker-compose.yml` y
`.env.example` están materializados; `run.sh` sigue pendiente.

Responsable de instalación futura: Dani. Todo el equipo valida alcance y demo. La raíz se considera terminada cuando una persona nueva puede comprender y ejecutar el proyecto sin ayuda.

## Skill de frontend

Usa `$build-a2ui-frontend` para interfaces y futuros catálogos compatibles con
A2UI v0.9.1. `citizen:v1` está congelado: cualquier evolución funcional publica
`citizen:v2`. La skill versionada está en
`.agents/skills/build-a2ui-frontend`.
