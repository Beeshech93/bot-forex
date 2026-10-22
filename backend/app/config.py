"""Validated application settings."""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Smart Signals FX API"
    environment: str = "development"
    api_token: str | None = Field(default=None, repr=False)
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    log_level: str = "INFO"
    mt5_terminal_path: str | None = Field(default=None, repr=False)
    database_url: str = Field(default="sqlite:///./smart_signals_fx.db", repr=False)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator("api_token")
    @classmethod
    def reject_short_tokens(cls, value: str | None) -> str | None:
        if value is not None and len(value) < 32:
            raise ValueError("API_TOKEN must contain at least 32 characters")
        return value

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        normalized = value.upper()
        if normalized not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("LOG_LEVEL must be a standard Python logging level")
        return normalized


@lru_cache
def get_settings() -> Settings:
    """Return cached settings; clear this cache when changing env in tests."""
    return Settings()
