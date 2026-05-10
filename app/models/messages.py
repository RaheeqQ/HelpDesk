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
    type: MessageType = Field(default=MessageType.text, sa_column=Column(String, nullable=False))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    edited_at: datetime
    is_edited: bool = Field(default=False)

