from sqlalchemy import JSON, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin
from hom_core.enums import ModelVersionStatus


class ModelVersion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A concrete, versioned, trained model - the unit the Model Registry
    manages. `model_name` groups versions together (e.g. all HOM-CRM
    versions share model_name="HOM-CRM")."""

    __tablename__ = "model_versions"
    __table_args__ = (UniqueConstraint("model_name", "version", name="uq_model_name_version"),)

    model_name: Mapped[str] = mapped_column(String(255), index=True)
    version: Mapped[int] = mapped_column(Integer)

    base_model_id: Mapped[str | None] = mapped_column(ForeignKey("base_models.id"), nullable=True)
    dataset_id: Mapped[str | None] = mapped_column(ForeignKey("datasets.id"), nullable=True)
    training_job_id: Mapped[str | None] = mapped_column(ForeignKey("training_jobs.id"), nullable=True)

    training_config: Mapped[dict] = mapped_column(JSON, default=dict)
    training_metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    evaluation_metrics: Mapped[dict] = mapped_column(JSON, default=dict)

    artifact_location: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[ModelVersionStatus] = mapped_column(
        Enum(ModelVersionStatus, name="model_version_status"), default=ModelVersionStatus.EXPERIMENTAL
    )
    deployment_status: Mapped[str | None] = mapped_column(String(50), nullable=True)

    @property
    def display_name(self) -> str:
        return f"{self.model_name}-v{self.version}"


class ModelAlias(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Stable pointer (e.g. hom-crm-production) an Agent can target without
    being updated on every deployment."""

    __tablename__ = "model_aliases"

    alias: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    model_version_id: Mapped[str] = mapped_column(ForeignKey("model_versions.id"))
