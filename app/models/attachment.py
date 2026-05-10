from sqlmodel import SQLModel, Field
import uuid
from datetime import datetime, timezone


class Attachment(SQLModel, table=True):
    __tablename__ = "attachments"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    ticket_id: str = Field(foreign_key="tickets.id")
    uploader_id: str = Field(foreign_key="users.id")
    filename: str
    file_url: str
    mime_type: str
    file_size: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))