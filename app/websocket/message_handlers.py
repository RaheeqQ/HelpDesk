from datetime import datetime, timezone
from ..schemas.message_schema import MessageRead
from ..models.messages import Message
from ..utils.permission_helpers import ensure_conversation, ensure_message
from ..websocket.manager import manager


async def handle_send_message(data, conversation_id, current_user, session):
    ensure_conversation(conversation_id, current_user.id, session)

    message_text = data.get("message")
    reply_to_id = data.get("reply_to_id")

    if reply_to_id:
        ensure_message(reply_to_id, conversation_id, current_user.id, session)

    message = Message(
        message=message_text,
        reply_to_id=reply_to_id,
        conversation_id=conversation_id,
        sender_id=current_user.id,
        created_at=datetime.now(timezone.utc)
    )

    session.add(message)
    session.commit()
    session.refresh(message)

    message_data = MessageRead.model_validate(message).model_dump(mode="json")

    await manager.broadcast_message(
        conversation_id,
        {
            "event": "message_created",
            "data": message_data
        }
    )


async def handle_update_message(data, conversation_id, current_user, session):
    ensure_conversation(conversation_id, current_user.id, session)

    message_id = data.get("message_id")
    new_text = data.get("message")

    existing = ensure_message(message_id, conversation_id, current_user.id, session)

    if existing.sender_id != current_user.id:
        await manager.broadcast_message(
            conversation_id,
            {
                "event": "error",
                "data": "You can only edit your own messages"
            }
        )
        return

    if existing.deleted_at:
        await manager.broadcast_message(
            conversation_id,
            {
                "event": "error",
                "data": "Cannot edit deleted message"
            }
        )
        return

    existing.message = new_text
    existing.edited_at = datetime.now(timezone.utc)
    existing.is_edited = True

    session.add(existing)
    session.commit()
    session.refresh(existing)

    message_data = MessageRead.model_validate(existing).model_dump(mode="json")

    await manager.broadcast_message(
        conversation_id,
        {
            "event": "message_updated",
            "data": message_data
        }
    )


async def handle_delete_message(data, conversation_id, current_user, session):
    ensure_conversation(conversation_id, current_user.id, session)

    message_id = data.get("message_id")

    existing = ensure_message(message_id, conversation_id, current_user.id, session)

    if existing.sender_id != current_user.id:
        await manager.broadcast_message(
            conversation_id,
            {
                "event": "error",
                "data": "You can only delete your own messages"
            }
        )
        return

    if existing.deleted_at:
        await manager.broadcast_message(
            conversation_id,
            {
                "event": "error",
                "data": "Message already deleted"
            }
        )
        return

    existing.deleted_at = datetime.now(timezone.utc)
    existing.is_edited = False

    session.add(existing)
    session.commit()

    await manager.broadcast_message(
        conversation_id,
        {
            "event": "message_deleted",
            "data": {
                "id": existing.id
            }
        }
    )