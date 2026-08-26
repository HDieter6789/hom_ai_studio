from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin
from hom_core.enums import ComputeProviderKind, WorkerStatus


class Worker(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A GPU worker registered with the platform. Registered dynamically -
    workers call POST /api/workers/heartbeat, they are never hardcoded."""

    __tablename__ = "workers"

    worker_key: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hostname: Mapped[str] = mapped_column(String(255))
    status: Mapped[WorkerStatus] = mapped_column(Enum(WorkerStatus, name="worker_status"), default=WorkerStatus.OFFLINE)
    compute_provider: Mapped[ComputeProviderKind] = mapped_column(
        Enum(ComputeProviderKind, name="compute_provider_kind"), default=ComputeProviderKind.LOCAL
    )
    gpus: Mapped[list] = mapped_column(JSON, default=list)
    running_job_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
