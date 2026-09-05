"""Application configuration, loaded from the environment (never from flags/code)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    log_level: str = "info"

    # Comma-separated browser origins allowed to call this API (CORS). Auth/RLS still gate
    # identity + tenant; CORS only permits cross-origin browser requests.
    frontend_origins: str = ""

    # Database (control plane only — never given to the AI runtime)
    database_url: str = "postgresql+asyncpg://aegispay_app:aegispay@localhost:5432/aegispay"
    database_migration_url: str = ""

    redis_url: str = "redis://localhost:6379/0"
    sqs_url: str = ""

    # AI Runtime -> Control Plane (isolated service; AI only ever talks via this HTTP API)
    control_plane_url: str = ""
    control_plane_token: str = ""

    # AI Runtime -> Ollama (optional; the AI reasons here but never moves money)
    ollama_url: str = ""
    ollama_model: str = "qwen2.5:0.5b"

    # Razorpay (test keys; secret never leaves the adapter boundary)
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""
    razorpay_base_url: str = "https://api.razorpay.com/v1"

    jwt_secret: str = "change-me"
    oidc_issuer: str = ""

    # Password reset: token TTL (minutes) and whether to reveal the reset token in the API
    # response. With no SMTP provider configured the token is returned (and logged) so a demo
    # can complete the flow; set to true only outside production, never in prod.
    password_reset_ttl_minutes: int = 30
    password_reset_reveal_token: bool = True

    field_enc_key: str = ""

    otel_exporter_otlp_endpoint: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
