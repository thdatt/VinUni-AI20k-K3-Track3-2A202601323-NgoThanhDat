"""Central application configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables or `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="local", validation_alias="APP_ENV")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    llm_provider: str = Field(default="offline", validation_alias="LLM_PROVIDER")

    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", validation_alias="OPENAI_MODEL")
    # Any OpenAI-compatible endpoint (OpenRouter, Together, a local server).
    # Left unset the SDK talks to api.openai.com.
    openai_base_url: str | None = Field(default=None, validation_alias="OPENAI_BASE_URL")

    groq_api_key: str | None = Field(default=None, validation_alias="GROQ_API_KEY")
    groq_model: str = Field(default="openai/gpt-oss-120b", validation_alias="GROQ_MODEL")

    search_provider: str = Field(default="offline", validation_alias="SEARCH_PROVIDER")
    offline_corpus_path: Path = Field(
        default=Path("data/offline_corpus"),
        validation_alias="OFFLINE_CORPUS_PATH",
    )
    tavily_api_key: str | None = Field(default=None, validation_alias="TAVILY_API_KEY")

    langsmith_api_key: str | None = Field(default=None, validation_alias="LANGSMITH_API_KEY")
    langsmith_project: str = Field(
        default="multi-agent-research-lab",
        validation_alias="LANGSMITH_PROJECT",
    )
    langfuse_public_key: str | None = Field(default=None, validation_alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str | None = Field(default=None, validation_alias="LANGFUSE_SECRET_KEY")
    langfuse_host: str = Field(
        default="https://cloud.langfuse.com",
        validation_alias="LANGFUSE_HOST",
    )

    max_iterations: int = Field(default=6, ge=1, le=20, validation_alias="MAX_ITERATIONS")
    timeout_seconds: int = Field(default=90, ge=5, le=600, validation_alias="TIMEOUT_SECONDS")
    max_retries: int = Field(default=3, ge=1, le=8, validation_alias="MAX_RETRIES")
    enable_critic: bool = Field(default=True, validation_alias="ENABLE_CRITIC")

    input_cost_per_1m: float | None = Field(default=None, validation_alias="INPUT_COST_PER_1M")
    output_cost_per_1m: float | None = Field(default=None, validation_alias="OUTPUT_COST_PER_1M")

    def validate_provider(self, *, require_real: bool = False) -> None:
        provider = self.llm_provider.lower().strip()
        if require_real and provider == "offline":
            raise ValueError(
                "Final submission requires LLM_PROVIDER=groq or openai; "
                "offline mode is only for deterministic tests."
            )
        if provider == "groq" and not self.groq_api_key:
            raise ValueError("GROQ_API_KEY is required for LLM_PROVIDER=groq.")
        if provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for LLM_PROVIDER=openai.")
        if provider not in {"offline", "groq", "openai"}:
            raise ValueError(f"Unsupported LLM_PROVIDER={self.llm_provider!r}.")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
