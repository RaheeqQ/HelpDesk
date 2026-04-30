from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select


from ..schemas.users_schema import CreateUser
from ..models.users import User
from ..db.database import get_session
from ..utils.response_wrapper import api_response
from ..security.auth import (
    create_access_token,
    hash_password,
    verify_password
)
from fastapi.security import OAuth2PasswordRequestForm


router = APIRouter()


# create user (registration)
@router.post("/users/")
async def create_user(
    user: CreateUser, 
    session: Session = Depends(get_session)
):
    existing = session.exec(
        select(User).where(User.email == user.email)
    ).first()

    if existing:
        raise HTTPException(status_code = 400, detail = "Email already registered")
    
    new_user = User(
        **user.model_dump(exclude={"password"}),
        password=hash_password(user.password)
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    return api_response(data = new_user, message = "User created successfully")


# user login
@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    session: Session = Depends(get_session)
):
    user = session.exec(
        select(User).where(User.email == form_data.username)
    ).first()

    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token_data = {
        "sub": str(user.id),
        "email": user.email
    }

    access_token = create_access_token(token_data)

    return {"access_token": access_token, "token_type": "bearer"}