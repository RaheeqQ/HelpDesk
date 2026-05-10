from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select
from datetime import datetime, timezone


from ..schemas.comment_schema import CreateComment, UpdateComment, CommentRead
from ..models.comments import Comment
from ..models.tickets import Ticket
from ..models.users import User
from ..models.project_members import ProjectMember, Role
from ..db.database import get_session
from ..utils.response_wrapper import api_response
from ..utils.comment_helpers import get_ticket_and_membership, ensure_can_comment
from ..security.auth import get_current_user

router = APIRouter()


# get ticket comments (user)
@router.get("/tickets/{ticket_id}/comments")
async def get_ticket_comments(
    ticket_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    ticket, membership = get_ticket_and_membership(ticket_id, current_user.id, session)

    comments = session.exec(
        select(Comment).where(Comment.ticket_id == ticket_id)
    ).all()

    return api_response(
        data=[CommentRead.model_validate(c) for c in comments],
        message="Comments retrieved successfully"
    )

# create comment (user)
@router.post("/tickets/{ticket_id}/comments")
async def create_comment(
    ticket_id: str,
    payload: CreateComment,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    ticket, membership = get_ticket_and_membership(ticket_id, current_user.id, session)
    ensure_can_comment(membership)

    new_comment = Comment(
        ticket_id=ticket_id,
        user_id=current_user.id,
        message=payload.message,
        created_at=datetime.now(timezone.utc)
    )

    session.add(new_comment)
    session.commit()
    session.refresh(new_comment)

    return api_response(
        data=CommentRead.model_validate(new_comment),
        message="Comment created successfully"
    )


# update comment (user)
@router.patch("/tickets/{ticket_id}/comments/{comment_id}")
async def update_comment(
    ticket_id: str,
    comment_id: str,
    payload: UpdateComment,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    ticket, membership = get_ticket_and_membership(ticket_id, current_user.id, session)
    ensure_can_comment(membership)

    db_comment = session.get(Comment, comment_id)

    if not db_comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if db_comment.ticket_id != ticket_id:
        raise HTTPException(status_code=400, detail="Comment does not belong to this ticket")

    if db_comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    if payload.message is not None:
        db_comment.message = payload.message

    db_comment.edited_at = datetime.now(timezone.utc)

    session.add(db_comment)
    session.commit()
    session.refresh(db_comment)

    return api_response(
        data=CommentRead.model_validate(db_comment),
        message="Comment updated successfully"
    )


# delete comment (user)
@router.delete("/tickets/{ticket_id}/comments/{comment_id}")
async def delete_comment(
    ticket_id: str,
    comment_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    ticket, membership = get_ticket_and_membership(ticket_id, current_user.id, session)
    ensure_can_comment(membership)

    db_comment = session.get(Comment, comment_id)

    if not db_comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if db_comment.ticket_id != ticket_id:
        raise HTTPException(status_code=400, detail="Comment does not belong to this ticket")

    if db_comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    session.delete(db_comment)
    session.commit()

    return api_response(message="Comment deleted successfully")