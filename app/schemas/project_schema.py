from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class CreateProject(BaseModel):
    title: str
    description: str


class UpdateProject(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class ProjectRead(BaseModel):
    id: str
    title: str
    owner_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class AssignedProjectRead(BaseModel):
    project: ProjectRead
    role: str
