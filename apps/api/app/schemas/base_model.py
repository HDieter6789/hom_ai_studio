from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from hom_core.enums import BaseModelStatus, ModelProvider


class BaseModelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    provider: ModelProvider
    huggingface_id: str | None = None
    architecture: str | None = None
    parameter_count: str | None = None
    context_length: int | None = Field(default=None, gt=0)
    license: str | None = None
    quantization: str | None = None
    local_path: str | None = None
    status: BaseModelStatus = BaseModelStatus.UNAVAILABLE


class BaseModelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    provider: ModelProvider
    huggingface_id: str | None
    architecture: str | None
    parameter_count: str | None
    context_length: int | None
    license: str | None
    quantization: str | None
    local_path: str | None
    status: BaseModelStatus
    created_at: datetime
