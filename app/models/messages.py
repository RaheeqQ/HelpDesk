from sqlmodel import SQLModel, Field
import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, ForeignKey, String


class MessageType(str, Enum):
    text = "text"
    image = "image"
    system = "system"


class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    conversation_id: str = Field(sa_column=Column(String, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True))
    sender_id: str = Field(sa_column=Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True))
    message: str
    message_type: MessageType = Field(default=MessageType.text, sa_column=Column(String, nullable=False))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    edited_at: datetime | None = Field(default=None, nullable=True)
    is_edited: bool = Field(default=False)
    reply_to_id: str | None = Field(sa_column=Column(String, ForeignKey("messages.id", ondelete="SET NULL"), nullable=True, index=True))
    deleted_at: datetime | None = Field(default=None, nullable=True)
