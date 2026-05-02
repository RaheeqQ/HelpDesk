import os
from dotenv import load_dotenv

import bcrypt
import jwt 
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException, Depends
from ..models.users import User, Role
from ..models.project import Project
from sqlmodel import Session, select
from ..db.database import get_session
from ..models.project_members import ProjectMember, Role

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
EXPIRES_MINUTES = int(os.getenv("EXPIRES_MINUTES"))
if not SECRET_KEY or not ALGORITHM:
    raise Exception("Missing JWT configuration")


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")


# password helpers
def hash_password(plain: str):
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str):
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# token helpers
def create_access_token(data: dict) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=EXPIRES_MINUTES)
    payload.update({"exp": expire})

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
        token: str = Depends(oauth2_scheme),
        session: Session = Depends(get_session)
    ):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        user = session.get(User, user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return user

    except jwt.exceptions.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    

def require_admin(
    user: User = Depends(get_current_user)
):
    if user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Admins only")
    return user


def require_project_owner(
    project_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    project = session.exec(
        select(Project)
        .where(Project.id == project_id)
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return project