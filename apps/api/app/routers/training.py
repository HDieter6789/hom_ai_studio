from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import security
from app.database import get_db
from app.models.user import User
from app.schemas.training import TrainingJobCreate, TrainingJobOut, TrainingLogOut
from app.services import training_service
from hom_core.enums import UserRole

router = APIRouter(prefix="/api/training", tags=["training"])

_can_write = security.require_role(UserRole.ADMIN, UserRole.ML_ENGINEER)


@router.get("/jobs", response_model=list[TrainingJobOut])
def list_jobs(db: Session = Depends(get_db), user: User = Depends(security.get_current_user)):
    return training_service.list_jobs(db)


@router.post("/jobs", response_model=TrainingJobOut, status_code=201)
def create_job(payload: TrainingJobCreate, db: Session = Depends(get_db), user: User = Depends(_can_write)):
    return training_service.create_training_job(
        db,
        name=payload.name,
        base_model_id=payload.base_model_id,
        dataset_id=payload.dataset_id,
        preset=payload.preset,
        training_type=payload.training_type,
        hyperparameter_overrides=payload.hyperparameter_overrides,
        actor=user.email,
    )


@router.get("/jobs/{job_id}", response_model=TrainingJobOut)
def get_job(job_id: str, db: Session = Depends(get_db), user: User = Depends(security.get_current_user)):
    return training_service.get_job(db, job_id)


@router.get("/jobs/{job_id}/logs", response_model=list[TrainingLogOut])
def get_job_logs(
    job_id: str, limit: int = 500, db: Session = Depends(get_db), user: User = Depends(security.get_current_user)
):
    return training_service.recent_logs(db, job_id, limit=min(limit, 2000))


@router.post("/jobs/{job_id}/cancel", response_model=TrainingJobOut)
def cancel_job(job_id: str, db: Session = Depends(get_db), user: User = Depends(_can_write)):
    return training_service.cancel_job(db, job_id, actor=user.email)
