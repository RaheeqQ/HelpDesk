from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class CreateSprint(BaseModel):
    name: str
    status: str
    goal: str 
    start_date: datetime
    end_date: datetime


class UpdateSprint(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    goal: Optional[str] = None
    start_date: Optional[datetime]= None
    end_date: Optional[datetime]= None


class SprintRead(BaseModel):
    name: str
    start_date: datetime
    end_date: datetime

    class Config:
        from_attributes = True