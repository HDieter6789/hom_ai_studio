import re
import shutil
from pathlib import Path
from typing import BinaryIO, Iterator

from hom_core.providers.storage_provider import StorageProvider

_SAFE_KEY = re.compile(r"^[A-Za-z0-9_\-./]+$")


class StorageKeyError(ValueError):
    pass


class LocalStorageProvider(StorageProvider):
    """Filesystem-backed storage rooted at a fixed directory. Every key is
    validated and resolved against that root so a caller can never escape
    it via `..` segments or an absolute path - this is the only place
    user-influenced paths are allowed to touch the filesystem.

    apps/api, services/training-worker and services/inference all point
    this at the same shared volume (see docker-compose.yml) so a storage
    key created by one service can be read by another without any of them
    needing to know about the others' internals.
    """

    def __init__(self, root: str):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        if not key or not _SAFE_KEY.match(key) or ".." in key.split("/"):
            raise StorageKeyError(f"Invalid storage key: {key!r}")
        path = (self.root / key).resolve()
        if self.root not in path.parents and path != self.root:
            raise StorageKeyError(f"Storage key escapes storage root: {key!r}")
        return path

    def resolve_path(self, key: str) -> str:
        """Escape hatch for callers (e.g. the LLaMA-Factory adapter) that
        must hand a real filesystem path to an external CLI tool."""
        return str(self._resolve(key))

    def save(self, key: str, stream: BinaryIO) -> str:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            shutil.copyfileobj(stream, f)
        return key

    def open(self, key: str) -> BinaryIO:
        return open(self._resolve(key), "rb")

    def exists(self, key: str) -> bool:
        try:
            return self._resolve(key).exists()
        except StorageKeyError:
            return False

    def delete(self, key: str) -> None:
        path = self._resolve(key)
        if path.exists():
            path.unlink()

    def size(self, key: str) -> int:
        return self._resolve(key).stat().st_size

    def iter_lines(self, key: str) -> Iterator[str]:
        with open(self._resolve(key), "r", encoding="utf-8") as f:
            for line in f:
                yield line.rstrip("\n")
