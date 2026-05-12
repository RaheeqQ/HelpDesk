from sqlmodel import SQLModel, Field
from sqlalchemy import Column, ForeignKey, String
import uuid
from datetime import datetime, timezone


class Attachment(SQLModel, table=True):
    __tablename__ = "attachments"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    ticket_id: str = Field(sa_column=Column(String, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True))
    uploader_id: str = Field(sa_column=Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True))
    filename: str
    file_url: str
    mime_type: str
    file_size: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))