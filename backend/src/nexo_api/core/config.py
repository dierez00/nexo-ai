"""Configuración centralizada de la aplicación vía pydantic-settings.

Fuente única de verdad para variables de entorno. Los módulos importan
`get_settings()` en vez de leer `os.environ` directamente.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Raíz del repo: core/ -> nexo_api -> src -> backend -> <raíz>. Permite cargar el
# .env sin importar el CWD (uvicorn corre desde cualquier carpeta). En contenedor
# el archivo no existe y pydantic-settings usa las variables de entorno reales.
_REPO_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # App
    # ------------------------------------------------------------------
    app_env: Literal["development", "staging", "production"] = "development"
    public_base_url: str = "http://localhost:8000"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # Perfil de orquestación. `fake` usa dobles en proceso (default, sin cargar
    # corpus ni agentes). `real` ensambla el grafo MVP real (tools mock, modelo
    # fake) en el lifespan. Cambiarlo no toca routers ni servicios (§deps).
    orchestrator_profile: Literal["fake", "real"] = "fake"

    # Tenant al que se asocian los ciudadanos anónimos (chat y citas sin token).
    public_tenant_slug: str = "gobierno-demo"

    # Rate limiting in-app (por usuario/tenant) para escrituras/costosas.
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 20

    # ------------------------------------------------------------------
    # Base de datos
    # ------------------------------------------------------------------
    database_url: str = Field(
        default="postgresql+asyncpg://nexo:nexo@localhost:5432/nexo_dev",
        description="URL de conexión a PostgreSQL (asyncpg).",
    )

    # ------------------------------------------------------------------
    # Twilio
    # ------------------------------------------------------------------
    twilio_account_sid: str = ""
    twilio_auth_token: SecretStr = SecretStr("")
    twilio_whatsapp_sender: str = ""
    twilio_webhook_base_url: str = ""

    # ------------------------------------------------------------------
    # Supabase (nuevo sistema de API keys: publishable/secret + JWKS)
    # El backend usa la SECRET key (bypassa RLS); publishable es de frontend.
    # ------------------------------------------------------------------
    supabase_url: str = ""
    supabase_publishable_key: str = ""
    supabase_secret_key: SecretStr = SecretStr("")
    supabase_jwks_url: str = ""
    supabase_jwt_aud: str = "authenticated"

    # ------------------------------------------------------------------
    # Modelos (aliases opcionales; se completan cuando haya proveedor)
    # ------------------------------------------------------------------
    openai_api_key: SecretStr = SecretStr("")
    anthropic_api_key: SecretStr = SecretStr("")
    ollama_base_url: str = "http://localhost:11434"

    # ------------------------------------------------------------------
    # OpenTelemetry (Pro)
    # ------------------------------------------------------------------
    otel_exporter_otlp_endpoint: str = ""

    # Ejecuci\u00f3n local de runs / idempotencia (MVP sin cola externa).
    run_shutdown_grace_seconds: int = Field(default=15, ge=1, le=120)
    sse_poll_interval_ms: int = Field(default=500, ge=100, le=5000)
    sse_keepalive_seconds: int = Field(default=15, ge=1, le=60)
    idempotency_processing_ttl_seconds: int = Field(default=300, ge=30, le=3600)

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def twilio_configured(self) -> bool:
        return bool(self.twilio_account_sid and self.twilio_auth_token.get_secret_value())

    @property
    def supabase_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_secret_key.get_secret_value())


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Devuelve la instancia singleton de Settings (cacheada)."""
    return Settings()
