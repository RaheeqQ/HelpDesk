from sqlmodel import SQLModel, Field
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, ForeignKey, String


class SprintStatus(str, Enum):
    planned = "planned"
    active = "active"
    completed = "completed"


class Sprint(SQLModel, table=True):
    __tablename__ = "sprints"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(sa_column=Column(String, ForeignKey("project.id", ondelete="CASCADE"), nullable=False, index=True))
    name: str
    status: SprintStatus = Field(default=SprintStatus.planned, sa_column=Column(String, nullable=False, index=True))
    goal: str 
    start_date: datetime | None = None
    end_date: datetime | None = None