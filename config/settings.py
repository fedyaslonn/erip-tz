from functools import lru_cache

from pydantic_settings import SettingsConfigDict, BaseSettings


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    DB_URL: str


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
