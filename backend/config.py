from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "SmartHire"
    api_prefix: str = "/api"

    # In-memory SQLite. StaticPool keeps one connection so state survives sessions.
    database_url: str = "sqlite://"

    jwt_secret: str = "dev-secret-change-me-at-least-32-bytes-long"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    # LLM: mock | openai | anthropic. Falls back to mock when no api key is set.
    llm_provider: str = "mock"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_timeout_seconds: float = 30.0

    # Scoring / fusion policy
    qa_max_score: int = 5
    hold_margin: float = 15.0  # combined score within this of threshold -> HOLD

    # Seed data
    input_data_path: str = "../input-data.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
