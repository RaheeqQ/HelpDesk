from sqlmodel import SQLModel, Field
from sqlalchemy import Column, ForeignKey, String
import uuid
from datetime import datetime, timezone
from typing import Optional


class Comment(SQLModel, table=True):
    __tablename__ = "comments"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    ticket_id: str = Field(sa_column=Column(String, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True))
    user_id: str = Field(sa_column=Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True))
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    edited_at: Optional[datetime] = None