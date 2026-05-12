from sqlmodel import SQLModel, Field
import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, ForeignKey, String


class ConversationType(str, Enum):
    direct = "direct"
    group = "group"


class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(sa_column=Column(String, ForeignKey("project.id", ondelete="CASCADE"), nullable=True, index=True))
    conversation_type: ConversationType = Field(default=ConversationType.direct, sa_column=Column(String, nullable=False, index=True))
    created_by: str = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    title: str | None = None
    updated_at: datetime | None = None