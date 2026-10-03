from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "PinMe API"
    app_env: str = "local"
    debug: bool = True

    database_url: str = "postgresql+psycopg://pinme:pinme@localhost:5433/pinme"

    s3_endpoint_url: str = "http://localhost:9090"
    s3_access_key: str = "test"
    s3_secret_key: str = "test"
    s3_bucket: str = "pin-me"
    s3_region: str = "us-east-1"

    jwt_secret: str = "change-me-in-production"
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
