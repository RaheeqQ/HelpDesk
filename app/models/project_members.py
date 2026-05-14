from sqlmodel import SQLModel, Field
from enum import Enum
from datetime import datetime, timezone
from sqlalchemy import Column, ForeignKey, String

class MemberRole(str, Enum):
    owner = "owner"
    teamlead = "teamlead"
    member = "member"
    viewer = "viewer"


class ProjectMember(SQLModel, table=True):
    __tablename__="project_members"

    user_id: str = Field(sa_column=Column(String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True))
    project_id: str = Field(sa_column=Column(String, ForeignKey("project.id", ondelete="CASCADE"), primary_key=True))
    role: MemberRole = Field(default=MemberRole.member, sa_column=Column(String, nullable=False, index=True))
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))