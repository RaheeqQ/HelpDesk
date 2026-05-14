from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlmodel import Session
from datetime import datetime, timezone

from ..db.database import get_session
from ..websocket.manager import manager
from ..models.users import User
from ..utils.permission_helpers import ensure_conversation
from ..security.auth import get_current_user_ws
from .message_handlers import(
    handle_send_message, 
    handle_update_message,
    handle_delete_message
)


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

            data = await websocket.receive_json()

            event = data.get("event")

            if event == "send_message":
                await handle_send_message(data, conversation_id, current_user, session)

            elif event == "update_message":
                await handle_update_message(data, conversation_id, current_user, session)
                
            elif event == "delete_message":
                await handle_delete_message(data, conversation_id, current_user, session)

    except WebSocketDisconnect:
        manager.disconnect(conversation_id, current_user.id)