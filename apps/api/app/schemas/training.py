from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from hom_core.enums import ErrorCode, TrainingJobStatus, TrainingPreset, TrainingType


class TrainingJobCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    base_model_id: str
    dataset_id: str
    preset: TrainingPreset = TrainingPreset.BALANCED
    training_type: TrainingType | None = None
    hyperparameter_overrides: dict | None = None


class TrainingJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    base_model_id: str
    dataset_id: str
    training_type: TrainingType
    preset: TrainingPreset
    hyperparameters: dict
    status: TrainingJobStatus
    provider: str
    worker_id: str | None
    current_epoch: float | None
    current_step: int | None
    total_steps: int | None
    loss: float | None
    learning_rate: float | None
    gpu_memory_used_gb: float | None
    gpu_utilization_pct: float | None
    samples_per_sec: float | None
    tokens_per_sec: float | None
    progress_pct: float
    error_code: ErrorCode | None
    error_message: str | None
    failed_step: str | None
    suggested_actions: list
    output_dir: str | None
    artifacts: dict
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class TrainingLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    timestamp: datetime
    level: str
    message: str


class TrainingStatusCallback(BaseModel):
    """Payload the training-worker posts back to the API's internal
    endpoint to report progress."""

    status: TrainingJobStatus | None = None
    current_epoch: float | None = None
    current_step: int | None = None
    total_steps: int | None = None
    loss: float | None = None
    learning_rate: float | None = None
    gpu_memory_used_gb: float | None = None
    gpu_utilization_pct: float | None = None
    samples_per_sec: float | None = None
    tokens_per_sec: float | None = None
    progress_pct: float | None = None
    provider_run_id: str | None = None
    worker_id: str | None = None
    output_dir: str | None = None
    artifacts: dict | None = None
    error_code: ErrorCode | None = None
    error_message: str | None = None
    failed_step: str | None = None
    suggested_actions: list[str] | None = None


class TrainingLogCallback(BaseModel):
    level: str = "info"
    message: str


class TrainingJobConfigOut(BaseModel):
    """Everything the training-worker needs to run a job, without ever
    touching Postgres directly. Deliberately shaped close to
    hom_core.schemas.training.TrainingConfig."""

    job_id: str
    training_name: str
    base_model_id: str
    base_model_local_path: str | None
    base_model_huggingface_id: str | None
    dataset_id: str
    dataset_storage_key: str
    dataset_format: str
    training_type: TrainingType
    preset: TrainingPreset
    hyperparameters: dict
    output_dir: str
