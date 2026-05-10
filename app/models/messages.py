from sqlmodel import SQLModel, Field
import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, String


class MessageType(str, Enum):
    text = "text"
    image = "image"
    system = "system"


class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    conversation_id: str = Field(foreign_key="conversations.id")
    sender_id: str = Field(foreign_key="users.id")
    message: str
    message_type: MessageType = Field(default=MessageType.text, sa_column=Column(String, nullable=False))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    edited_at: datetime | None = Field(default=None, nullable=True)
    is_edited: bool = Field(default=False)
    reply_to_id: str | None = Field(default=None, foreign_key="messages.id", nullable=True)
    deleted_at: datetime | None = Field(default=None, nullable=True)
