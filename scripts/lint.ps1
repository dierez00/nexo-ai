# Verificación de lint del workspace nexo-ai (Windows / dev).
# Uso:  .\scripts\lint.ps1
# Corre desde la raíz del repo. Fail-fast: se detiene en el primer error.
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "==> ruff format --check"
uv run ruff format --check backend integrations observability scripts
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> ruff check"
uv run ruff check backend integrations observability scripts
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> mypy"
uv run mypy backend/src integrations/src observability/src
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Lint OK"
