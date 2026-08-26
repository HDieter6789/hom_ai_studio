from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app import security
from app.database import get_db
from app.models.user import User
from app.schemas.dataset import DatasetOut, DatasetSampleOut
from app.services import dataset_service
from hom_core.enums import DatasetType, UserRole

router = APIRouter(prefix="/api/datasets", tags=["datasets"])

_can_write = security.require_role(UserRole.ADMIN, UserRole.ML_ENGINEER, UserRole.DEVELOPER)


@router.get("", response_model=list[DatasetOut])
def list_datasets(db: Session = Depends(get_db), user: User = Depends(security.get_current_user)):
    return dataset_service.list_datasets(db)


@router.post("", response_model=DatasetOut, status_code=201)
async def create_dataset(
    name: str = Form(...),
    description: str | None = Form(None),
    type: DatasetType = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(_can_write),
):
    return await dataset_service.upload_dataset(
        db, name=name, description=description, dataset_type=type, file=file, actor=user.email
    )


@router.get("/{dataset_id}", response_model=DatasetOut)
def get_dataset(dataset_id: str, db: Session = Depends(get_db), user: User = Depends(security.get_current_user)):
    return dataset_service.get_dataset(db, dataset_id)


@router.get("/{dataset_id}/preview", response_model=DatasetSampleOut)
def preview_dataset(
    dataset_id: str, limit: int = 20, db: Session = Depends(get_db), user: User = Depends(security.get_current_user)
):
    return DatasetSampleOut(samples=dataset_service.preview_samples(db, dataset_id, limit=min(limit, 100)))


@router.delete("/{dataset_id}", status_code=204)
def delete_dataset(dataset_id: str, db: Session = Depends(get_db), user: User = Depends(_can_write)):
    dataset_service.delete_dataset(db, dataset_id, actor=user.email)
