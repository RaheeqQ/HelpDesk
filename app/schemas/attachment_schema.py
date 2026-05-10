from pydantic import BaseModel
from datetime import datetime


class AttachmentRead(BaseModel):
    id: str
    ticket_id: str
    uploader_id: str
    filename: str
    file_url: str
    mime_type: str
    file_size: int
    created_at: datetime

    class Config:
        from_attributes = True