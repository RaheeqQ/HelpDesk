from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select


from ..schemas.sprint_schema import CreateSprint, UpdateSprint, SprintRead
from ..models.sprint import Sprint, SprintStatus
from ..models.users import User
from ..models.project import Project
from ..models.tickets import Ticket
from ..db.database import get_session
from ..utils.response_wrapper import api_response
from datetime import datetime, timezone
from ..security.auth import (
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


# get or filter sprint user's projects (users)
@router.get("/projects/{project_id}/sprints")
async def get_project_sprints(
    project: Project = Depends(require_project_member),
    session: Session = Depends(get_session),
    status: SprintStatus | None = Query(None),
    limit: int = Query(10, le=100),
    offset: int = 0,
):
    query = select(Sprint)

    if status:
        query = query.where(Sprint.status == status)

    query = query.where(Sprint.project_id == project.id)
    query = query.offset(offset)
    query = query.limit(limit)
    
    sprints = session.exec(query).all()

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


# get sprint details
@router.get("/projects/{project_id}/sprints/{sprint_id}")
async def get_project_sprint_details(
    project_id: str,
    sprint_id: str,
    session: Session = Depends(get_session),
    project: Project = Depends(require_project_member)
):
    sprint = session.get(Sprint, sprint_id)

    if not sprint or sprint.project_id != project_id:
        raise HTTPException(status_code=404, detail="Sprint not found")

    sprint_data = {
        "sprint": SprintRead.model_validate(sprint),
        "project_title": project.title
    }
    
    return api_response(
        data=sprint_data,
        message="Sprint details retrieved successfully"
    )


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
    
    new_sprint = Sprint(**sprint.model_dump(), project_id=project_id)

    session.add(new_sprint)
    session.commit()
    session.refresh(new_sprint)

    return api_response(data = SprintRead.model_validate(new_sprint), message = "Sprint created successfully")


# start sprint
@router.post("/projects/{project_id}/sprints/{sprint_id}/start")
async def start_sprint(
    project_id: str,
    sprint_id: str,
    session: Session = Depends(get_session),
    _: Project = Depends(require_project_owner)
):
    sprint = session.get(Sprint, sprint_id)

    if not sprint or sprint.project_id != project_id:
        raise HTTPException(status_code=404, detail="Sprint not found")

    if sprint.status != SprintStatus.planned:
        raise HTTPException(status_code=400, detail="Only planned sprint can be started")
    
    active = session.exec(
        select(Sprint)
        .where(Sprint.project_id == project_id,
               Sprint.status == SprintStatus.active       
        )
    ).first()

    if active:
        raise HTTPException(status_code=400, detail="Another sprint already active")
    
    sprint.status = SprintStatus.active
    sprint.start_date = datetime.now(timezone.utc)

    session.add(sprint)
    session.commit()
    session.refresh(sprint)

    return api_response(
        data=SprintRead.model_validate(sprint),
        message="Sprint started"
    )


# complete sprint
@router.post("/projects/{project_id}/sprints/{sprint_id}/complete")
async def complete_sprint(
    project_id: str,
    sprint_id: str,
    session: Session = Depends(get_session),
    _: Project = Depends(require_project_owner)
):
    sprint = session.get(Sprint, sprint_id)

    if not sprint or sprint.project_id != project_id:
        raise HTTPException(status_code=404, detail="Sprint not found")

    if sprint.status != SprintStatus.active:
        raise HTTPException(status_code=400, detail="Only active sprint can be completed")

    sprint.status = SprintStatus.completed
    sprint.end_date = datetime.now(timezone.utc)

    session.add(sprint)
    session.commit()
    session.refresh(sprint)

    return api_response(
        data=SprintRead.model_validate(sprint),
        message="Sprint completed"
    )


# update sprint (users - owner)
@router.put("/projects/{project_id}/sprints/{sprint_id}")
async def update_project_sprint(
    project_id: str,
    sprint_id: str,
    sprint_update: UpdateSprint,
    session: Session = Depends(get_session),
    _: Project = Depends(require_project_owner)
):
    sprint = session.get(Sprint, sprint_id)

    if not sprint or sprint.project_id != project_id:
        raise HTTPException(status_code=404, detail="Sprint not found")
    
    if sprint.status != SprintStatus.planned:
        raise HTTPException(status_code=400, detail="Only planned sprint can be updated")
    
    update_data = sprint_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(sprint, key, value)
    
    session.add(sprint)
    session.commit()
    session.refresh(sprint)

    return api_response(data = SprintRead.model_validate(sprint), message = "Sprint updated successfully")


# delete sprint (users - owner) 
@router.delete("/projects/{project_id}/sprints/{sprint_id}")
async def delete_project_sprint(
    project_id: str,
    sprint_id: str,
    session: Session = Depends(get_session),
    _: Project = Depends(require_project_owner)
):
    sprint = session.get(Sprint, sprint_id)

    if not sprint or sprint.project_id != project_id:
        raise HTTPException(status_code=404, detail="Sprint not found")
    
    if sprint.status == SprintStatus.active:
        raise HTTPException(status_code=400, detail="Cannot delete active sprint")
    
    tickets = session.exec(
        select(Ticket)
        .where(Ticket.sprint_id == sprint_id)
    ).all()

    for ticket in tickets:
        ticket.sprint_id = None
        session.add(ticket)

    session.delete(sprint)
    session.commit()

    return api_response(message=f"Sprint {sprint.name} deleted successfully")