from typing import Optional
from pydantic import BaseModel
from ..models.project_members import MemberRole


class CreateMember(BaseModel):
    user_id: str 
    role: MemberRole


class UpdateMember(BaseModel):
    role: Optional[MemberRole]


class BulkMemberItem(BaseModel):
    user_id: str
    role: MemberRole


class BulkMembersCreate(BaseModel):
    members: list[BulkMemberItem]