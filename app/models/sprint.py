from sqlmodel import SQLModel, Field
import uuid
from datetime import datetime


class Sprint(SQLModel, table=True):
    __tablename__ = "sprints"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(foreign_key="project.id")
    name: str
    status: str
    goal: str 
    start_date: datetime
    end_date: datetime