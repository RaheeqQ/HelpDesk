from sqlmodel import SQLModel, Field
from typing import Optional
import uuid
from enum import Enum
from sqlalchemy import Column, ForeignKey, String
from datetime import datetime, timezone


class TicketType(str, Enum):
    epic = "epic"
    task = "task"
    story = "story"
    feature = "feature"
    request = "request"
    bug = "bug"


class TicketStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    in_review = "in_review"
    done = "done"
    closed = "closed"


class Ticket(SQLModel, table=True):
    __tablename__ = "tickets"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(sa_column=Column(String, ForeignKey("project.id", ondelete="CASCADE"), nullable=False, index=True))
    parent_id: Optional[str] = Field(sa_column=Column(String, ForeignKey("tickets.id", ondelete="SET NULL"), nullable=True))
    sprint_id: Optional[str] = Field(foreign_key="sprints.id", index=True)
    summary: str
    type: TicketType = Field(sa_column=Column(String, nullable=False, index=True))
    description: Optional[str] = None
    status: TicketStatus = Field(default=TicketStatus.open, sa_column=Column(String, nullable=False, index=True))
    priority: int = Field(index=True)
    assignee_id: Optional[str] = Field(sa_column=Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True))
    reporter_id: str = Field(sa_column=Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True))
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    is_flagged: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None