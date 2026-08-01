# Scripts

## Objetivo

Proveer comandos repetibles para arranque, seed, ingesta, evaluación y demo.

## Debe contener

Wrappers pequeños alrededor de CLIs públicas con `--help`, validación y códigos de salida.

## No debe contener

Lógica reusable, secretos ni acciones destructivas sin objetivo/confirmación explícitos.

## Convenciones

Idempotentes, fail-fast, ejecutables desde la raíz y compatibles con CI.

Los scripts deben ser reproducibles, documentar sus entradas y salidas y
mantener separadas las operaciones offline de las que requieren servicios externos.

## Ejemplos y tareas

Dependencias permitidas: CLIs públicas de los módulos y variables documentadas. Ejemplos: `run.sh`, `seed_demo.sh`, `ingest_demo.sh`, `eval.sh`. Implementar arranque de una línea y checks.

## Scripts disponibles

| Script | Qué hace |
|---|---|
| `lint.ps1` / `lint.sh` | ruff format --check + ruff check + mypy |
| `test.ps1` / `test.sh` | pytest (exit 5 = sin tests = OK en bootstrap) |
| `seed_demo.py` | Siembra permisos + role_permissions + usuario demo (Supabase Auth + `public.users`). Idempotente. Credenciales por `SEED_DEMO_EMAIL`/`SEED_DEMO_PASSWORD`. Uso: `uv run python scripts/seed_demo.py` |
| `export_openapi.py` | Exporta el OpenAPI a `contracts/openapi/v1.yaml` (test de drift lo cuida). Uso: `uv run python scripts/export_openapi.py` |
| `run.sh` / `run.ps1` | Arranque de una línea. Docker Compose por defecto; `--local` / `-Mode local` = uvicorn. Espera health e imprime URLs. |

## Terminado

Los scripts documentan precondiciones, no ocultan errores y funcionan en un entorno limpio soportado.
