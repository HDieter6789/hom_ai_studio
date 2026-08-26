from abc import ABC, abstractmethod
from dataclasses import dataclass

from hom_core.schemas.worker import GPUInfo


@dataclass
class GPUDevice:
    index: int
    name: str
    vram_total_gb: float


class ComputeProvider(ABC):
    """Abstraction over where training/inference compute actually runs.
    Training and inference code depend only on this interface, never on
    how a GPU was obtained (bare metal, remote box, cloud instance)."""

    @abstractmethod
    def is_available(self) -> bool:
        """Whether this compute provider currently has usable GPU(s)."""

    @abstractmethod
    def list_devices(self) -> list[GPUDevice]:
        """Enumerate GPUs this provider can currently schedule work on."""

    @abstractmethod
    def get_utilization(self) -> list[GPUInfo]:
        """Return live utilization/VRAM snapshots for each device."""

    @abstractmethod
    def describe(self) -> str:
        """Human readable identifier, e.g. hostname or remote endpoint."""
