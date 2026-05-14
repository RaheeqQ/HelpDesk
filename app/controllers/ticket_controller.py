from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select
from sqlalchemy import or_


from ..schemas.ticket_schema import CreateTicket, UpdateTicket, TicketRead
from ..models.sprint import Sprint, SprintStatus
from ..models.users import User
from ..models.project import Project
from ..models.project_members import ProjectMember
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
from fastapi import BackgroundTasks
from ..tasks.ticket_tasks import notify_project_members


router = APIRouter()

# shared filter , sort and pagination function
def _build_ticket_query(
    base_query,
    status: TicketStatus | None,
    ticket_type: TicketType | None,
    priority: int | None,
    sort_by: str | None,
    order: str,
    user_type: str | None,
    user_id: str,
    limit: int,
    offset: int,
):
    if status:
        base_query = base_query.where(Ticket.status == status)
    if ticket_type:
        base_query = base_query.where(Ticket.type == ticket_type)
    if priority is not None:
        base_query = base_query.where(Ticket.priority == priority)

    if sort_by == "priority":
        base_query = base_query.order_by(
            Ticket.priority.desc() if order == "desc" else Ticket.priority
        )
    elif sort_by == "created_at":
        base_query = base_query.order_by(
            Ticket.created_at.desc() if order == "desc" else Ticket.created_at
        )
    
    if user_type == "reporter":
        base_query = base_query.where(Ticket.reporter_id == user_id)
    elif user_type == "assignee":
        base_query = base_query.where(Ticket.assignee_id == user_id)

    return base_query.offset(offset).limit(limit)


_ALLOWED_PARENT: dict[TicketType, TicketType | None] = {
    TicketType.epic:    None,
    TicketType.task:    TicketType.epic,
    TicketType.story:   TicketType.epic,
    TicketType.feature: TicketType.epic,
    TicketType.request: TicketType.epic,
    TicketType.bug:     TicketType.task,
}


def _validate_hierarchy(ticket_type: TicketType, parent: Ticket | None) -> None:
    allowed_parent_type = _ALLOWED_PARENT.get(ticket_type)

    if ticket_type == TicketType.epic and parent is not None:
        raise HTTPException(status_code=400, detail="Epic cannot have a parent")

    if allowed_parent_type is not None and parent is None:
        raise HTTPException(
            status_code=400,
            detail=f"{ticket_type.value} must belong to a {allowed_parent_type.value}"
        )

    if parent is not None and allowed_parent_type is not None:
        if parent.type != allowed_parent_type:
            raise HTTPException(
                status_code=400,
                detail=f"{ticket_type.value} must belong to a {allowed_parent_type.value}, not a {parent.type.value}"
            )


def _validate_dates(start_date, due_date) -> None:
    if start_date and due_date and due_date < start_date:
        raise HTTPException(status_code=400, detail="Due date must be greater than or equal to start date")


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
    
    tickets_data = [
        {
            "ticket": TicketRead.model_validate(ticket),
            "project_title": title
        }
        for ticket, title in tickets
    ]

    return api_response(data = tickets_data, message = "All tickets retrieved successfully")


# get or filter or sort project tickets
@router.get("/projects/{project_id}/tickets")
async def get_filter_sort_tickets(
    project_id: str,
    ticket_type: TicketType | None = Query(None),
    status: TicketStatus | None = Query(None),
    priority: int | None = Query(None, ge=0, le=5),
    sort_by: str | None = Query(None, pattern="^(priority|created_at)$"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    user_type: str | None = Query(None, pattern="^(reporter|assignee)$"),
    limit: int = Query(10, le=100),
    offset: int = Query(0),
    session: Session = Depends(get_session),
    _: Project = Depends(require_project_member),
    current_user: User = Depends(get_current_user)
):
    query = _build_ticket_query(
        select(Ticket)
        .where(Ticket.project_id == project_id),
        status, ticket_type, priority, sort_by, order, user_type, current_user.id, limit, offset
    )

    tickets = session.exec(query).all()

    return api_response(
        data=[TicketRead.model_validate(t) for t in tickets],
        message="Tickets retrieved successfully"
    )


# search ticket (full text search)
@router.get("/projects/{project_id}/tickets/search")
async def search_ticket(
    project_id: str,
    q: str,
    session: Session = Depends(get_session),
    _: Project = Depends(require_project_member)
):
    tickets = session.exec(
        select(Ticket)
        .where(
            Ticket.project_id == project_id,
            or_(
                Ticket.summary.ilike(f"%{q}%"),
                Ticket.description.ilike(f"%{q}%")
            )
        )
    ).all()

    return api_response(
        data=[TicketRead.model_validate(t) for t in tickets],
        message="Tickets retrieved successfully"
    )


# get ticket details
@router.get("/projects/{project_id}/tickets/{ticket_id}")
async def get_ticket_details(
    project_id: str,
    ticket_id: str,
    session: Session = Depends(get_session),
    project: Project = Depends(require_project_member)
):
    ticket = session.get(Ticket, ticket_id)

    if not ticket or ticket.project_id != project_id:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket_data = {
        "ticket": TicketRead.model_validate(ticket),
        "project_title": project.title
    }

    return api_response(
        data=ticket_data,
        message="Ticket details retrieved successfully"
    )


# get ticket's subtickets
@router.get("/projects/{project_id}/tickets/{ticket_id}/subtickets")
async def get_ticket_subtickets(
    project_id: str,
    ticket_id: str,
    session: Session = Depends(get_session),
    _: Project = Depends(require_project_member)
):
    ticket = session.get(Ticket, ticket_id)

    if not ticket or ticket.project_id != project_id:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    subtickets = session.exec(
        select(Ticket)
        .where(
            Ticket.project_id == project_id,
            Ticket.parent_id == ticket_id
        )
    ).all()

    return api_response(
        data=[TicketRead.model_validate(t) for t in subtickets],
        message="Ticket subtickets retrieved successfully"
    )


# create ticket (user - member)
@router.post("/projects/{project_id}/tickets")
async def create_ticket(
    project_id: str,
    ticket: CreateTicket,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
    _: Project = Depends(require_project_member)
):
    if ticket.assignee_id:
        assignee = session.exec(
            select(ProjectMember)
            .where(
                ProjectMember.user_id == ticket.assignee_id,
                ProjectMember.project_id == project_id
            )
        ).first()
        if not assignee:
            raise HTTPException(status_code=400, detail="Assignee is not a member of this project")

    if ticket.parent_id:
        parent = session.get(Ticket, ticket.parent_id)
        if not parent or parent.project_id != project_id:
            raise HTTPException(status_code=404, detail="Parent ticket not found in this project")
        _validate_hierarchy(ticket.type, parent)

    _validate_dates(ticket.start_date, ticket.due_date)

    new_ticket = Ticket(
        **ticket.model_dump(),
        project_id=project_id,
        reporter_id=user.id,
        status=TicketStatus.open
    )

    session.add(new_ticket)
    session.commit()
    session.refresh(new_ticket)

    members = session.exec(
        select(User.email)
        .join(ProjectMember, ProjectMember.user_id == User.id)
        .where(ProjectMember.project_id == project_id)
    ).all()

    emails = [m for m in members]
    
    background_tasks.add_task(
        notify_project_members,
        emails,
        new_ticket.summary
    )

    return api_response(
        data=TicketRead.model_validate(new_ticket),
        message="Ticket created successfully"
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

    return api_response(message="Ticket added to sprint successfully")


# assign parent to ticket
@router.put("/projects/{project_id}/tickets/{ticket_id}/parent")
async def assign_parent_to_ticket(
    project_id: str,
    ticket_id: str,
    parent_id: str,
    session: Session = Depends(get_session),
    _: Project = Depends(require_project_member)
):
    if ticket_id == parent_id:
        raise HTTPException(status_code=400, detail="Ticket cannot be its own parent")

    ticket = session.get(Ticket, ticket_id)
    parent = session.get(Ticket, parent_id)

    if not ticket or ticket.project_id != project_id:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if not parent or parent.project_id != project_id:
        raise HTTPException(status_code=404, detail="Parent not found")

    if ticket.parent_id:
        raise HTTPException(status_code=400, detail="Ticket already has a parent")
    
    if parent.sprint_id and ticket.sprint_id:
        if parent.sprint_id != ticket.sprint_id:
            raise HTTPException(
                status_code=400,
                detail="Parent and child must belong to same sprint"
            )

    _validate_hierarchy(ticket.type, parent)

    ticket.parent_id = parent_id
    ticket.updated_at = datetime.now(timezone.utc)

    session.add(ticket)
    session.commit()
    session.refresh(ticket)

    return api_response(message="Parent assigned to ticket successfully")


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

    return api_response(message="Ticket moved to backlog successfully")


# remove parent from ticket
@router.delete("/projects/{project_id}/tickets/{ticket_id}/parent")
async def remove_parent_from_ticket(
    project_id: str,
    ticket_id: str,
    session: Session = Depends(get_session),
    _: Project = Depends(require_project_member)
):
    ticket = session.get(Ticket, ticket_id)

    if not ticket or ticket.project_id != project_id:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.parent_id = None
    ticket.updated_at = datetime.now(timezone.utc)

    session.add(ticket)
    session.commit()
    session.refresh(ticket)

    return api_response(message="Parent removed from ticket successfully")


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
        message="Sprint tickets retrieved successfully"
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
            Ticket.sprint_id == None,
            Ticket.parent_id == None
        )
    ).all()

    return api_response(
        data= [TicketRead.model_validate(t) for t in tickets],
        message= "Backlog retrieved successfully"
    )


# update ticket 
@router.patch("/projects/{project_id}/tickets/{ticket_id}")
async def update_ticket(
    project_id: str,
    ticket_id: str,
    update_ticket: UpdateTicket,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    ticket = session.get(Ticket, ticket_id)

    if not ticket or ticket.project_id != project_id:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if ticket.status == TicketStatus.done:
        raise HTTPException(status_code=400, detail="Cannot modify a closed (done) ticket")

    is_reporter = current_user.id == ticket.reporter_id
    is_assignee = ticket.assignee_id == current_user.id
    if not is_reporter and not is_assignee:
        raise HTTPException(status_code=403, detail="Only the assigned user or the reporter can update this ticket")

    if update_ticket.status is not None:
        ticket.status = update_ticket.status
        if ticket.status == TicketStatus.done:
            ticket.completed_at = datetime.now(timezone.utc)
        else:
            ticket.completed_at = None
    if update_ticket.priority is not None:
        ticket.priority = update_ticket.priority 
    if update_ticket.summary is not None:
        ticket.summary = update_ticket.summary
    if update_ticket.description is not None:
        ticket.description = update_ticket.description
    if update_ticket.assignee_id is not None:
        assignee = session.exec(
            select(ProjectMember)
            .where(
                ProjectMember.user_id == update_ticket.assignee_id,
                ProjectMember.project_id == project_id   
            )
        ).first()

        if not assignee:
            raise HTTPException(status_code=400, detail="assignee not in this project")
        
        ticket.assignee_id = update_ticket.assignee_id
    if update_ticket.is_flagged is not None:
        ticket.is_flagged = update_ticket.is_flagged

    new_start = update_ticket.start_date if update_ticket.start_date is not None else ticket.start_date
    new_due   = update_ticket.due_date   if update_ticket.due_date   is not None else ticket.due_date
    _validate_dates(new_start, new_due)

    if update_ticket.due_date is not None:
        ticket.due_date = update_ticket.due_date
    if update_ticket.start_date is not None:
        ticket.start_date = update_ticket.start_date
    
    ticket.updated_at = datetime.now(timezone.utc)

    session.add(ticket)
    session.commit()
    session.refresh(ticket)

    return api_response(
        data=TicketRead.model_validate(ticket), 
        message="Ticket updated successfully"
    )


# delete ticket
@router.delete("/projects/{project_id}/tickets/{ticket_id}")
async def delete_ticket(
    project_id: str,
    ticket_id: str,
    session: Session = Depends(get_session),
    _: Project = Depends(require_project_owner)
):
    ticket = session.get(Ticket, ticket_id)

    if not ticket or ticket.project_id != project_id:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # check for subticket
    subticket = session.exec(
        select(Ticket)
        .where(
            Ticket.project_id == project_id,
            Ticket.parent_id == ticket_id
        )
    ).first()

    if subticket:
        raise HTTPException(status_code=400, detail="Cannot delete ticket with subticket")

    session.delete(ticket)
    session.commit()

    return api_response(message="Ticket deleted successfully")