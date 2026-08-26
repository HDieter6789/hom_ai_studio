from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="HOM_", extra="ignore")

    environment: str = "development"
    database_url: str = "postgresql+psycopg://hom:hom@localhost:5432/hom_ai_studio"
    redis_url: str = "redis://localhost:6379/0"

    # secret used to sign session/JWT tokens - MUST be overridden via env in
    # any non-local environment, never hardcoded for real deployments
    secret_key: str = "dev-only-insecure-secret-change-me"
    access_token_expire_minutes: int = 60 * 12

    # shared secret the training-worker/inference services use to call back
    # into internal API endpoints (job status/log/metric updates). Never
    # exposed to the frontend.
    internal_api_token: str = "dev-only-internal-token-change-me"

    storage_backend: str = "local"
    storage_root: str = "./data/storage"
    max_upload_size_mb: int = 512

    training_provider: str = "llama_factory"
    inference_provider: str = "vllm"

    llama_factory_path: str = "./services/training-worker/vendor/LLaMA-Factory"
    vllm_python: str = "python"

    cors_origins: list[str] = ["http://localhost:3000"]

    audit_log_enabled: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
