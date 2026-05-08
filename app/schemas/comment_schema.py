from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class CreateComment(BaseModel):
    message: str


class UpdateComment(BaseModel):
    message: Optional[str] = None


class CommentRead(BaseModel):
    id: str
    ticket_id: str
    user_id: str
    message: str
    created_at: datetime
    edited_at: Optional[datetime] = None

    class Config:
        from_attributes = True