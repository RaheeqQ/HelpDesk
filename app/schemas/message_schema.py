from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from ..models.messages import MessageType


class CreateMessage(BaseModel):
    message: str
    message_type: MessageType = MessageType.text
    reply_to_id: str | None = None


class UpdateMessage(BaseModel):
    message: str


class MessageRead(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    message: str
    message_type: MessageType
    created_at: datetime
    edited_at: datetime | None
    is_edited: bool
    reply_to_id: str | None
    deleted_at: datetime | None

    class Config:
        from_attributes = True