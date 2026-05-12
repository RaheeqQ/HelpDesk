import uuid
from sqlmodel import SQLModel, Field
from .users import User
from datetime import datetime, timezone

class Project(SQLModel, table=True):
    __tablename__ = "project"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    title: str
    description: str
    owner_id: str = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))