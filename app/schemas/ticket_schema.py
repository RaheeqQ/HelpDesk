from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from ..models.tickets import TicketStatus, TicketType


class CreateTicket(BaseModel):
    summary: str
    type: TicketType
    description: Optional[str] = None
    priority: int
    assignee_id: Optional[str] = None
    is_flagged: bool = False
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    parent_id: Optional[str] = None


class UpdateTicket(BaseModel):
    summary: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TicketStatus] = None
    priority: Optional[int] = None
    is_flagged: Optional[bool] = None
    assignee_id: Optional[str] = None
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None


class TicketRead(BaseModel):
    id: str
    project_id: str
    parent_id: Optional[str] = None
    sprint_id: Optional[str] = None
    summary: str
    type: TicketType
    description: Optional[str] = None
    status: TicketStatus
    priority: int
    assignee_id: Optional[str] = None
    reporter_id: str
    is_flagged: bool
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True