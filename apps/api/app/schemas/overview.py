from pydantic import BaseModel

from app.schemas.registry import ModelVersionOut
from app.schemas.training import TrainingJobOut


class OverviewStats(BaseModel):
    models_total: int
    production_models: int
    active_training_jobs: int
    training_jobs_last_30_days: int
    datasets_total: int
    training_samples_total: int
    gpu_workers_online: int
    gpu_workers_total: int
    avg_gpu_utilization_pct: float | None
    active_deployments: int


class OverviewResponse(BaseModel):
    stats: OverviewStats
    recent_training_runs: list[TrainingJobOut]
    production_models: list[ModelVersionOut]
