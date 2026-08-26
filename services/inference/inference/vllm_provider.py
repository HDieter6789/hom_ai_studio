"""vLLM inference provider adapter.

Deploys a model artifact by launching `vllm serve` (an OpenAI-compatible
server) as a subprocess bound to a locally allocated port, and tracks it
in a small JSON registry file so deployments survive a worker restart
(the subprocess itself would not, but health_check() then correctly
reports it unhealthy rather than the worker losing track of it silently).

This is the only file that knows vLLM's CLI/port model - callers only
ever see hom_core.providers.InferenceProvider.
"""

import json
import shutil
import socket
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

from hom_core.providers.inference_provider import InferenceProvider
from hom_core.schemas.deployment import DeploymentRequest, DeploymentResult, HealthCheckResult


class VLLMNotInstalled(RuntimeError):
    pass


class VLLMInferenceProvider(InferenceProvider):
    def __init__(self, registry_path: str, host: str = "0.0.0.0", port_range: tuple[int, int] = (8100, 8199)):
        self.registry_path = Path(registry_path)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.host = host
        self.port_range = port_range

    # -- registry persistence -----------------------------------------

    def _load_registry(self) -> dict:
        if not self.registry_path.exists():
            return {}
        try:
            return json.loads(self.registry_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_registry(self, data: dict) -> None:
        self.registry_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _allocate_port(self, taken: set[int]) -> int:
        for port in range(*self.port_range):
            if port in taken:
                continue
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex((self.host, port)) != 0:
                    return port
        raise RuntimeError("No free port available in the configured vLLM port range")

    # -- InferenceProvider interface -----------------------------------

    def deploy_model(self, request: DeploymentRequest) -> DeploymentResult:
        if shutil.which("vllm") is None:
            raise VLLMNotInstalled(
                "vLLM is not installed in this environment. Install it in the inference "
                "service/image to serve real models; the deployment will otherwise fail "
                "with a clear 'vLLM not installed' error rather than crashing silently."
            )

        registry = self._load_registry()
        taken_ports = {entry["port"] for entry in registry.values()}
        port = self._allocate_port(taken_ports)

        cmd = [
            "vllm",
            "serve",
            request.artifact_path,
            "--served-model-name",
            request.served_model_name,
            "--host",
            self.host,
            "--port",
            str(port),
            "--gpu-memory-utilization",
            str(request.gpu_memory_utilization),
        ]
        if request.max_model_len:
            cmd += ["--max-model-len", str(request.max_model_len)]
        if request.quantization:
            cmd += ["--quantization", request.quantization]

        log_path = self.registry_path.parent / f"{request.served_model_name}.log"
        with open(log_path, "ab") as log_f:
            process = subprocess.Popen(cmd, stdout=log_f, stderr=subprocess.STDOUT, shell=False, start_new_session=True)

        started_at = datetime.now(timezone.utc)
        registry[request.served_model_name] = {
            "pid": process.pid,
            "port": port,
            "artifact_path": request.artifact_path,
            "started_at": started_at.isoformat(),
        }
        self._save_registry(registry)

        return DeploymentResult(
            endpoint_url=f"http://{self.host}:{port}/v1",
            process_id=process.pid,
            started_at=started_at,
        )

    def stop_model(self, served_model_name: str) -> None:
        registry = self._load_registry()
        entry = registry.pop(served_model_name, None)
        self._save_registry(registry)
        if entry is None:
            return
        import os
        import signal

        try:
            os.killpg(os.getpgid(entry["pid"]), signal.SIGTERM)
        except (ProcessLookupError, PermissionError, OSError):
            pass

    def health_check(self, served_model_name: str) -> HealthCheckResult:
        registry = self._load_registry()
        entry = registry.get(served_model_name)
        checked_at = datetime.now(timezone.utc)
        if entry is None:
            return HealthCheckResult(healthy=False, checked_at=checked_at, detail="Not deployed")

        url = f"http://{self.host}:{entry['port']}/health"
        start = time.monotonic()
        try:
            resp = httpx.get(url, timeout=5.0)
            latency_ms = (time.monotonic() - start) * 1000
            healthy = resp.status_code == 200
            return HealthCheckResult(
                healthy=healthy,
                checked_at=checked_at,
                latency_ms=latency_ms,
                detail=None if healthy else f"HTTP {resp.status_code}",
            )
        except httpx.HTTPError as exc:
            return HealthCheckResult(healthy=False, checked_at=checked_at, detail=str(exc))

    def list_models(self) -> list[str]:
        return list(self._load_registry().keys())
