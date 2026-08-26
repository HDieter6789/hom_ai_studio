from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin, utcnow
from hom_core.enums import ErrorCode, TrainingJobStatus, TrainingPreset, TrainingType


class TrainingJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "training_jobs"

    name: Mapped[str] = mapped_column(String(255), index=True)
    base_model_id: Mapped[str] = mapped_column(ForeignKey("base_models.id"))
    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id"))

    training_type: Mapped[TrainingType] = mapped_column(Enum(TrainingType, name="training_type"))
    preset: Mapped[TrainingPreset] = mapped_column(Enum(TrainingPreset, name="training_preset"))
    hyperparameters: Mapped[dict] = mapped_column(JSON, default=dict)

    status: Mapped[TrainingJobStatus] = mapped_column(
        Enum(TrainingJobStatus, name="training_job_status"), default=TrainingJobStatus.QUEUED
    )
    provider: Mapped[str] = mapped_column(String(50), default="llama_factory")
    provider_run_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    worker_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    current_epoch: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_step: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_steps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    learning_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    gpu_memory_used_gb: Mapped[float | None] = mapped_column(Float, nullable=True)
    gpu_utilization_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    samples_per_sec: Mapped[float | None] = mapped_column(Float, nullable=True)
    tokens_per_sec: Mapped[float | None] = mapped_column(Float, nullable=True)
    progress_pct: Mapped[float] = mapped_column(Float, default=0)

    error_code: Mapped[ErrorCode | None] = mapped_column(Enum(ErrorCode, name="error_code"), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    failed_step: Mapped[str | None] = mapped_column(String(255), nullable=True)
    suggested_actions: Mapped[list] = mapped_column(JSON, default=list)

    output_dir: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    artifacts: Mapped[dict] = mapped_column(JSON, default=dict)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    logs: Mapped[list["TrainingLog"]] = relationship(
        back_populates="job", cascade="all, delete-orphan", order_by="TrainingLog.timestamp"
    )


class TrainingLog(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "training_logs"

    job_id: Mapped[str] = mapped_column(ForeignKey("training_jobs.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    level: Mapped[str] = mapped_column(String(20), default="info")
    message: Mapped[str] = mapped_column(Text)

    job: Mapped[TrainingJob] = relationship(back_populates="logs")
