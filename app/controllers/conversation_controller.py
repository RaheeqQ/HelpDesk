from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from sqlalchemy.orm import aliased


from ..schemas.conversation_schema import ConversationRead, CreateDirectConversation, CreateGroupConversation
from ..models.conversations import Conversation, ConversationType
from ..models.conversation_participants import ConversationParticipant
from ..models.project import Project
from ..models.users import User
from ..models.project_members import ProjectMember
from ..db.database import get_session
from ..utils.response_wrapper import api_response
from ..security.auth import (
    get_current_user,
    require_project_member
)


router = APIRouter()


# create direct conversation
@router.post("/projects/{project_id}/conversations/direct")
async def create_direct_conversation(
    project_id: str,
    payload: CreateDirectConversation,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    _: Project = Depends(require_project_member)
):
    if current_user.id == payload.user_id:
        raise HTTPException(status_code=400, detail="Cannot create conversation with yourself")

    membership = session.exec(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == payload.user_id
        )
    ).first()

    if not membership:
        raise HTTPException(status_code=403, detail="Not a project member")

    participant1 = aliased(ConversationParticipant)
    participant2 = aliased(ConversationParticipant)

    existing = session.exec(
        select(Conversation)
        .join(participant1, participant1.conversation_id == Conversation.id)
        .join(participant2, participant2.conversation_id == Conversation.id)
        .where(
            participant1.user_id == current_user.id,
            participant2.user_id == payload.user_id,
            Conversation.conversation_type == ConversationType.direct,
            Conversation.project_id == project_id
        )
    ).first()

    if existing:
        return api_response(
            data=ConversationRead.model_validate(existing),
            message="Conversation already exists"
        )

    conversation = Conversation(
        project_id=project_id,
        conversation_type=ConversationType.direct,
        created_by=current_user.id
    )

    session.add(conversation)
    session.flush()

    participants = [
        ConversationParticipant(
            conversation_id=conversation.id,
            user_id=current_user.id
        ),
        ConversationParticipant(
            conversation_id=conversation.id,
            user_id=payload.user_id
        )
    ]

    session.add_all(participants)

    session.commit()
    session.refresh(conversation)

    return api_response(
        data=ConversationRead.model_validate(conversation),
        message="Conversation created successfully"
    )


# create group conversation
@router.post("/projects/{project_id}/conversations/group")
async def create_group_conversation(
    project_id: str,
    payload: CreateGroupConversation,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    _: Project = Depends(require_project_member)
):
    all_user_ids = set(payload.user_ids)
    all_user_ids.add(current_user.id)

    memberships = session.exec(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id.in_(all_user_ids)
        )
    ).all()

    if len(memberships) != len(all_user_ids):
        raise HTTPException(status_code=403, detail="Not all users are project members")

    conversation = Conversation(
        project_id=project_id,
        conversation_type=ConversationType.group,
        created_by=current_user.id
    )

    session.add(conversation)
    session.flush()

    participants = [
        ConversationParticipant(
            conversation_id=conversation.id,
            user_id=user_id
        )
        for user_id in all_user_ids
    ]

    session.add_all(participants)

    session.commit()
    session.refresh(conversation)

    return api_response(
        data=ConversationRead.model_validate(conversation),
        message="Conversation created successfully"
    )