from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from ..models.tickets import TicketStatus, TicketType


class CreateTicket(BaseModel):
    summary: str
    type: TicketType
    description: str
    priority: int
    assignee_id: Optional[str] = None
    is_flagged: bool


class UpdateTicket(BaseModel):
    summary: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TicketStatus] = None
    priority: Optional[int] = None
    is_flagged: Optional[bool] = None
    assignee_id: Optional[str] = None


class TicketRead(BaseModel):
    id: str
    summary: str
    description: str
    status: TicketStatus
    priority: int
    start_date: Optional[datetime]
    due_date: Optional[datetime]

    class Config:
        from_attributes = True