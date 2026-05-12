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
            data = await websocket.receive_json()

            try:
                if "message" not in data or not data["message"]:
                    await websocket.send_json({"error": "Missing required field: message"})
                    continue

                message = Message(
                    message=data["message"],
                    message_type=data.get("message_type", MessageType.text),
                    reply_to_id=data.get("reply_to_id"),
                    conversation_id=conversation_id,
                    sender_id=current_user.id,
                    created_at=datetime.now(timezone.utc)
                )
                session.add(message)
                session.commit()
                session.refresh(message)

                await manager.broadcast_message(
                    conversation_id,
                    MessageRead.model_validate(message).model_dump_json()
                )

            except Exception as e:
                session.rollback()
                await websocket.send_json({"error": str(e)})

    except WebSocketDisconnect:
        manager.disconnect(conversation_id, current_user.id)