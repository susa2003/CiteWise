from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CITEWISE_",
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "CiteWise AI"
    environment: str = "development"
    database_url: str = f"sqlite:///{(PROJECT_ROOT / 'storage' / 'citewise.db').as_posix()}"
    storage_dir: Path = PROJECT_ROOT / "storage"
    max_upload_mb: int = Field(default=50, ge=1, le=500)
    cors_origins: str = "http://localhost:5173"
    llm_provider: str = "none"
    llm_api_key: str | None = None
    llm_model: str | None = None
    llm_base_url: str | None = None
    embedding_provider: str = "none"
    embedding_model: str | None = None
    ocr_enabled: bool = False

    @field_validator("llm_provider", "embedding_provider", mode="before")
    @classmethod
    def normalize_provider(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("llm_provider")
    @classmethod
    def validate_llm_provider(cls, value: str) -> str:
        if value not in {"none", "openai_compatible"}:
            raise ValueError("LLM provider must be 'none' or 'openai_compatible'.")
        return value

    @field_validator("embedding_provider")
    @classmethod
    def validate_embedding_provider(cls, value: str) -> str:
        if value not in {"none", "sentence_transformers"}:
            raise ValueError("Embedding provider must be 'none' or 'sentence_transformers'.")
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def llm_is_configured(self) -> bool:
        return bool(self.llm_provider != "none" and self.llm_api_key and self.llm_model)


@lru_cache
def get_settings() -> Settings:
    return Settings()
