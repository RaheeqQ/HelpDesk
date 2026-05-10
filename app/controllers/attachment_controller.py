from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from sqlmodel import Session, select
import cloudinary.uploader


from ..schemas.attachment_schema import AttachmentRead
from ..models.attachment import Attachment
from ..models.users import User
from ..db.database import get_session
from ..utils.response_wrapper import api_response
from ..utils.permission_helpers import (
    get_ticket_and_membership,
    ensure_can_write
)
from ..security.auth import get_current_user

router = APIRouter()


ALLOWED_TYPES = [
    "image/png",
    "image/jpeg",
    "application/pdf"
]

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


# get ticket attachments
@router.get("/tickets/{ticket_id}/attachments")
async def get_ticket_attachments(
    ticket_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    ticket, membership = get_ticket_and_membership(ticket_id, current_user.id, session)

    attachments = session.exec(
        select(Attachment)
        .where(Attachment.ticket_id == ticket.id)
    ).all()

    return api_response(
        data=[AttachmentRead.model_validate(a) for a in attachments],
        message="Attachments retrieved successfully"
    )


# upload attachment (user)
@router.post("/tickets/{ticket_id}/attachments")
async def upload_attachment(
    ticket_id: str,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    ticket, membership = get_ticket_and_membership(ticket_id, current_user.id,session)
    ensure_can_write(membership)

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    file_bytes = await file.read()
    file_size = len(file_bytes)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 5MB limit")
    
    resource_type = "image"

    if file.content_type == "application/pdf":
        resource_type = "raw"
    
    upload_result = cloudinary.uploader.upload(file_bytes, resource_type=resource_type)

    new_attachment = Attachment(
        ticket_id=ticket.id,
        uploader_id=current_user.id,
        filename=file.filename,
        file_url=upload_result["secure_url"],
        mime_type=file.content_type,
        file_size=file_size
    )

    session.add(new_attachment)
    session.commit()
    session.refresh(new_attachment)

    return api_response(
        data=AttachmentRead.model_validate(new_attachment),
        message="Attachment uploaded successfully"
    )


# update attachment (user)
@router.patch("/tickets/{ticket_id}/attachments/{attachment_id}")
async def update_attachment(
    ticket_id: str,
    attachment_id: str,
    filename: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    ticket, membership = get_ticket_and_membership(ticket_id, current_user.id, session)
    ensure_can_write(membership)

    db_attachment = session.get(Attachment, attachment_id)

    if not db_attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    if db_attachment.ticket_id != ticket.id:
        raise HTTPException(status_code=400, detail="Attachment does not belong to this ticket")

    if db_attachment.uploader_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    db_attachment.filename = filename

    session.add(db_attachment)
    session.commit()
    session.refresh(db_attachment)

    return api_response(
        data=AttachmentRead.model_validate(db_attachment),
        message="Attachment updated successfully"
    )


# delete attachment (user)
@router.delete("/tickets/{ticket_id}/attachments/{attachment_id}")
async def delete_attachment(
    ticket_id: str,
    attachment_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    ticket, membership = get_ticket_and_membership(ticket_id, current_user.id, session)
    ensure_can_write(membership)

    db_attachment = session.get(Attachment, attachment_id)

    if not db_attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    if db_attachment.ticket_id != ticket.id:
        raise HTTPException(status_code=400, detail="Attachment does not belong to this ticket")

    if db_attachment.uploader_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    session.delete(db_attachment)
    session.commit()

    return api_response(message="Attachment deleted successfully")