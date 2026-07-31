#!/usr/bin/env bash
# Ejecuta la suite de tests del workspace nexo-ai (CI / Unix).
# Uso:  ./scripts/test.sh  [args de pytest, p.ej. -k auth -x]
# Nota: exit 5 de pytest = "sin tests recolectados"; se trata como OK durante
#       la fase bootstrap. Un fallo real (exit 1) sí propaga el error.
set -uo pipefail

echo "==> pytest"
set +e
uv run pytest backend/tests integrations/tests observability/tests "$@"
code=$?
set -e

if [ "$code" -eq 5 ]; then
  echo "pytest: 0 tests recolectados (exit 5) — OK en fase bootstrap"
elif [ "$code" -ne 0 ]; then
  exit "$code"
fi

echo "Tests OK"
