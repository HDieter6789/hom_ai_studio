from sqlalchemy import JSON, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin
from hom_core.enums import DatasetFormat, DatasetStatus, DatasetType


class Dataset(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "datasets"

    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(50), default="v1")
    type: Mapped[DatasetType] = mapped_column(Enum(DatasetType, name="dataset_type"))
    format: Mapped[DatasetFormat] = mapped_column(Enum(DatasetFormat, name="dataset_format"))
    source: Mapped[str] = mapped_column(String(255), default="upload")
    status: Mapped[DatasetStatus] = mapped_column(
        Enum(DatasetStatus, name="dataset_status"), default=DatasetStatus.UPLOADING
    )

    storage_key: Mapped[str] = mapped_column(String(1024))
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0)

    sample_count: Mapped[int] = mapped_column(Integer, default=0)
    schema_info: Mapped[dict] = mapped_column(JSON, default=dict)
    stats: Mapped[dict] = mapped_column(JSON, default=dict)
    validation_errors: Mapped[list] = mapped_column(JSON, default=list)
    dataset_metadata: Mapped[dict] = mapped_column(JSON, default=dict)

    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
