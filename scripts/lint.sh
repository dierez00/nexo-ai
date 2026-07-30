#!/usr/bin/env bash
# Verificación de lint del workspace nexo-ai (CI / Unix).
# Uso:  ./scripts/lint.sh
set -euo pipefail

echo "==> ruff format --check"
uv run ruff format --check .

echo "==> ruff check"
uv run ruff check .

echo "==> mypy"
uv run mypy .

echo "Lint OK"
