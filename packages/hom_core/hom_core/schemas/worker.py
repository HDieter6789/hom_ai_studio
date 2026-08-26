from pydantic import BaseModel


class GPUInfo(BaseModel):
    index: int
    name: str
    vram_total_gb: float
    vram_used_gb: float
    utilization_pct: float
    temperature_c: float | None = None


class WorkerInfo(BaseModel):
    worker_id: str
    hostname: str
    status: str
    gpus: list[GPUInfo] = []
    running_job_id: str | None = None
    compute_provider: str = "local"
