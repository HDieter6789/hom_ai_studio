from datetime import datetime

from pydantic import BaseModel, ConfigDict

from hom_core.schemas.evaluation import EvaluationMetrics


class EvaluationCreate(BaseModel):
    model_version_id: str
    dataset_id: str | None = None
    metrics: EvaluationMetrics
    sample_count: int = 0
    notes: str | None = None


class EvaluationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    model_version_id: str
    dataset_id: str | None
    metrics: dict
    sample_count: int
    notes: str | None
    created_at: datetime


class CompareRequest(BaseModel):
    version_id_a: str
    version_id_b: str
