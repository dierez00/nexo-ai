# Desarrollo local

## Requisitos

- Python 3.12
- `uv >= 0.12`
- Node.js/npm para `apps/web`
- Docker y Docker Compose para PostgreSQL local

## Núcleo Python

Desde la raíz del repositorio:

```bash
uv sync --all-packages --frozen
uv run pytest
```

Para ejecutar una suite concreta:

```bash
uv run pytest agents/tests rag/tests orchestration/tests
uv run pytest tests/e2e
```

## API

```bash
uv run uvicorn nexo_api.main:app --reload --port 8000
```

La API expone `/health/live` y `/health/ready`. Las variables se configuran a
partir de `.env.example`; nunca se deben versionar credenciales reales.

## Colección Postman

La colección [`Nexo IA API.postman_collection.json`](../../postman/Nexo%20IA%20API.postman_collection.json)
contiene solicitudes para healthchecks, autenticación, conversaciones, runs,
acciones, citas, voz y webhooks. Importa el archivo en Postman y configura las
variables de colección antes de probar endpoints protegidos.

## Aplicación web

```bash
cd apps/web
npm install
cp .env.example .env.local
npm run dev
```

Variables mínimas:

```dotenv
NEXT_PUBLIC_NEXO_API_URL=http://localhost:8000
NEXT_PUBLIC_ELEVENLABS_AGENT_ID=
```

La aplicación queda disponible normalmente en `http://localhost:3000`.

## Base de datos local

```bash
docker compose --profile local-db up -d
```

Aplica las migraciones y seeds documentados en [`database/`](../../database/)
y [`supabase/`](../../supabase/). Los tests de integración se omiten por
defecto y requieren una base de datos explícita.

## Artefactos derivados

Después de modificar modelos de `contracts`, regenera sus esquemas:

```bash
uv run python -m nexo_contracts.export
```

Antes de abrir una contribución, ejecuta `scripts/lint.sh` y las pruebas del
paquete afectado.
