from datetime import datetime

from pydantic import BaseModel


class DeploymentRequest(BaseModel):
    model_version_id: str
    served_model_name: str
    artifact_path: str
    gpu_memory_utilization: float = 0.85
    max_model_len: int | None = None
    quantization: str | None = None


class DeploymentResult(BaseModel):
    endpoint_url: str | None
    container_id: str | None = None
    process_id: int | None = None
    started_at: datetime


class HealthCheckResult(BaseModel):
    healthy: bool
    checked_at: datetime
    latency_ms: float | None = None
    detail: str | None = None
