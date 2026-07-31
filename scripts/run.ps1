# Arranque de una línea (Windows). Por defecto: Docker Compose. Con -Mode local: uvicorn.
#   .\scripts\run.ps1               # Docker Compose
#   .\scripts\run.ps1 -Mode local   # uvicorn directo (dev)
param([string]$Mode = "docker")
$ErrorActionPreference = "Stop"

if ($Mode -eq "local") {
    Write-Host "==> Arranque local (uvicorn en :8000)"
    uv sync --all-packages
    python -m uvicorn nexo_api.main:app --reload --port 8000
}
else {
    Write-Host "==> Arranque con Docker Compose"
    docker compose up --build -d api
    Write-Host "==> Esperando health..."
    for ($i = 0; $i -lt 40; $i++) {
        try {
            Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/health/live -TimeoutSec 2 | Out-Null
            Write-Host "API arriba -> http://127.0.0.1:8000  (docs: /docs)"
            exit 0
        }
        catch { Start-Sleep -Seconds 1 }
    }
    Write-Error "La API no respondió a /health/live a tiempo"
    exit 1
}
