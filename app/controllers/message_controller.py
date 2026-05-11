from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select
from datetime import datetime, timezone


from ..schemas.message_schema import MessageRead, CreateMessage, UpdateMessage
from ..models.messages import Message, MessageType
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
from ..utils.permission_helpers import ensure_conversation, ensure_message


router = APIRouter()


# send a message 
@router.post("/conversations/{conversation_id}/messages")
async def create_message(
    conversation_id: str,
    payload: CreateMessage,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    ensure_conversation(conversation_id, current_user.id, session)

    if payload.reply_to_id:
        message_exist = ensure_message(payload.reply_to_id, conversation_id, current_user.id, session)
    
    message = Message(
        **payload.model_dump(),
        conversation_id=conversation_id,
        sender_id=current_user.id,
        created_at=datetime.now(timezone.utc)
    )

    session.add(message)
    session.commit()
    session.refresh(message)

    return api_response(
        data=MessageRead.model_validate(message),
        message="Message created successfully"
    )


# get conversation messages
@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    limit: int = Query(10, le=100),
    offset: int = 0
):
    ensure_conversation(conversation_id, current_user.id, session)

    messages = session.exec(
        select(Message)
        .where(
            Message.conversation_id == conversation_id,
            Message.deleted_at == None
        )
        .order_by(Message.created_at.asc())
        .offset(offset)
        .limit(limit)
    ).all()
    
    return api_response(
        data=[MessageRead.model_validate(m) for m in messages],
        message="Message retrieved successfully"
    )


# update message 
@router.patch("/conversations/{conversation_id}/messages/{message_id}")
async def update_message(
    conversation_id: str,
    message_id: str,
    payload: UpdateMessage,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    ensure_conversation(conversation_id, current_user.id, session)

    existing = ensure_message(message_id, conversation_id, current_user.id, session)

    if existing.sender_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only modify your own messages")

    if existing.deleted_at:
        raise HTTPException(status_code=400, detail="Cannot edit deleted message")
    
    update_data = payload.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(existing, key, value)

    existing.edited_at = datetime.now(timezone.utc)
    existing.is_edited = True
    
    session.add(existing)
    session.commit()
    session.refresh(existing)

    return api_response(data=MessageRead.model_validate(existing), message = "Message updated successfully")


# message soft delete 
@router.delete("/conversations/{conversation_id}/messages/{message_id}")
async def delete_message(
    conversation_id: str,
    message_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    ensure_conversation(conversation_id, current_user.id, session)

    existing = ensure_message(message_id, conversation_id, current_user.id, session)

    if existing.sender_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only modify your own messages")

    if existing.deleted_at:
        raise HTTPException(status_code=400, detail="Message already deleted")
    
    existing.deleted_at = datetime.now(timezone.utc)
    existing.is_edited = False
    
    session.add(existing)
    session.commit()

    return api_response(message = "Message deleted successfully")