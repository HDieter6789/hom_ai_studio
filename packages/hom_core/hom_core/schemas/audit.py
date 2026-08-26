from datetime import datetime

from pydantic import BaseModel

from hom_core.enums import AuditAction


class AuditLogEntry(BaseModel):
    action: AuditAction
    actor: str
    target_type: str
    target_id: str
    metadata: dict = {}
    timestamp: datetime
