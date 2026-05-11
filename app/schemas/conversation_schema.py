from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from ..models.conversations import ConversationType


class CreateDirectConversation(BaseModel):
    user_id: str


class CreateGroupConversation(BaseModel):
    user_ids: list[str]


class ConversationRead(BaseModel):
    id: str
    project_id: str
    conversation_type: ConversationType
    created_by: str
    created_at: datetime

    class Config:
        from_attributes = True