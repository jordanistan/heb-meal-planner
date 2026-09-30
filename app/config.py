"""Application settings, loaded from environment (12-factor)."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Core
    app_name: str = "HEB Meal Planner"
    environment: str = "development"

    # Database. Defaults to a local SQLite file so tests and local dev need no
    # Postgres; Docker Compose / k8s override this with a Postgres URL.
    database_url: str = "sqlite:///./dev.db"

    # HEB deep links (the v1 "buy" step runs in the user's own browser).
    heb_search_url: str = "https://www.heb.com/search/?q={query}"

    # Optional: Claude plan generation (v1 works fully without it).
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-5"


settings = Settings()
