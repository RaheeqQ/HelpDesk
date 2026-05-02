from sqlmodel import SQLModel, Field
from enum import Enum
from datetime import datetime, timezone
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import ENUM

class Role(str, Enum):
    teamlead = "teamlead"
    member = "member"
    viewer = "viewer"


role_enum = ENUM("teamlead", "member", "viewer", name="project_role", create_type=True)


class ProjectMember(SQLModel, table=True):
    __tablename__="project_members"

    user_id: str = Field(foreign_key="users.id", primary_key=True)
    project_id: str = Field(foreign_key="project.id", primary_key=True)
    role: Role = Field(sa_column=Column(role_enum))
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))