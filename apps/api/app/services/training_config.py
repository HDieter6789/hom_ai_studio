from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.base_model import BaseModelEntity
from app.models.dataset import Dataset
from hom_core.enums import BaseModelStatus, DatasetStatus, TrainingPreset, TrainingType
from hom_core.schemas.training import HyperParameters, PRESET_TRAINING_TYPE, resolve_hyperparameters


def resolve_training_type(preset: TrainingPreset, requested: TrainingType | None) -> TrainingType:
    if preset != TrainingPreset.CUSTOM:
        return PRESET_TRAINING_TYPE.get(preset, TrainingType.QLORA)
    if requested is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "training_type is required for the Custom preset")
    return requested


def build_hyperparameters(preset: TrainingPreset, overrides: dict | None) -> HyperParameters:
    try:
        return resolve_hyperparameters(preset, overrides)
    except Exception as exc:  # pydantic ValidationError etc.
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Invalid hyperparameters: {exc}") from exc


def validate_training_inputs(db: Session, base_model_id: str, dataset_id: str) -> tuple[BaseModelEntity, Dataset]:
    base_model = db.get(BaseModelEntity, base_model_id)
    if base_model is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Base model not found")
    if base_model.status not in (BaseModelStatus.AVAILABLE, BaseModelStatus.DOWNLOADING):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Base model '{base_model.name}' is not available (status: {base_model.status.value})",
        )

    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Dataset not found")
    if dataset.status != DatasetStatus.READY:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Dataset '{dataset.name}' is not ready for training (status: {dataset.status.value})",
        )

    return base_model, dataset
