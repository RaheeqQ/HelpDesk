from ..models.users import Role, Specialty
from typing import Optional
from pydantic import EmailStr, BaseModel


class CreateUser(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Role
    specialty: Specialty
    is_active: bool = True


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    specialty: Optional[Specialty] = None
    is_active: Optional[bool] = None


class UserRead(BaseModel):
    id: str
    name: str
    email: str
    role: Role
    specialty: Specialty

    class Config:
        from_attributes = True