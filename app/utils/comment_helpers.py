from fastapi import HTTPException
from sqlmodel import Session, select
from ..models.tickets import Ticket
from ..models.project_members import ProjectMember, Role


def get_ticket_and_membership(ticket_id: str, user_id: str, session: Session):
    ticket = session.get(Ticket, ticket_id)

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    membership = session.exec(
        select(ProjectMember).where(
            ProjectMember.project_id == ticket.project_id,
            ProjectMember.user_id == user_id
        )
    ).first()

    if not membership:
        raise HTTPException(status_code=403, detail="Not a project member")

    return ticket, membership


def ensure_can_comment(membership: ProjectMember):
    if membership.role == Role.viewer:
        raise HTTPException(status_code=403, detail="Viewer cannot comment")