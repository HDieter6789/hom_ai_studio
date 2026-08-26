from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin
from hom_core.enums import DeploymentStatus


class Deployment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "deployments"

    model_version_id: Mapped[str] = mapped_column(ForeignKey("model_versions.id"), index=True)
    served_model_name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    endpoint_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[DeploymentStatus] = mapped_column(
        Enum(DeploymentStatus, name="deployment_status", values_callable=lambda e: [x.value for x in e]), default=DeploymentStatus.PENDING
    )
    worker_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gpu_memory_utilization: Mapped[float] = mapped_column(Float, default=0.85)
    max_model_len: Mapped[int | None] = mapped_column(Integer, nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    stopped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_health_check_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_health_detail: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
