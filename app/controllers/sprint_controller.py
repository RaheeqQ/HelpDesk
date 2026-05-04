from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select


from ..schemas.sprint_schema import CreateSprint, UpdateSprint, SprintRead
from ..models.sprint import Sprint
from ..models.users import User
from ..models.project import Project
from ..models.project_members import ProjectMember
from ..db.database import get_session
from ..utils.response_wrapper import api_response
from datetime import datetime, timezone
from ..security.auth import (
    get_current_user,
    require_admin,
    require_project_owner,
    require_project_member
)


router = APIRouter()


# get all sprints (admin)
@router.get("/sprints/")
async def get_all_sprints(
    session: Session = Depends(get_session),
    limit: int = Query(10, le=100),
    offset: int = 0,
    _: User = Depends(require_admin)
):
    sprints = session.exec(
        select(Sprint)
        .offset(offset)
        .limit(limit)
    ).all()

    if not sprints: 
        raise HTTPException(status_code = 404, detail = "Sprints not found")
    
    sprints_data = [SprintRead.model_validate(s) for s in sprints]
    return api_response(data = sprints_data, message = "All sprints retrieved")


# get user's projects (users)
@router.get("/projects/{project_id}/sprints")
async def get_project_sprints(
    project: Project = Depends(require_project_member),
    session: Session = Depends(get_session),
    limit: int = Query(10, le=100),
    offset: int = 0,
):
    sprints = session.exec(
        select(Sprint)
        .where(Sprint.project_id == project.id)
        .offset(offset)
        .limit(limit)
    ).all()

    if not sprints:
        raise HTTPException(status_code=404, detail="No sprints found")

    result = [
        {
            "sprint": SprintRead.model_validate(s).model_dump(),
            "project_title": project.title
        } 
        for s in sprints
    ]
    return api_response(data=result, message="Project sprints retrieved")


# create sprint (users - owner)
@router.post("/projects/{project_id}/sprints")
async def create_project_sprints(
    project_id: str,
    sprint: CreateSprint,
    session: Session = Depends(get_session),
    _: Project = Depends(require_project_owner)
):
    existing = session.exec(
        select(Sprint)
        .where(
            Sprint.name == sprint.name,
            Sprint.project_id == project_id
        )
    ).first()

    if existing:
        raise HTTPException(status_code = 400, detail = "Sprint already registered")
    
    if sprint.start_date >= sprint.end_date:
        raise HTTPException(status_code = 400, detail = "Sprint start date must be less than end date")
    
    now = datetime.now(timezone.utc)
    start_date_aware = sprint.start_date.replace(tzinfo=timezone.utc) if sprint.start_date.tzinfo is None else sprint.start_date
    end_date_aware = sprint.end_date.replace(tzinfo=timezone.utc) if sprint.end_date.tzinfo is None else sprint.end_date
    
    if start_date_aware < now or end_date_aware < now:
        raise HTTPException(status_code = 400, detail = "Sprint start date or end date cannot be in the past")
    
    new_sprint = Sprint(**sprint.model_dump(), project_id=project_id)

    session.add(new_sprint)
    session.commit()
    session.refresh(new_sprint)

    return api_response(data = new_sprint, message = "Sprint created successfully")


# update sprint (users - owner)
@router.put("/projects/{project_id}/sprints/{sprint_id}")
async def update_project_sprint(
    project_id: str,
    sprint_id: str,
    sprint: UpdateSprint,
    session: Session = Depends(get_session),
    _: Project = Depends(require_project_owner)
):
    existing = session.exec(
        select(Sprint)
        .where(
            Sprint.id == sprint_id,
            Sprint.project_id == project_id
        )
    ).first()

    if not existing: 
        raise HTTPException(status_code = 404, detail = "Sprint not found")
    
    update_data = sprint.model_dump(exclude_unset=True)

    start_date = update_data.get('start_date', existing.start_date)
    end_date = update_data.get('end_date', existing.end_date)
    
    if start_date and end_date and start_date >= end_date:
        raise HTTPException(status_code=400, detail="Sprint start date must be less than end date")

    for key, value in update_data.items():
        setattr(existing, key, value)
    
    session.add(existing)
    session.commit()
    session.refresh(existing)

    return api_response(data = existing, message = "Sprint updated successfully")


# delete sprint (users - owner) 
@router.delete("/projects/{project_id}/sprints/{sprint_id}")
async def delete_project_sprint(
    project_id: str,
    sprint_id: str,
    session: Session = Depends(get_session),
    _: Project = Depends(require_project_owner)
):
    existing = session.exec(
        select(Sprint)
        .where(
            Sprint.id == sprint_id,
            Sprint.project_id == project_id
        )
    ).first()

    if not existing:
        raise HTTPException(status_code = 404, detail = "Sprint not found")
    
    session.delete(existing)
    session.commit()

    return api_response(message=f"Sprint {existing.name} deleted successfully")