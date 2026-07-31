# Runbook — Arranque del backend nexo-ai

Guía operativa para levantar, verificar, desplegar y hacer rollback del backend
(API FastAPI). Responsable: Dani. Última fase cubierta: MVP (Partes 0–7).

---

## 1. Requisitos

| Herramienta | Versión | Notas |
|---|---|---|
| Python | 3.12 | `.python-version` lo fija |
| uv | ≥ 0.12 | gestor de paquetes/venv |
| Docker | opcional | solo para Compose |
| Cuenta Supabase | — | DB + Auth (proyecto ya provisionado) |
| Cuenta Twilio | — | WhatsApp Sandbox |

Instalar uv (una vez):
```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# En bash MINGW, agregar al PATH de la sesión:
export PATH="$HOME/.local/bin:$PATH"
```

---

## 2. Configuración (`.env`)

Copiar la plantilla y completar con valores reales (el `.env` NO se versiona):
```bash
cp .env.example .env
```

Variables críticas:

- **`DATABASE_URL`** — usar el **Session pooler** de Supabase (IPv4, puerto 5432).
  El host directo `db.<ref>.supabase.co` es IPv6-only y no resuelve.
  URL-encodear caracteres especiales de la contraseña (`$` → `%24`):
  ```
  postgresql+asyncpg://postgres.<ref>:<pwd>@aws-0-<region>.pooler.supabase.com:5432/postgres
  ```
- **`SUPABASE_URL`, `SUPABASE_SECRET_KEY`** — backend (la secret key bypassa RLS).
- **`SUPABASE_JWKS_URL`** — para validar los JWT de Supabase (auth).
- **`TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_SENDER`**.
- **`PUBLIC_BASE_URL`** — en local con túnel, debe ser **exactamente** la URL pública
  del túnel (sin barra final). Es clave para validar la firma de Twilio.

> ⚠️ **Tras editar `.env`, SIEMPRE reinicia el server.** Las settings se cargan una
> vez al arrancar (`get_settings()` usa `lru_cache`); no se recargan en caliente.

---

## 3. Instalación y datos demo

```bash
uv sync --all-packages          # instala TODAS las deps del workspace
uv run python scripts/seed_demo.py   # permisos + rol admin + usuario demo (idempotente)
```
Usuario demo resultante: `admin@gobierno-demo.mx` / `Demo1234!`.

---

## 4. Arranque local

Desde la **raíz del repo**:
```bash
python -m uvicorn nexo_api.main:app --reload --port 8000
```
(`core/config.py` resuelve el `.env` por ruta absoluta, así que también corre desde
otras carpetas, pero la raíz es lo recomendado.)

Verificar:
```bash
curl http://127.0.0.1:8000/health/live     # {"status":"alive"}
curl http://127.0.0.1:8000/health/ready    # {"status":"ready","checks":{"database":"ok"}}
# Docs interactivos (OpenAPI): http://127.0.0.1:8000/docs
```

---

## 5. Calidad (antes de commitear / en cada iteración)

```bash
bash scripts/lint.sh    # ruff format --check + ruff check + mypy
bash scripts/test.sh    # pytest
```
También hay un subagente `verify-lint-test` para correrlos por iteración.

---

## 6. Smoke funcional (flujo completo)

```bash
BASE=http://127.0.0.1:8000
TOKEN=$(curl -s -X POST $BASE/api/v1/auth/login -H 'Content-Type: application/json' \
  -d '{"email":"admin@gobierno-demo.mx","password":"Demo1234!"}' \
  | python -c "import sys,json;print(json.load(sys.stdin)['tokens']['access_token'])")

# Conversación → mensaje (202) → run
CID=$(curl -s -X POST $BASE/api/v1/conversations -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"channel":"web"}' \
  | python -c "import sys,json;print(json.load(sys.stdin)['conversation_id'])")
curl -s -X POST $BASE/api/v1/conversations/$CID/messages -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"content":"hola"}'

# SSE de eventos:  GET $BASE/api/v1/runs/<run_id>/events  (header o ?access_token=)
# Acción idempotente: POST $BASE/api/v1/actions/<name>/confirm  (header Idempotency-Key)
# Citas: GET /api/v1/appointments/availability ; POST /api/v1/appointments/holds
```

---

## 7. WhatsApp (Twilio Sandbox) en local

1. Exponer el puerto 8000 con un túnel **público** (ngrok o VS Code dev tunnel con
   acceso anónimo). Copiar la URL pública `https://…`.
2. Poner esa URL en `.env` → `PUBLIC_BASE_URL=https://…` (sin barra final) y
   **reiniciar** el server.
3. En la consola de Twilio (WhatsApp Sandbox):
   - **When a message comes in** → `https://…/webhooks/twilio/whatsapp` · **POST**
   - **Status callback URL** → `https://…/webhooks/twilio/status` · **POST**
4. En el teléfono: enviar `join <palabra-del-sandbox>` al número del sandbox.
5. Enviar un mensaje; debe llegar la respuesta del orquestador.

> La seguridad del webhook es la **firma** (`X-Twilio-Signature`), validada contra
> `PUBLIC_BASE_URL + path`. Si `PUBLIC_BASE_URL` no coincide con la URL pública real
> → **403**. El remitente se guarda como `pii_ref` (hash), nunca el teléfono crudo.

---

## 8. Docker / Compose

```bash
docker compose up --build api            # API usa la DB de Supabase (.env)
docker compose --profile local-db up     # + Postgres pgvector local (dev offline)
```
Build directo de la imagen:
```bash
docker build -f infrastructure/docker/Dockerfile -t nexo-api .
```

---

## 9. Despliegue (Railway) y rollback

**Deploy:**
1. Configurar las variables de entorno del §2 en el servicio de Railway
   (NUNCA subir `.env`). `PUBLIC_BASE_URL` = dominio público del servicio.
2. Railway construye con `infrastructure/docker/Dockerfile`.
3. Verificar `/health/ready` tras el deploy (DB alcanzable).

**Rollback:**
1. Railway → Deployments → seleccionar el deployment previo sano → **Redeploy**.
   (o `git revert <commit>` + push si el problema es de código.)
2. Confirmar `/health/ready` verde.
3. Si el problema es de datos/migración: coordinar con Daher (owner de migraciones);
   el backend no aplica migraciones destructivas.

---

## 10. Troubleshooting

| Síntoma | Causa probable | Solución |
|---|---|---|
| `uv: command not found` | uv no en PATH de la shell | `export PATH="$HOME/.local/bin:$PATH"` |
| `ModuleNotFoundError: fastapi` | falta instalar miembros del workspace | `uv sync --all-packages` |
| Falta `JWT_SECRET`/campo requerido | `.env` no cargado (CWD/arranque) | correr desde la raíz o revisar `PUBLIC_BASE_URL` |
| `/health/ready` 503 / `getaddrinfo failed` | host directo de DB (IPv6) | usar el **Session pooler** (5432) |
| Contraseña de DB truncada | `python-dotenv` interpola `$` | URL-encodear `$`→`%24` en `DATABASE_URL` |
| `supabase_configured: False` | falta `SUPABASE_SECRET_KEY` | pegar la secret key completa en `.env` |
| Webhook Twilio → **403 firma** | `PUBLIC_BASE_URL` ≠ URL pública, o server no reiniciado | igualar `PUBLIC_BASE_URL` al túnel y **reiniciar** |
| Túnel devuelve login/anti-phishing | túnel no público | poner el puerto en acceso anónimo/público |
| Cambios en `.env` no aplican | settings cacheadas | **reiniciar** el server |
