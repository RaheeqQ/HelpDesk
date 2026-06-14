from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
import uuid


class ActivityLog(SQLModel, table=True):
    __tablename__ = "activity_logs"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    
    user_id: str = Field(nullable=False, index=True)
    project_id: str = Field(nullable=False, index=True) 
    
    action: str
    entity_type: str
    entity_id: str
    
    old_value: str | None = None
    new_value: str | None = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
