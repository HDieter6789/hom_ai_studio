from functools import lru_cache

from app.config import get_settings
from app.services.storage.local import LocalStorageProvider
from hom_core.providers import StorageProvider


@lru_cache
def get_storage() -> StorageProvider:
    settings = get_settings()
    if settings.storage_backend == "local":
        return LocalStorageProvider(root=settings.storage_root)
    raise ValueError(f"Unsupported storage backend: {settings.storage_backend}")
