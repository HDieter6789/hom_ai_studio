import socket
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="HOM_", extra="ignore")

    redis_url: str = "redis://localhost:6379/0"
    api_base_url: str = "http://localhost:8000"
    internal_api_token: str = "dev-only-internal-token-change-me"

    storage_root: str = "./data/storage"

    worker_key: str = socket.gethostname()
    compute_provider: str = "local"  # "local" | "remote"

    # only used when compute_provider == "remote"
    remote_gpu_agent_url: str | None = None

    llama_factory_repo: str = "./vendor/LLaMA-Factory"
    python_executable: str = "python"

    heartbeat_interval_seconds: int = 15
    status_poll_interval_seconds: int = 5


@lru_cache
def get_worker_settings() -> WorkerSettings:
    return WorkerSettings()
