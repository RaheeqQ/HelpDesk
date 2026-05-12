from sqlmodel import SQLModel, Field
import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, String


class ConversationType(str, Enum):
    direct = "direct"
    group = "group"


class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(default=None, foreign_key="project.id", nullable=True)
    conversation_type: ConversationType = Field(default=ConversationType.direct, sa_column=Column(String, nullable=False))
    created_by: str = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))