import socket

from hom_core.providers.compute_provider import ComputeProvider, GPUDevice
from hom_core.schemas.worker import GPUInfo

from worker import gpu


class LocalGPUProvider(ComputeProvider):
    """Compute provider for GPUs attached to the machine the worker
    process itself runs on. Degrades gracefully (is_available() == False)
    when no GPU/driver is present, e.g. in a CPU-only dev container."""

    def is_available(self) -> bool:
        return gpu.nvidia_smi_available() and len(gpu.query_devices()) > 0

    def list_devices(self) -> list[GPUDevice]:
        return gpu.query_devices()

    def get_utilization(self) -> list[GPUInfo]:
        return gpu.query_gpus()

    def describe(self) -> str:
        return socket.gethostname()
