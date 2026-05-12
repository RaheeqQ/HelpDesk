from fastapi import HTTPException
from sqlmodel import Session, select
from ..models.project import Project
from ..models.sprint import Sprint
from ..models.tickets import Ticket
from ..models.project_members import ProjectMember, Role
from ..models.conversations import Conversation
from ..models.conversation_participants import ConversationParticipant
from ..models.messages import Message


def ensure_project(project_id: str, user_id: str, session: Session):
    project = session.exec(
        select(Project)
        .where(Project.owner_id == user_id, Project.id == project_id)
    ).first()

    if not project:
        raise HTTPException(status_code = 404, detail = "Project not found")
    
    return project


def ensure_sprint(sprint_id: str, project_id: str, session: Session):
    sprint = session.get(Sprint, sprint_id)

    if not sprint or sprint.project_id != project_id:
        raise HTTPException(status_code=404, detail="Sprint not found")
    
    return sprint


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


def ensure_can_write(membership: ProjectMember):
    if membership.role == Role.viewer:
        raise HTTPException(status_code=403, detail="Insufficient permissions")


def ensure_conversation(conversation_id: str, user_id: str, session: Session):
    existing = session.exec(
        select(Conversation)
        .where(Conversation.id == conversation_id)
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conversation_participant = session.exec(
        select(ConversationParticipant)
        .where(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == user_id
        )
    ).first()

    if not conversation_participant:
        raise HTTPException(status_code=403, detail=f"Not a conversation participant")
    
    return existing
    
def ensure_message(message_id: str, conversation_id: str, user_id: str, session: Session):
    existing = session.exec(
        select(Message)
        .where(
            Message.id == message_id,
            Message.conversation_id == conversation_id,
            Message.deleted_at == None
        )
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Message not found")
    
    return existing