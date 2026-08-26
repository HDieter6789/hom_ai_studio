from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Evaluation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "evaluations"

    model_version_id: Mapped[str] = mapped_column(ForeignKey("model_versions.id"), index=True)
    dataset_id: Mapped[str | None] = mapped_column(ForeignKey("datasets.id"), nullable=True)

    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    sample_count: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
