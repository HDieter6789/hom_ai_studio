from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import security
from app.database import get_db
from app.models.base_model import BaseModelEntity
from app.models.user import User
from app.schemas.base_model import BaseModelCreate, BaseModelOut
from hom_core.enums import UserRole

router = APIRouter(prefix="/api/models", tags=["base-models"])

_can_write = security.require_role(UserRole.ADMIN, UserRole.ML_ENGINEER)


@router.get("", response_model=list[BaseModelOut])
def list_base_models(db: Session = Depends(get_db), user: User = Depends(security.get_current_user)):
    return db.query(BaseModelEntity).order_by(BaseModelEntity.name).all()


@router.post("", response_model=BaseModelOut, status_code=201)
def register_base_model(payload: BaseModelCreate, db: Session = Depends(get_db), user: User = Depends(_can_write)):
    model = BaseModelEntity(**payload.model_dump())
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


@router.get("/{model_id}", response_model=BaseModelOut)
def get_base_model(model_id: str, db: Session = Depends(get_db), user: User = Depends(security.get_current_user)):
    model = db.get(BaseModelEntity, model_id)
    if model is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Base model not found")
    return model
