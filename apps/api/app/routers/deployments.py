from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import security
from app.database import get_db
from app.models.user import User
from app.schemas.deployment import DeploymentCreate, DeploymentOut
from app.services import deployment_service
from hom_core.enums import UserRole

router = APIRouter(prefix="/api/deployments", tags=["deployments"])

_can_write = security.require_role(UserRole.ADMIN, UserRole.ML_ENGINEER)


@router.get("", response_model=list[DeploymentOut])
def list_deployments(db: Session = Depends(get_db), user: User = Depends(security.get_current_user)):
    return deployment_service.list_deployments(db)


@router.post("", response_model=DeploymentOut, status_code=201)
def create_deployment(payload: DeploymentCreate, db: Session = Depends(get_db), user: User = Depends(_can_write)):
    return deployment_service.create_deployment(
        db,
        model_version_id=payload.model_version_id,
        served_model_name=payload.served_model_name,
        gpu_memory_utilization=payload.gpu_memory_utilization,
        max_model_len=payload.max_model_len,
        actor=user.email,
    )


@router.get("/{deployment_id}", response_model=DeploymentOut)
def get_deployment(deployment_id: str, db: Session = Depends(get_db), user: User = Depends(security.get_current_user)):
    return deployment_service.get_deployment(db, deployment_id)


@router.delete("/{deployment_id}", response_model=DeploymentOut)
def stop_deployment(deployment_id: str, db: Session = Depends(get_db), user: User = Depends(_can_write)):
    return deployment_service.stop_deployment(db, deployment_id, actor=user.email)
