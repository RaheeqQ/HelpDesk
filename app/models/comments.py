from sqlmodel import SQLModel, Field
import uuid
from datetime import datetime, timezone
from typing import Optional


class Comment(SQLModel, table=True):
    __tablename__ = "comments"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    ticket_id: str = Field(foreign_key="tickets.id")
    user_id: str = Field(foreign_key="users.id")
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    edited_at: Optional[datetime] = None