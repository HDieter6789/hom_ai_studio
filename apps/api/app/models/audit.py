from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.common import UUIDPrimaryKeyMixin, utcnow
from hom_core.enums import AuditAction


class AuditLog(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "audit_logs"

    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction, name="audit_action"))
    actor: Mapped[str] = mapped_column(String(255))
    target_type: Mapped[str] = mapped_column(String(100))
    target_id: Mapped[str] = mapped_column(String(255))
    event_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
