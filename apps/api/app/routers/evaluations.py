from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import security
from app.database import get_db
from app.models.user import User
from app.schemas.evaluation import CompareRequest, EvaluationCreate, EvaluationOut
from app.services import evaluation_service
from hom_core.enums import UserRole

router = APIRouter(prefix="/api/evaluations", tags=["evaluations"])

_can_write = security.require_role(UserRole.ADMIN, UserRole.ML_ENGINEER)


@router.get("", response_model=list[EvaluationOut])
def list_evaluations(
    model_version_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(security.get_current_user),
):
    return evaluation_service.list_evaluations(db, model_version_id)


@router.post("", response_model=EvaluationOut, status_code=201)
def create_evaluation(payload: EvaluationCreate, db: Session = Depends(get_db), user: User = Depends(_can_write)):
    return evaluation_service.create_evaluation(
        db,
        model_version_id=payload.model_version_id,
        dataset_id=payload.dataset_id,
        metrics=payload.metrics,
        sample_count=payload.sample_count,
        notes=payload.notes,
        actor=user.email,
    )


@router.post("/compare")
def compare(payload: CompareRequest, db: Session = Depends(get_db), user: User = Depends(security.get_current_user)):
    return evaluation_service.compare(db, payload.version_id_a, payload.version_id_b)
