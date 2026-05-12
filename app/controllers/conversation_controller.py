from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from sqlalchemy.orm import aliased
from datetime import datetime, timezone


from ..schemas.conversation_schema import(
    ConversationRead, 
    CreateDirectConversation, 
    CreateGroupConversation,
    RenameConversation,
    AddParticipant
)
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
from ..utils.permission_helpers import ensure_conversation, ensure_participant

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


# get user conversations
@router.get("/projects/{project_id}/conversations")
async def get_conversations(
    project_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    _: Project = Depends(require_project_member)
):
    conversations = session.exec(
        select(Conversation)
        .join(
            ConversationParticipant,
            ConversationParticipant.conversation_id == Conversation.id
        )
        .where(
            Conversation.project_id == project_id,
            ConversationParticipant.user_id == current_user.id
        )
        .order_by(Conversation.created_at.desc())
    ).all()

    return api_response(
        data=[
            ConversationRead.model_validate(c).model_dump(mode="json")
            for c in conversations
        ],
        message="Conversations retrieved successfully"
    )


# change group name
@router.patch("/conversations/{conversation_id}/rename")
async def rename_group_conversation(
    conversation_id: str,
    payload: RenameConversation,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    conversation = ensure_conversation(conversation_id, current_user.id, session)

    if conversation.conversation_type != ConversationType.group:
        raise HTTPException(status_code=400, detail="Only groups can be renamed")

    conversation.title = payload.title
    conversation.updated_at = datetime.now(timezone.utc)

    session.add(conversation)
    session.commit()
    session.refresh(conversation)

    return api_response(
        data=ConversationRead.model_validate(conversation),
        message="Conversation renamed successfully"
    )


# add new participant
@router.post("/conversations/{conversation_id}/participants")
async def add_participant(
    conversation_id: str,
    payload: AddParticipant,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    conversation = ensure_conversation(conversation_id, current_user.id, session)

    if conversation.conversation_type != ConversationType.group:
        raise HTTPException(status_code=400, detail="Only groups support participants")

    exists = session.exec(
        select(ConversationParticipant)
        .where(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == payload.user_id
        )
    ).first()

    if exists:
        raise HTTPException(status_code=400, detail="User already exists in group")

    participant = ConversationParticipant(
        conversation_id=conversation_id,
        user_id=payload.user_id,
        updated_at = datetime.now(timezone.utc)
    )

    session.add(participant)
    session.commit()

    return api_response(
        message="Participant added successfully"
    )


# remove participant
@router.delete("/conversations/{conversation_id}/participants/{user_id}")
async def remove_participant(
    conversation_id: str,
    user_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    conversation = ensure_conversation(conversation_id, current_user.id, session)

    if conversation.conversation_type != ConversationType.group:
        raise HTTPException(status_code=400, detail="Only groups support participants")

    participant = ensure_participant(conversation_id, user_id, session)

    session.delete(participant)
    session.commit()

    return api_response(message="Participant removed successfully")


# leave group 
@router.delete("/conversations/{conversation_id}/leave")
async def leave_conversation(
    conversation_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    participant = ensure_participant(conversation_id, current_user.id, session)

    session.delete(participant)
    session.commit()

    return api_response(message="Left conversation successfully")