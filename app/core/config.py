from functools import lru_cache

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_JWT_SECRET = "change-me-in-production-use-32chars"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "PinMe API"
    # Safe by default: a forgotten APP_ENV must not enable local-only behaviour.
    app_env: str = "production"
    debug: bool = False

    database_url: str = "postgresql+psycopg://pinme:pinme@localhost:5433/pinme"

    s3_endpoint_url: str = "http://localhost:9090"
    s3_access_key: str = "test"
    s3_secret_key: str = "test"
    s3_bucket: str = "pin-me"
    s3_region: str = "us-east-1"

    jwt_secret: str = _DEFAULT_JWT_SECRET
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

    @field_validator("database_url")
    @classmethod
    def _use_psycopg3(cls, value: str) -> str:
        # Railway/Heroku give postgres(ql)://, which SQLAlchemy maps to psycopg2 (not installed).
        for prefix in ("postgresql://", "postgres://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value[len(prefix):]
        return value

    @model_validator(mode="after")
    def _refuse_unsafe_production(self) -> "Settings":
        if self.is_local:
            return self
        if self.jwt_secret == _DEFAULT_JWT_SECRET or len(self.jwt_secret) < 32:
            raise ValueError("JWT_SECRET must be a unique value of 32+ chars outside local")
        if self.auth_dev_bypass:
            raise ValueError("AUTH_DEV_BYPASS must be false outside local")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip().rstrip("/")
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    @property
    def google_oauth_configured(self) -> bool:
        return bool(self.google_client_id and self.google_client_secret)

    @property
    def is_local(self) -> bool:
        return self.app_env.lower() in {"local", "test", "development", "dev"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
