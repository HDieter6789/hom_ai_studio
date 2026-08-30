import httpx

from hom_core.providers.compute_provider import ComputeProvider, GPUDevice
from hom_core.schemas.worker import GPUInfo


class RemoteGPUProvider(ComputeProvider):
    """Compute provider for a GPU box that is not the worker process's own
    host - e.g. a machine only powered on for the duration of a training
    run. Talks to a small status endpoint (`GET {agent_url}/gpus`) run on
    that remote box. If the agent is unreachable (box powered off, still
    booting), this provider simply reports itself unavailable rather than
    raising - callers must treat "no GPU" as an expected, displayable
    state, not a crash.
    """

    def __init__(self, agent_url: str, agent_token: str | None = None, timeout_seconds: float = 5.0):
        self.agent_url = agent_url.rstrip("/")
        self.agent_token = agent_token
        self.timeout_seconds = timeout_seconds

    def _headers(self) -> dict:
        return {"X-Agent-Token": self.agent_token} if self.agent_token else {}

    def _fetch(self) -> list[dict] | None:
        try:
            resp = httpx.get(f"{self.agent_url}/gpus", headers=self._headers(), timeout=self.timeout_seconds)
            resp.raise_for_status()
            return resp.json()
        except (httpx.HTTPError, ValueError):
            return None

    def is_available(self) -> bool:
        data = self._fetch()
        return bool(data)

    def list_devices(self) -> list[GPUDevice]:
        data = self._fetch() or []
        return [GPUDevice(index=g["index"], name=g["name"], vram_total_gb=g["vram_total_gb"]) for g in data]

    def get_utilization(self) -> list[GPUInfo]:
        data = self._fetch() or []
        return [GPUInfo(**g) for g in data]

    def describe(self) -> str:
        return self.agent_url


def get_compute_provider():
    """Factory selecting LocalGPUProvider vs RemoteGPUProvider based on
    worker configuration - training/deployment code never instantiates a
    concrete provider directly."""
    from worker.config import get_worker_settings
    from worker.providers.compute_local import LocalGPUProvider

    settings = get_worker_settings()
    if settings.compute_provider == "remote" and settings.remote_gpu_agent_url:
        return RemoteGPUProvider(settings.remote_gpu_agent_url, agent_token=settings.remote_gpu_agent_token)
    return LocalGPUProvider()
