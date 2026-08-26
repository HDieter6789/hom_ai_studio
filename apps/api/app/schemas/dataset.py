from datetime import datetime

from pydantic import BaseModel, ConfigDict

from hom_core.enums import DatasetFormat, DatasetStatus, DatasetType


class DatasetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    version: str
    type: DatasetType
    format: DatasetFormat
    source: str
    status: DatasetStatus
    sample_count: int
    file_size_bytes: int
    schema_info: dict
    stats: dict
    validation_errors: list
    created_at: datetime
    updated_at: datetime
    created_by: str | None


class DatasetSampleOut(BaseModel):
    samples: list[dict]
