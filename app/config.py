"""Application settings, loaded from environment variables."""
import secrets
from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite+pysqlite:///./dev.db"
    # Comma-separated list of accepted API keys for write endpoints.
    # If unset, a random undisclosed key is generated so auth is never disabled (writes stay locked).
    api_keys: str = ""
    log_level: str = "INFO"
    api_key_generated: bool = False

    @model_validator(mode="after")
    def _ensure_api_key(self) -> "Settings":
        if not self.api_key_set:
            self.api_keys = secrets.token_urlsafe(24)
            self.api_key_generated = True
        return self

    @property
    def api_key_set(self) -> set[str]:
        return {k.strip() for k in self.api_keys.split(",") if k.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
