from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select


from ..schemas.users_schema import UserUpdate, UserRead
from ..models.users import User, Role
from ..db.database import get_session
from ..utils.response_wrapper import api_response
from ..security.auth import (
    get_current_user,
    hash_password,
    require_admin
    )


router = APIRouter()


# get all users (admin)
@router.get("/users/")
async def get_users(
    session: Session = Depends(get_session),
    limit: int = Query(10, le=100),
    offset: int = 0,
    _: User = Depends(require_admin),
    ):
    users = session.exec(
        select(User)
        .where(User.is_active == True)
        .offset(offset)
        .limit(limit)
    ).all()
    
    users = [UserRead.model_validate(u) for u in users]
    return api_response(data = users, message = "All users retrieved")


# search users
@router.get("/users/search")
async def search_users(
    query: str,
    session: Session = Depends(get_session),
    limit: int = Query(10, le=100),
    offset: int = 0,
    _: User = Depends(get_current_user),
):
    users = session.exec(
        select(User)
        .where(User.is_active == True)
        .where(
            User.name.ilike(f"%{query}%") |
            User.email.ilike(f"%{query}%")
        )
        .offset(offset)
        .limit(limit)
    ).all()
    
    users = [UserRead.model_validate(u) for u in users]
    return api_response(
        data = {
            "users": users,
            "offset": offset,
            "limit": limit
        }, 
        message = "Users retrieved successfully")


# get current user
@router.get("/users/me")
async def get_me(
    current_user: User = Depends(get_current_user)
):
    return api_response(
        data=UserRead.model_validate(current_user),
        message="Current user retrieved successfully"
    )


# self update
@router.put("/users/me")
async def update_user_me(
    user_update: UserUpdate, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    update_data = user_update.model_dump(exclude_unset=True)

    if "role" in update_data:
            raise HTTPException(status_code=403, detail="Cannot change role")
    
    if "password" in update_data:
        update_data["password"] = hash_password(update_data["password"])
    
    for key, value in update_data.items():
        setattr(current_user, key, value)
    
    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    return api_response(data = current_user, message = "User updated successfully")


# get specific user (admin)
@router.get("/users/{user_id}")
async def get_user(
    user_id: str, 
    session: Session = Depends(get_session), 
    _: User = Depends(require_admin),
):
    user = session.get(User, user_id)

    if not user or not user.is_active:
        raise HTTPException(status_code = 404, detail = "User not found")
    
    return api_response(
        data=UserRead.model_validate(user),
        message = "User retrieved successfully"
    )


# admin update
@router.put("/users/{user_id}")
async def update_user_admin(
    user_id: str, 
    user_update: UserUpdate, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    user = session.get(User, user_id)

    if not user or not user.is_active:
        raise HTTPException(status_code = 404, detail = "User not found")
    
    if current_user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Admins only can edit")
    
    update_data = user_update.model_dump(exclude_unset=True)
    
    if "password" in update_data:
        raise HTTPException(status_code=403, detail="Admin cannot change password here")
    
    for key, value in update_data.items():
        setattr(user, key, value)
    
    session.add(user)
    session.commit()
    session.refresh(user)

    return api_response(data = user, message = "User updated successfully")


# delete specific user
@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    user = session.get(User, user_id)

    if not user or not user.is_active:
        raise HTTPException(status_code = 404, detail = "User not found")
    
    if current_user.id != user_id and current_user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    user.is_active = False
    session.add(user)
    session.commit()

    return api_response(message="User deleted successfully")