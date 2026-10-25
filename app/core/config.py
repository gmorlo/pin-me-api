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

    jwt_secret: str = "change-me-in-production-use-32chars"
    jwt_expire_hours: int = 24 * 7
    auth_cookie_name: str = "pinme_access"

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"

    # Where Google OAuth sends the browser after login (pin-me-web).
    web_app_origin: str = "http://localhost:3001"

    # If set, ensure this email exists in users (allowlist) on startup.
    allowlist_seed_email: str = ""

    # Local-only: POST /auth/dev-login for allowlisted emails without Google.
    auth_dev_bypass: bool = False

    cors_origins: str = "http://localhost:3000,http://localhost:3001"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def google_oauth_configured(self) -> bool:
        return bool(self.google_client_id and self.google_client_secret)

    @property
    def is_local(self) -> bool:
        return self.app_env.lower() in {"local", "test", "development", "dev"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
