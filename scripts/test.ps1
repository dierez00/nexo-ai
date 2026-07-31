# Ejecuta la suite de tests del workspace nexo-ai (Windows / dev).
# Uso:  .\scripts\test.ps1  [args de pytest, p.ej. -k auth -x]
# Nota: exit 5 de pytest = "sin tests recolectados"; se trata como OK durante
#       la fase bootstrap. Un fallo real (exit 1) sí propaga el error.
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "==> pytest"
uv run pytest backend/tests integrations/tests observability/tests @args
$code = $LASTEXITCODE

if ($code -eq 5) {
    Write-Host "pytest: 0 tests recolectados (exit 5) — OK en fase bootstrap"
} elseif ($code -ne 0) {
    exit $code
}

Write-Host "Tests OK"
