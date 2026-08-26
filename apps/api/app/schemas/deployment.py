from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from hom_core.enums import DeploymentStatus


class DeploymentCreate(BaseModel):
    model_version_id: str
    served_model_name: str = Field(min_length=1, max_length=255)
    gpu_memory_utilization: float = Field(default=0.85, gt=0, le=1)
    max_model_len: int | None = None


class DeploymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    model_version_id: str
    served_model_name: str
    endpoint_url: str | None
    status: DeploymentStatus
    worker_id: str | None
    gpu_memory_utilization: float
    max_model_len: int | None
    started_at: datetime | None
    stopped_at: datetime | None
    last_health_check_at: datetime | None
    last_health_detail: str | None
    created_at: datetime


class DeploymentStatusCallback(BaseModel):
    status: DeploymentStatus
    endpoint_url: str | None = None
    worker_id: str | None = None
    detail: str | None = None
