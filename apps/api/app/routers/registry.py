from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import security
from app.database import get_db
from app.models.user import User
from app.schemas.registry import (
    ModelAliasOut,
    ModelVersionOut,
    RegisterFromJobRequest,
    SetAliasRequest,
    SetVersionStatusRequest,
)
from app.services import registry_service
from hom_core.enums import UserRole

router = APIRouter(prefix="/api/registry", tags=["registry"])

_can_write = security.require_role(UserRole.ADMIN, UserRole.ML_ENGINEER)


@router.get("", response_model=list[ModelVersionOut])
def list_versions(
    model_name: str | None = None, db: Session = Depends(get_db), user: User = Depends(security.get_current_user)
):
    return registry_service.list_versions(db, model_name)


@router.post("", response_model=ModelVersionOut, status_code=201)
def register_from_job(
    payload: RegisterFromJobRequest, db: Session = Depends(get_db), user: User = Depends(_can_write)
):
    return registry_service.register_from_job(db, payload.training_job_id, payload.model_name, actor=user.email)


@router.get("/aliases", response_model=list[ModelAliasOut])
def list_aliases(db: Session = Depends(get_db), user: User = Depends(security.get_current_user)):
    return registry_service.list_aliases(db)


@router.put("/aliases", response_model=ModelAliasOut)
def set_alias(payload: SetAliasRequest, db: Session = Depends(get_db), user: User = Depends(_can_write)):
    return registry_service.set_alias(db, payload.alias, payload.model_version_id)


@router.get("/aliases/{alias}", response_model=ModelVersionOut)
def resolve_alias(alias: str, db: Session = Depends(get_db), user: User = Depends(security.get_current_user)):
    return registry_service.resolve_alias(db, alias)


@router.get("/{model_name}", response_model=list[ModelVersionOut])
def list_versions_for_model(
    model_name: str, db: Session = Depends(get_db), user: User = Depends(security.get_current_user)
):
    return registry_service.list_versions(db, model_name)


@router.patch("/versions/{version_id}/status", response_model=ModelVersionOut)
def set_status(
    version_id: str,
    payload: SetVersionStatusRequest,
    db: Session = Depends(get_db),
    user: User = Depends(_can_write),
):
    return registry_service.set_status(db, version_id, payload.status, actor=user.email)
