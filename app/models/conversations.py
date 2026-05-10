from sqlmodel import SQLModel, Field
import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, String


class ConversationType(str, Enum):
    ticket = "ticket"
    direct = "direct"
    group = "group"


class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    ticket_id: str = Field(foreign_key="tickets.id")
    type: ConversationType = Field(default=ConversationType.ticket, sa_column=Column(String, nullable=False))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))