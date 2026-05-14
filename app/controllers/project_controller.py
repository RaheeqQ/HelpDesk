from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select


from ..schemas.project_schema import(
    CreateProject, 
    UpdateProject, 
    ProjectRead, 
    AssignedProjectRead
)
from ..models.project import Project
from ..models.users import User
from ..models.project_members import ProjectMember, MemberRole
from ..db.database import get_session
from ..utils.response_wrapper import api_response
from ..security.auth import (
    get_current_user,
    require_admin,
    require_project_member
)
from ..utils.permission_helpers import ensure_project


router = APIRouter()


# get all projects (admin)
@router.get("/projects/")
async def get_all_projects(
    session: Session = Depends(get_session),
    limit: int = Query(10, le=100),
    offset: int = 0,
    _: User = Depends(require_admin)
):
    projects = session.exec(
        select(Project)
        .offset(offset)
        .limit(limit)
    ).all()

    if not projects: 
        raise HTTPException(status_code = 404, detail = "Projects not found")
    
    projects = [ProjectRead.model_validate(p) for p in projects]
    return api_response(data = projects, message = "All projects retrieved")


# get user's projects (users - member)
@router.get("/projects/me")
async def get_my_projects(
    session: Session = Depends(get_session),
    limit: int = Query(10, le=100),
    offset: int = 0,
    current_user: User = Depends(get_current_user)
):
    projects = session.exec(
        select(Project, ProjectMember.role)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .where(ProjectMember.user_id == current_user.id)
        .offset(offset)
        .limit(limit)
    ).all()

    if not projects:
        raise HTTPException(status_code = 404, detail = "Projects not found")

    return api_response(
        data=[AssignedProjectRead(project=ProjectRead.model_validate(p), role=role) for p, role in projects],
        message="All your assigned projects retrieved"
    )


# get project details (users - owner or member)
@router.get("/projects/{project_id}")
async def get_project_details(
    project_id: str,
    session: Session = Depends(get_session),
    _: Project = Depends(require_project_member)
):
    project = session.get(Project, project_id)

    if not project:
        raise HTTPException(status_code = 404, detail = "Project not found")
    
    return api_response(data = project, message = "Project details retrieved successfully")


# create project (users)
@router.post("/projects/")
async def create_project(
    project: CreateProject,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    existing = session.exec(
        select(Project)
        .where(Project.title == project.title, Project.owner_id == current_user.id)
    ).first()

    if existing:
        raise HTTPException(status_code = 400, detail = "Project already registered")
    
    new_project = Project(
        **project.model_dump(),
        owner_id=current_user.id
    )

    session.add(new_project)
    session.commit()
    session.refresh(new_project)

    owner_member = ProjectMember(
        project_id=new_project.id,
        user_id=new_project.owner_id,
        role=MemberRole.owner
    )

    session.add(owner_member)
    session.commit()

    return api_response(data = new_project, message = "Project created successfully")


# update project (users - owner)
@router.put("/projects/{project_id}")
async def update_my_project(
    project_id: str,
    project_update: UpdateProject,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    existing = ensure_project(project_id, current_user.id, session)
    
    update_data = project_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(existing, key, value)
    
    session.add(existing)
    session.commit()
    session.refresh(existing)

    return api_response(data = existing, message = "Project updated successfully")


# delete project (users - owner) 
@router.delete("/projects/{project_id}")
async def delete_my_project(
    project_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    project = ensure_project(project_id, current_user.id, session)
    
    session.delete(project)
    session.commit()

    return api_response(message="Project deleted successfully")