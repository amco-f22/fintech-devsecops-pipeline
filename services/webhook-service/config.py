"""
Application configuration via environment variables (12-factor app).
Supports SQLite for local dev, PostgreSQL for production/K8s.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "SecurePay Webhook Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./webhook.db"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Security
    API_KEY_HEADER: str = "X-API-Key"
    ALLOWED_ORIGINS: list[str] = ["*"]

    # Metrics
    METRICS_ENABLED: bool = True

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — created once per process."""
    return Settings()
