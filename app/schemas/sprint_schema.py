from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from ..models.sprint import SprintStatus


class CreateSprint(BaseModel):
    name: str
    goal: str


class UpdateSprint(BaseModel):
    name: Optional[str] = None
    goal: Optional[str] = None


class SprintRead(BaseModel):
    id: str
    name: str
    goal: str
    status: SprintStatus
    start_date: Optional[datetime]
    end_date: Optional[datetime]

    class Config:
        from_attributes = True