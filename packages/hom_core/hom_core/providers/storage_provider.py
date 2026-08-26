from abc import ABC, abstractmethod
from typing import BinaryIO, Iterator


class StorageProvider(ABC):
    """Abstraction over where files (dataset uploads, model artifacts,
    checkpoints) live. LocalStorageProvider implements this today; an
    S3/MinIO-backed implementation can be dropped in later without
    touching callers."""

    @abstractmethod
    def save(self, key: str, stream: BinaryIO) -> str:
        """Persist a stream under a namespaced key. Returns a storage-
        internal path/URI, never a raw filesystem path the caller must
        trust as a literal disk location."""

    @abstractmethod
    def open(self, key: str) -> BinaryIO:
        """Open a previously saved object for reading."""

    @abstractmethod
    def exists(self, key: str) -> bool: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...

    @abstractmethod
    def size(self, key: str) -> int: ...

    @abstractmethod
    def iter_lines(self, key: str) -> Iterator[str]:
        """Stream a text object line by line (used for JSONL datasets and
        training log files without loading them fully into memory)."""
