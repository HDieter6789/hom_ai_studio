from datetime import datetime

from pydantic import BaseModel, ConfigDict

from hom_core.enums import ComputeProviderKind, WorkerStatus


class WorkerHeartbeat(BaseModel):
    worker_key: str
    hostname: str
    status: WorkerStatus
    compute_provider: ComputeProviderKind = ComputeProviderKind.LOCAL
    gpus: list[dict] = []
    running_job_id: str | None = None


class WorkerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    worker_key: str
    hostname: str
    status: WorkerStatus
    compute_provider: ComputeProviderKind
    gpus: list
    running_job_id: str | None
    last_heartbeat_at: datetime | None
