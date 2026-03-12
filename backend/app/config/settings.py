from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolves to the directory containing config.py → goes up one level to backend/
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",   # ← absolute path to backend/.env
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


    llm_provider: str = "groq"
    cors_origins: str = "http://localhost:5173,http://localhost:4173"

    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"

    openrouter_api_key: str | None = None
    openrouter_model: str = "meta-llama/llama-3.3-70b-instruct"

    aws_region: str = "us-east-1"
    bedrock_model: str = "amazon.nova-lite-v1:0"

    # Cache Settings
    cache_backend: str = "memory"  # "memory" or "redis"
    cache_ttl: int = 3600  # 1 hour
    cache_max_size: int = 1000  # For in-memory cache
    

    def validate_provider(self) -> None:
        if self.llm_provider == "groq" and not self.groq_api_key:
            raise ValueError("GROQ_API_KEY is required when LLM_PROVIDER=groq")
        if self.llm_provider == "openrouter" and not self.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY is required when LLM_PROVIDER=openrouter")


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance (singleton pattern)."""
    settings = Settings()
    settings.validate_provider
    return settings
