from sqlalchemy import Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin
from hom_core.enums import BaseModelStatus, ModelProvider


class BaseModelEntity(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A registrable foundation model (Qwen, Mistral, Llama, Gemma, ...).
    Never hardcoded - always created through the API/UI."""

    __tablename__ = "base_models"

    name: Mapped[str] = mapped_column(String(255), index=True)
    provider: Mapped[ModelProvider] = mapped_column(Enum(ModelProvider, name="model_provider"))
    huggingface_id: Mapped[str | None] = mapped_column(String(500), nullable=True)
    architecture: Mapped[str | None] = mapped_column(String(255), nullable=True)
    parameter_count: Mapped[str | None] = mapped_column(String(50), nullable=True)
    context_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    license: Mapped[str | None] = mapped_column(String(255), nullable=True)
    quantization: Mapped[str | None] = mapped_column(String(50), nullable=True)
    local_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[BaseModelStatus] = mapped_column(
        Enum(BaseModelStatus, name="base_model_status"), default=BaseModelStatus.UNAVAILABLE
    )
