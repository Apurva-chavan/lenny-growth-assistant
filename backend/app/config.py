from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_env: str = "development"
    log_level: str = "info"

    database_url: str = "postgresql+asyncpg://lenny:lenny_pass@localhost:5432/lenny_db"

    @property
    def async_database_url(self) -> str:
        """Convert standard postgres:// URL from Render to asyncpg-compatible URL."""
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    llm_provider: str = "groq"  # anthropic | openai | ollama | gemini | groq

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-sonnet-20241022"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.2"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    groq_api_key: str = ""
    groq_model: str = "llama3-8b-8192"

    transcripts_dir: str = "/app/data/transcripts"
    vector_index_path: str = "/app/data/vector_index"
    chunk_size: int = 800
    chunk_overlap: int = 100
    top_k_results: int = 5

    allowed_origins: str = "http://localhost:3000,http://localhost:5173"

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
