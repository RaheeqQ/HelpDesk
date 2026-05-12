from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlmodel import Session
from datetime import datetime, timezone

from ..db.database import get_session
from ..websocket.manager import manager
from ..models.users import User
from ..models.messages import Message, MessageType
from ..schemas.message_schema import MessageRead
from ..utils.permission_helpers import ensure_conversation
from ..security.auth import get_current_user_ws


router = APIRouter()


@router.websocket("/ws/conversations/{conversation_id}")
async def conversation_socket(
    websocket: WebSocket,
    conversation_id: str,
    current_user: User = Depends(get_current_user_ws),
    session: Session = Depends(get_session)
):
    ensure_conversation(conversation_id, current_user.id, session)

    await manager.connect(conversation_id, current_user.id, websocket)

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(conversation_id, current_user.id)