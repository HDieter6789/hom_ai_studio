import httpx

from hom_core.providers.compute_provider import ComputeProvider, GPUDevice
from hom_core.schemas.worker import GPUInfo


class RemoteGPUProvider(ComputeProvider):
    """
    Compute provider for the remote/on-demand GPU infrastructure.

    Architecture:

        AI Studio training worker
            -> HOM Training Gateway
            -> Vast.ai on-demand GPU

    Important semantics:

    - GET /health determines whether the remote compute infrastructure
      is available for accepting work.
    - GET /gpus reports GPUs that are currently running.
    - An empty /gpus response is NORMAL before a training run because
      Vast.ai instances are provisioned on demand.
    """

    def __init__(
        self,
        agent_url: str,
        agent_token: str | None = None,
        timeout_seconds: float = 5.0,
    ):
        self.agent_url = agent_url.rstrip("/")
        self.agent_token = agent_token
        self.timeout_seconds = timeout_seconds

    def _headers(self) -> dict[str, str]:
        if not self.agent_token:
            return {}

        return {
            "X-Agent-Token": self.agent_token,
        }

    def _fetch_health(self) -> dict | None:
        """
        Check whether the HOM Training Gateway itself is operational.

        GPU presence is deliberately NOT checked here because GPUs are
        provisioned on demand only after a training job is submitted.
        """
        try:
            response = httpx.get(
                f"{self.agent_url}/health",
                timeout=self.timeout_seconds,
            )

            response.raise_for_status()

            data = response.json()

            if not isinstance(data, dict):
                return None

            return data

        except (
            httpx.HTTPError,
            ValueError,
        ):
            return None

    def _fetch_gpus(self) -> list[dict] | None:
        """
        Return currently running GPU devices.

        [] is a valid state when no training job is active.
        """
        try:
            response = httpx.get(
                f"{self.agent_url}/gpus",
                headers=self._headers(),
                timeout=self.timeout_seconds,
            )

            response.raise_for_status()

            data = response.json()

            if not isinstance(data, list):
                return None

            return data

        except (
            httpx.HTTPError,
            ValueError,
        ):
            return None

    def is_available(self) -> bool:
        """
        Return True when the Training Gateway can accept a job.

        This must NOT depend on whether a GPU is already running.
        """
        data = self._fetch_health()

        if data is None:
            return False

        return data.get("ok") is True

    def list_devices(self) -> list[GPUDevice]:
        data = self._fetch_gpus() or []

        return [
            GPUDevice(
                index=g["index"],
                name=g["name"],
                vram_total_gb=g["vram_total_gb"],
            )
            for g in data
        ]

    def get_utilization(self) -> list[GPUInfo]:
        data = self._fetch_gpus() or []

        return [
            GPUInfo(**gpu)
            for gpu in data
        ]

    def describe(self) -> str:
        return self.agent_url


def get_compute_provider():
    """
    Select the configured compute provider.

    Remote mode means:
        AI Studio -> HOM Training Gateway -> Vast.ai
    """
    from worker.config import get_worker_settings
    from worker.providers.compute_local import LocalGPUProvider

    settings = get_worker_settings()

    if (
        settings.compute_provider == "remote"
        and settings.remote_gpu_agent_url
    ):
        return RemoteGPUProvider(
            settings.remote_gpu_agent_url,
            agent_token=settings.remote_gpu_agent_token,
        )

    return LocalGPUProvider()
