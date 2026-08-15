"""
Application settings and environment configuration.

Uses Pydantic v2's BaseSettings to load configuration from environment
variables and .env files. Provides a single source of truth for all
application-level configuration values.
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.

    Values are read from .env files or the process environment.
    All fields have sensible defaults for local development.
    """

    # ── General ────────────────────────────────────────────────────────────
    APP_NAME: str = "InsightIQ"
    APP_VERSION: str = "0.1.0"
    APP_DESCRIPTION: str = (
        "Enterprise Customer Intelligence Platform"
    )
    APP_ENV: str = "development"  # development | staging | production
    APP_DEBUG: bool = True
    APP_LOG_LEVEL: str = "INFO"

    # ── API / Uvicorn ──────────────────────────────────────────────────────
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4
    API_RELOAD: bool = True
    API_PREFIX: str = "/api/v1"
    API_DOCS_URL: str = "/docs"
    API_REDOC_URL: str = "/redoc"
    API_OPENAPI_URL: str = "/openapi.json"

    # ── Database (PostgreSQL) ──────────────────────────────────────────────
    DATABASE_URL: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/insightiq"
    )
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_ECHO: bool = False
    DATABASE_POOL_PRE_PING: bool = True
    DATABASE_POOL_RECYCLE: int = 3600  # seconds

    # ── CORS ───────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # ── Trusted Hosts ──────────────────────────────────────────────────────
    TRUSTED_HOSTS: list[str] = ["*"]

    # ── JWT / Authentication ───────────────────────────────────────────────
    JWT_SECRET_KEY: str = "change-me-to-a-secure-random-string-at-least-32-chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ISSUER: str = "insightiq"

    # ── Password Security ──────────────────────────────────────────────────
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    PASSWORD_HISTORY_LIMIT: int = 5
    PASSWORD_EXPIRATION_DAYS: int = 90
    PASSWORD_HASH_ALGORITHM: str = "bcrypt"  # bcrypt or argon2

    # ── Token Expiration ───────────────────────────────────────────────────
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 48
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 1
    INVITATION_TOKEN_EXPIRE_DAYS: int = 7

    # ── Account Lockout ────────────────────────────────────────────────────
    ACCOUNT_LOCKOUT_THRESHOLD: int = 5
    ACCOUNT_LOCKOUT_MINUTES: int = 15

    # ── Rate Limiting ──────────────────────────────────────────────────────
    RATE_LIMIT_LOGIN_PER_MINUTE: int = 10
    RATE_LIMIT_REGISTER_PER_HOUR: int = 3
    RATE_LIMIT_RESET_PASSWORD_PER_HOUR: int = 3

    # ── Email (SMTP) ───────────────────────────────────────────────────────
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@insightiq.example.com"
    SMTP_FROM_NAME: str = "InsightIQ"
    SMTP_USE_TLS: bool = False
    SMTP_USE_SSL: bool = False

    # ── Frontend URLs (for email links) ────────────────────────────────────
    FRONTEND_URL: str = "http://localhost:5173"
    FRONTEND_VERIFY_EMAIL_PATH: str = "/verify-email"
    FRONTEND_RESET_PASSWORD_PATH: str = "/reset-password"
    FRONTEND_ACCEPT_INVITATION_PATH: str = "/accept-invitation"

    # ── Paths ──────────────────────────────────────────────────────────────
    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent.parent
    LOG_DIR: Path = PROJECT_ROOT / "logs"
    ARTIFACT_STORAGE_PATH: str = "artifacts/models"

    # ── Pydantic model configuration ───────────────────────────────────────
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


# Module-level singleton for easy import
settings = Settings()