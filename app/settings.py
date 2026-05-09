from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_key: str | None = None
    onecms_quote_url: str = "https://www.bhaskar.com/onecms/quote-image-generator"
    onecms_username: str | None = None
    onecms_password: str | None = None
    onecms_storage_state_json: str | None = None
    browser_timeout_ms: int = 45_000


@lru_cache
def get_settings() -> Settings:
    return Settings()
