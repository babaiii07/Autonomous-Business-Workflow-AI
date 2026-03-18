from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Core
    env: Literal["dev", "test", "prod"] = Field(default="dev", alias="ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # LLM (Groq)
    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", alias="GROQ_MODEL")

    # Tavily
    tavily_api_key: str | None = Field(default=None, alias="TAVILY_API_KEY")

    # Pinecone
    pinecone_api_key: str | None = Field(default=None, alias="PINECONE_API_KEY")
    pinecone_index: str = Field(default="ai-coo-memory", alias="PINECONE_INDEX")
    pinecone_namespace: str = Field(default="default", alias="PINECONE_NAMESPACE")

    # Database
    db_url: str = Field(default="sqlite:///./data/app.db", alias="DB_URL")

    # Business rules
    high_value_threshold: float = Field(default=5000.0, alias="HIGH_VALUE_THRESHOLD")

    # Email
    email_mode: Literal["mock", "imap"] = Field(default="mock", alias="EMAIL_MODE")
    imap_host: str | None = Field(default=None, alias="IMAP_HOST")
    imap_user: str | None = Field(default=None, alias="IMAP_USER")
    imap_password: str | None = Field(default=None, alias="IMAP_PASSWORD")

    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str | None = Field(default=None, alias="SMTP_USER")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    email_from: str = Field(default="no-reply@example.com", alias="EMAIL_FROM")

    # API
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_rate_limit_per_minute: int = Field(default=120, alias="API_RATE_LIMIT_PER_MINUTE")

    # Frontend
    backend_base_url: str = Field(default="http://localhost:8000", alias="BACKEND_BASE_URL")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

