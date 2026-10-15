from pathlib import Path

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/retail_demand"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "retail_demand"
    postgres_user: str = "postgres"
    postgres_password: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")


settings = Settings()


def load_project_settings(path: str | Path = "config/settings.yaml") -> dict:
    """Load shared non-secret application settings from YAML."""
    with Path(path).open(encoding="utf-8") as stream:
        return yaml.safe_load(stream) or {}


def database_url() -> str:
    """Return DATABASE_URL when set, otherwise compose it from environment fields."""
    if settings.database_url:
        return settings.database_url
    return f"postgresql://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
