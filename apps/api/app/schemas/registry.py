from datetime import datetime

from pydantic import BaseModel, ConfigDict

from hom_core.enums import ModelVersionStatus


class RegisterFromJobRequest(BaseModel):
    training_job_id: str
    model_name: str


class ModelVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    model_name: str
    version: int
    display_name: str
    base_model_id: str | None
    dataset_id: str | None
    training_job_id: str | None
    training_config: dict
    training_metrics: dict
    evaluation_metrics: dict
    artifact_location: str | None
    status: ModelVersionStatus
    deployment_status: str | None
    created_at: datetime


class SetVersionStatusRequest(BaseModel):
    status: ModelVersionStatus


class SetAliasRequest(BaseModel):
    alias: str
    model_version_id: str


class ModelAliasOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    alias: str
    model_version_id: str
    updated_at: datetime
