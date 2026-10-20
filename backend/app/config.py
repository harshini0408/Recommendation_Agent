"""Settings anchored to backend/.env, independent of terminal directory."""

from functools import lru_cache
from pathlib import Path
from typing import Literal
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env", extra="ignore", env_file_encoding="utf-8"
    )
    app_env: str = "development"
    db_host: str = "localhost"
    db_port: int = Field(default=5432, ge=1, le=65535)
    db_name: str = "electronics_assistant"
    db_user: str = "electronics_app"
    db_password: SecretStr = SecretStr("")
    test_db_name: str = "electronics_assistant_test"
    groq_api_key: SecretStr = SecretStr("")
    groq_model: str = "openai/gpt-oss-20b"
    llm_mode: Literal["live", "demo"] = "live"
    llm_timeout_seconds: float = Field(default=30, ge=1, le=120)
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    def database_url(self, *, test=False) -> URL:
        name = self.test_db_name if test else self.db_name
        if test and (name == self.db_name or not name.endswith("_test")):
            raise ValueError("Test database must differ from development and end in _test.")
        return URL.create(
            "postgresql+psycopg",
            username=self.db_user,
            password=self.db_password.get_secret_value(),
            host=self.db_host,
            port=self.db_port,
            database=name,
        )


@lru_cache
def get_settings():
    return Settings()
