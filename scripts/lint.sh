#!/usr/bin/env bash
# Verificación de lint del workspace nexo-ai (CI / Unix).
# Uso:  ./scripts/lint.sh
set -euo pipefail

echo "==> ruff format --check"
uv run ruff format --check backend integrations observability scripts

echo "==> ruff check"
uv run ruff check backend integrations observability scripts

echo "==> mypy"
uv run mypy backend/src integrations/src observability/src

echo "Lint OK"
