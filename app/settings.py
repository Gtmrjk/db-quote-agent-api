from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_key: str | None = None
    quote_tool_file: str = "quote_tool/index.html"
    browser_timeout_ms: int = 45_000


@lru_cache
def get_settings() -> Settings:
    return Settings()
