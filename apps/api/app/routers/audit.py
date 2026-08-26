from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import security
from app.database import get_db
from app.models.user import User
from app.schemas.audit import AuditLogOut
from app.services import audit_service
from hom_core.enums import UserRole

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("", response_model=list[AuditLogOut])
def list_audit_log(
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(security.require_role(UserRole.ADMIN)),
):
    return audit_service.list_recent(db, limit=min(limit, 500))
