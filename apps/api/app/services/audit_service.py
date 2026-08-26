from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.audit import AuditLog
from hom_core.enums import AuditAction


def log(db: Session, *, action: AuditAction, actor: str, target_type: str, target_id: str, metadata: dict | None = None) -> None:
    if not get_settings().audit_log_enabled:
        return
    entry = AuditLog(
        action=action,
        actor=actor,
        target_type=target_type,
        target_id=target_id,
        event_metadata=metadata or {},
    )
    db.add(entry)
    db.commit()


def list_recent(db: Session, limit: int = 100) -> list[AuditLog]:
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
