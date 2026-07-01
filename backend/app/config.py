from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Expert17025"
    debug: bool = False

    database_url: str = "sqlite+aiosqlite:///./data/expert17025.db"
    redis_url: str = "redis://localhost:6379/0"

    secret_key: str = "expert17025-local-dev-secret-key-change-in-prod"
    access_token_expire_minutes: int = 60 * 24
    algorithm: str = "HS256"

    cors_origins: str = "http://localhost:3000"

    llm_provider: Literal["openai", "anthropic", "yandex", "gigachat", "local"] = "local"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    yandex_api_key: str = ""
    yandex_folder_id: str = ""
    gigachat_credentials: str = ""

    use_local_embeddings: bool = True
    embedding_model: str = "local-multilingual"
    embedding_dimensions: int = 384

    knowledge_relevance_threshold: float = 0.75
    hybrid_search_semantic_weight: float = 0.7
    hybrid_search_keyword_weight: float = 0.3

    max_search_time_ms: int = 1000
    max_cached_answer_time_ms: int = 2000
    max_llm_response_time_ms: int = 15000

    uploads_dir: str = "uploads"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def has_llm_api(self) -> bool:
        if self.llm_provider == "local":
            return False
        keys = {
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
            "yandex": self.yandex_api_key,
            "gigachat": self.gigachat_credentials,
        }
        return bool(keys.get(self.llm_provider, ""))


@lru_cache
def get_settings() -> Settings:
    return Settings()
