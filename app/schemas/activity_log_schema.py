from pydantic import BaseModel
from datetime import datetime


class ActivityLogRead(BaseModel):
    id: str
    user_id: str
    project_id: str
    action: str
    entity_type: str
    entity_id: str
    old_value: str | None = None
    new_value: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True