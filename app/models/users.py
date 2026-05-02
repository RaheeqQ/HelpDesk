import uuid
from sqlmodel import SQLModel, Field
from pydantic import EmailStr
from enum import Enum
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import ENUM

class Role (str, Enum):
    admin = "admin"
    user = "user"

class Specialty(str, Enum):
    backend = "backend"
    frontend = "frontend"
    qa = "qa"
    devops = "devops"


role_enum = ENUM("admin", "user", name="role", create_type=False)
specialty_enum = ENUM("backend", "frontend", "qa", "devops", name="specialty", create_type=False)


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str
    email: EmailStr = Field(index=True, unique=True)
    password: str
    role: Role = Field(sa_column=Column(role_enum))
    specialty: Specialty = Field(sa_column=Column(specialty_enum))
    is_active: bool