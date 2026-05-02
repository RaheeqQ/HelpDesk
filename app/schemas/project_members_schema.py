from typing import Optional
from pydantic import BaseModel
from ..models.project_members import Role


class CreateMember(BaseModel):
    user_id: str 
    role: Role


class UpdateMember(BaseModel):
    role: Optional[Role]