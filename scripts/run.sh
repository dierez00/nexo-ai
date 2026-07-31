#!/usr/bin/env bash
# Arranque de una línea. Por defecto: Docker Compose. Con --local: uvicorn.
#   ./scripts/run.sh            # Docker Compose (usa la DB de .env)
#   ./scripts/run.sh --local    # uvicorn directo (dev)
set -euo pipefail

MODE="${1:-docker}"

case "$MODE" in
  --local | local)
    echo "==> Arranque local (uvicorn en :8000)"
    uv sync --all-packages
    exec python -m uvicorn nexo_api.main:app --reload --port 8000
    ;;
  *)
    echo "==> Arranque con Docker Compose"
    docker compose up --build -d api
    echo "==> Esperando health..."
    for _ in $(seq 1 40); do
      if curl -sf http://127.0.0.1:8000/health/live >/dev/null 2>&1; then
        echo "API arriba -> http://127.0.0.1:8000  (docs: /docs)"
        exit 0
      fi
      sleep 1
    done
    echo "La API no respondió a /health/live a tiempo" >&2
    exit 1
    ;;
esac
