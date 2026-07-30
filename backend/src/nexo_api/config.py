"""Configuración centralizada de la aplicación vía pydantic-settings.

Fuente única de verdad para variables de entorno. Los módulos importan
`get_settings()` en vez de leer `os.environ` directamente.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
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

    # ------------------------------------------------------------------
    # Base de datos
    # ------------------------------------------------------------------
    database_url: str = Field(
        default="postgresql+asyncpg://nexo:nexo@localhost:5432/nexo_dev",
        description="URL de conexión a PostgreSQL (asyncpg).",
    )

    # ------------------------------------------------------------------
    # Auth — JWT bearer
    # ------------------------------------------------------------------
    jwt_secret: SecretStr = Field(
        default=...,
        description="Secreto HMAC (HS256) o clave privada PEM (RS256).",
    )
    jwt_alg: str = "HS256"
    jwt_access_ttl_seconds: int = 900
    jwt_refresh_ttl_seconds: int = 604800

    # ------------------------------------------------------------------
    # Twilio
    # ------------------------------------------------------------------
    twilio_account_sid: str = ""
    twilio_auth_token: SecretStr = SecretStr("")
    twilio_whatsapp_sender: str = ""
    twilio_webhook_base_url: str = ""

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

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def twilio_configured(self) -> bool:
        return bool(self.twilio_account_sid and self.twilio_auth_token.get_secret_value())


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Devuelve la instancia singleton de Settings (cacheada)."""
    return Settings()
