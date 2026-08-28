"""Application configuration, loaded from the environment (never from flags/code)."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    log_level: str = "info"

    # Database (control plane only — never given to the AI runtime)
    database_url: str = "postgresql+asyncpg://aegispay_app:aegispay@localhost:5432/aegispay"
    database_migration_url: str = ""

    redis_url: str = "redis://localhost:6379/0"
    sqs_url: str = ""

    # Razorpay (test keys; secret never leaves the adapter boundary)
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""
    razorpay_base_url: str = "https://api.razorpay.com/v1"

    jwt_secret: str = "change-me"
    oidc_issuer: str = ""

    field_enc_key: str = ""

    otel_exporter_otlp_endpoint: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
