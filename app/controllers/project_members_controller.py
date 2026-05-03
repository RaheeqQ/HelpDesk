from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select


from ..schemas.project_members_schema import CreateMember, UpdateMember
from ..models.project_members import ProjectMember, Role
from ..models.project import Project
from ..models.users import User
from ..db.database import get_session
from ..utils.response_wrapper import api_response
from ..security.auth import (
    get_current_user,
    require_project_owner,
    require_project_member
)


router = APIRouter()


# get project members (any project member or owner)
@router.get("/projects/{project_id}/members")
async def get_project_members(
    project_id: str,
    session: Session = Depends(get_session),
    _: Project = Depends(require_project_member)
):
    rows = session.exec(
        select(
            ProjectMember,
            User.name,
            User.email,
            User.specialty
        )
        .join(User, User.id == ProjectMember.user_id)
        .where(ProjectMember.project_id == project_id)
    ).all()

    members = [
        {
            **member.model_dump(),
            "name": name,
            "email": email,
            "specialty": specialty,
        }
        for member, name, email, specialty in rows
    ]

    return api_response(data=members, message="Project members retrieved")


# create project member (users - owner)
@router.post("/projects/{project_id}/members")
async def create_project_member(
    project_id: str,
    member: CreateMember, 
    session: Session = Depends(get_session),
    _: Project = Depends(require_project_owner)
):
    user = session.get(User, member.user_id)

    if not user:
        raise HTTPException(404, "User not found")

    existing = session.exec(
        select(ProjectMember)
        .where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == member.user_id
        )
    ).first()

    if existing:
        raise HTTPException(status_code = 400, detail = "User already in the project")
    
    new_member = ProjectMember(
        user_id=member.user_id,
        role=member.role,
        project_id=project_id
    )

    session.add(new_member)
    session.commit()
    session.refresh(new_member)

    return api_response(
        data = new_member, 
        message = "Member created successfully"
    )


# update member (users - owner)
@router.put("/projects/{project_id}/members/{user_id}")
async def update_project_member(
    project_id: str,
    user_id: str,
    member_update: UpdateMember,
    session: Session = Depends(get_session),
    _: Project = Depends(require_project_owner)
):
    member = session.exec(
        select(ProjectMember)
        .where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        )
    ).first()

    if not member:
        raise HTTPException(status_code = 404, detail = "Member not found")
    
    update_data = member_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(member, key, value)

    session.add(member)
    session.commit()
    session.refresh(member)

    return api_response(data = member, message = "Role updated successfully")


# delete member (users - owner)
@router.delete("/projects/{project_id}/members/{user_id}")
async def remove_member(
    project_id: str,
    user_id: str,
    session: Session = Depends(get_session),
    _: Project = Depends(require_project_owner)
):
    member = session.exec(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        )
    ).first()

    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    if member.role == Role.teamlead:
        raise HTTPException(400, "Cannot remove team lead")

    session.delete(member)
    session.commit()

    return api_response(message="Member removed")