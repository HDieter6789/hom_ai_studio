from datetime import datetime

from pydantic import BaseModel, ConfigDict

from hom_core.enums import AuditAction


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    action: AuditAction
    actor: str
    target_type: str
    target_id: str
    event_metadata: dict
    timestamp: datetime
