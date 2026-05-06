from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select


from ..schemas.ticket_schema import CreateTicket, UpdateTicket, TicketRead
from ..models.sprint import Sprint, SprintStatus
from ..models.users import User
from ..models.project import Project
from ..models.tickets import Ticket, TicketStatus, TicketType
from ..db.database import get_session
from ..utils.response_wrapper import api_response
from datetime import datetime, timezone
from ..security.auth import (
    require_admin,
    get_current_user,
    require_project_owner,
    require_project_member
)


router = APIRouter()

# get all tickets (admin)
@router.get("/tickets/")
async def get_all_tickets(
    session: Session = Depends(get_session),
    _: User = Depends(require_admin),
    limit: int = Query(10, le=100),
    offset: int = 0
):
    tickets = session.exec(
        select(
            Ticket, 
            Project.title
        )
        .join(Project, Ticket.project_id == Project.id)
        .offset(offset)
        .limit(limit)
    ).all()

    if not tickets: 
        return []
    
    tickets_data = [
        {
            "ticket": TicketRead.model_validate(ticket),
            "project_title": title
        }
        for ticket, title in tickets
    ]

    return api_response(data = tickets_data, message = "All tickets retrieved")


# get or filter or sort project tickets
@router.get("/projects/{project_id}/tickets")
async def get_filter_sort_tickets(
    project_id: str,
    type: TicketType | None = Query(None),
    status: TicketStatus | None = Query(None),
    priority: int | None = Query(None, ge=0, le=5),
    sort_by: str | None = Query(None, pattern="^(priority|created_at)$"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    limit: int = Query(10, le=100),
    offset: int = 0,
    session: Session = Depends(get_session),
    _: Project = Depends(require_project_member)
):
    query = select(Ticket).where(Ticket.project_id == project_id)

    if type:
        query = query.where(Ticket.type == type)

    if status:
        query = query.where(Ticket.status == status)

    if priority is not None:
        query = query.where(Ticket.priority == priority)

    # sorting
    if sort_by == "priority":
        query = query.order_by(
            Ticket.priority.desc() if order == "desc" else Ticket.priority
        )
    elif sort_by == "created_at":
        query = query.order_by(
            Ticket.created_at.desc() if order == "desc" else Ticket.created_at
        )

    query = query.offset(offset).limit(limit)

    tickets = session.exec(query).all()

    return api_response(
        data=[TicketRead.model_validate(t) for t in tickets],
        message="Tickets retrieved successfully"
    )


# create ticket (user - member)
@router.post("/projects/{project_id}/tickets")
async def create_ticket(
    project_id: str,
    ticket: CreateTicket,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
    _: Project = Depends(require_project_member)
):
    if ticket.assignee_id:
        assignee = session.get(User, ticket.assignee_id)
        if not assignee:
            raise HTTPException(status_code=404, detail="Assignee not found")
    
    new_ticket = Ticket(
        **ticket.model_dump(),
        project_id=project_id,
        reporter_id=user.id,
        status=TicketStatus.open
    )

    session.add(new_ticket)
    session.commit()
    session.refresh(new_ticket)

    return api_response(
        data=TicketRead.model_validate(new_ticket),
        message="Ticket created"
    )


# add ticket to sprint
@router.post("/projects/{project_id}/sprints/{sprint_id}/tickets/{ticket_id}")
async def assign_ticket_to_sprint(
    project_id: str,
    sprint_id: str,
    ticket_id: str,
    session: Session = Depends(get_session),
    _: Project = Depends(require_project_member)
):
    sprint = session.get(Sprint, sprint_id)
    ticket = session.get(Ticket, ticket_id)

    if not sprint or sprint.project_id != project_id:
        raise HTTPException(status_code=404, detail= "Sprint not found")

    if not ticket or ticket.project_id != project_id:
        raise HTTPException(status_code=404, detail= "Ticket not found")
    
    if ticket.sprint_id:
        raise HTTPException(status_code=400, detail= "Ticket already assigned to a sprint")

    if sprint.status != SprintStatus.planned:
        raise HTTPException(status_code=400, detail= "Cannot add tickets to active/completed sprint")

    ticket.sprint_id = sprint_id
    ticket.updated_at = datetime.now(timezone.utc)

    session.add(ticket)
    session.commit()
    session.refresh(ticket)

    return api_response(message="Ticket added to sprint")


# remove ticket from sprint
@router.delete("/projects/{project_id}/sprints/{sprint_id}/tickets/{ticket_id}")
async def remove_ticket_from_sprint(
    project_id: str,
    sprint_id: str,
    ticket_id: str,
    session: Session = Depends(get_session),
    _: Project = Depends(require_project_member)
):
    sprint = session.get(Sprint, sprint_id)
    ticket = session.get(Ticket, ticket_id)

    if not sprint or sprint.project_id != project_id:
        raise HTTPException(status_code=404, detail="Sprint not found")

    if not ticket or ticket.project_id != project_id:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if ticket.sprint_id != sprint_id:
        raise HTTPException(status_code=400, detail="Ticket not in this sprint")

    ticket.sprint_id = None
    ticket.updated_at = datetime.now(timezone.utc)

    session.add(ticket)
    session.commit()
    session.refresh(ticket)

    return api_response(message="Ticket moved to backlog")


# get sprint tickets
@router.get("/projects/{project_id}/sprints/{sprint_id}/tickets")
async def get_sprint_tickets(
    project_id: str,
    sprint_id: str,
    session: Session = Depends(get_session),
    _: Project = Depends(require_project_member)
):
    sprint = session.get(Sprint, sprint_id)

    if not sprint or sprint.project_id != project_id:
        raise HTTPException(status_code=404, detail="Sprint not found")

    tickets = session.exec(
        select(Ticket)
        .where(
            Ticket.project_id == project_id,
            Ticket.sprint_id == sprint_id
        )
    ).all()

    return api_response(
        data=[TicketRead.model_validate(t) for t in tickets],
        message="Sprint tickets retrieved"
    )


# get backlog tickets
@router.get("/projects/{project_id}/backlog")
async def get_backlog(
    project_id: str,
    session: Session = Depends(get_session),
    _: Project = Depends(require_project_member)
):
    tickets = session.exec(
        select(Ticket)
        .where(
            Ticket.project_id == project_id,
            Ticket.sprint_id == None   
        )
    ).all()

    return api_response(
        data= [TicketRead.model_validate(t) for t in tickets],
        message= "Backlog retrieved successfully"
    )