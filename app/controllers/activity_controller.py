from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select
from ..models.activity_log import ActivityLog
from ..models.project import Project
from ..models.users import User
from ..db.database import get_session
from ..utils.response_wrapper import api_response
from ..security.auth import get_current_user, require_project_member
from ..schemas.activity_log_schema import ActivityLogRead


router = APIRouter()


@router.get("/projects/{project_id}/activity")
async def get_project_activity(
    project_id: str,
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
    _: Project = Depends(require_project_member)
):  
    activities = session.exec(
        select(ActivityLog)
        .where(ActivityLog.project_id == project_id)
        .order_by(ActivityLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    total = session.exec(
        select(ActivityLog)
        .where(ActivityLog.project_id == project_id)
    ).all().__len__()

    return api_response(
        data={
            "activities": [ActivityLogRead.model_validate(a) for a in activities],
            "total": total
        },
        message="Project activity retrieved successfully"
    )


@router.get("/projects/{project_id}/tickets/{ticket_id}/activity")
async def get_ticket_activity(
    project_id: str,
    ticket_id: str,
    session: Session = Depends(get_session),
    _: Project = Depends(require_project_member)
):  
    activities = session.exec(
        select(ActivityLog)
        .where(
            ActivityLog.project_id == project_id,
            ActivityLog.entity_id == ticket_id
        )
        .order_by(ActivityLog.created_at.desc())
    ).all()

    return api_response(
        data=[ActivityLogRead.model_validate(a) for a in activities],
        message="Ticket activity retrieved successfully"
    )
