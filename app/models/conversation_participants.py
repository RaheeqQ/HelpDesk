from sqlmodel import SQLModel, Field
from sqlalchemy import Column, ForeignKey, String
from datetime import datetime, timezone


class ConversationParticipant(SQLModel, table=True):
    __tablename__ = "conversation_participants"

    conversation_id: str = Field(sa_column=Column(String, ForeignKey("conversations.id", ondelete="CASCADE"), primary_key=True))
    user_id: str = Field(sa_column=Column(String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True))
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_read_at: datetime | None = Field(default=None, nullable=True)