import uuid
from sqlmodel import SQLModel, Field
from pydantic import EmailStr
from enum import Enum

class Role (str, Enum):
    admin = "admin"
    user = "user"

class Specialty(str, Enum):
    backend = "backend"
    frontend = "frontend"
    qa = "qa"
    devops = "devops"

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str
    email: EmailStr = Field(index=True, unique=True)
    password: str
    role: Role
    specialty: Specialty
    is_active: bool