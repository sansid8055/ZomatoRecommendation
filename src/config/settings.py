from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_provider: str = Field(default="groq", alias="LLM_PROVIDER")
    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")
    llm_model: str = Field(default="llama-3.3-70b-versatile", alias="LLM_MODEL")
    llm_temperature: float = Field(default=0.3, alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=2000, alias="LLM_MAX_TOKENS")
    llm_timeout: float = Field(default=60.0, alias="LLM_TIMEOUT")

    max_candidates: int = Field(default=25, alias="MAX_CANDIDATES")
    top_k_results: int = Field(default=5, alias="TOP_K_RESULTS")

    data_cache_path: Path = Field(
        default=PROJECT_ROOT / "data" / "processed" / "restaurants.parquet",
        alias="DATA_CACHE_PATH",
    )
    hf_dataset_id: str = Field(
        default="ManikaSaini/zomato-restaurant-recommendation",
        alias="HF_DATASET_ID",
    )
    default_metro_city: str = Field(
        default="Bangalore",
        alias="DEFAULT_METRO_CITY",
    )
    data_metro_filter: str | None = Field(
        default="Bangalore",
        alias="DATA_METRO_FILTER",
        description="Keep only this metro when ingesting multi-city HF datasets",
    )

    @field_validator("max_candidates", "top_k_results")
    @classmethod
    def _positive_int(cls, value: int) -> int:
        if value < 1:
            raise ValueError("must be >= 1")
        return value

    @field_validator("data_cache_path", mode="before")
    @classmethod
    def _resolve_path(cls, value: str | Path) -> Path:
        path = Path(value)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return path

    @model_validator(mode="after")
    def _clamp_top_k_to_max_candidates(self) -> "Settings":
        if self.top_k_results > self.max_candidates:
            object.__setattr__(self, "top_k_results", self.max_candidates)
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
