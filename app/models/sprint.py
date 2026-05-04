from sqlmodel import SQLModel, Field
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String


class SprintStatus(str, Enum):
    planned = "planned"
    active = "active"
    completed = "completed"


class Sprint(SQLModel, table=True):
    __tablename__ = "sprints"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(foreign_key="project.id")
    name: str
    status: SprintStatus = Field(default=SprintStatus.planned, sa_column=Column(String, nullable=False))
    goal: str 
    start_date: datetime | None = None
    end_date: datetime | None = None