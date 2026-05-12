from fastapi import FastAPI
from app.controllers.users_controller import router as users_router
from app.controllers.auth_controller import router as auth_router  # login + register
from app.controllers.project_controller import router as projects_router
from app.controllers.project_members_controller import router as project_members_router
from app.controllers.sprint_controller import router as sprints_router
from app.controllers.ticket_controller import router as tickets_router
from app.controllers.comment_controller import router as comments_router
from app.controllers.attachment_controller import router as attachments_router
from app.controllers.conversation_controller import router as conversation_router
from app.controllers.message_controller import router as message_router
from app.websocket.chat_socket import router as websocket_router
from .utils import cloudinary_config

app = FastAPI()

app.include_router(
    auth_router, 
    prefix="/api/v1", 
    tags=["Auth"]
)

app.include_router(
    users_router,
    prefix="/api/v1",
    tags=["Users"]
)

app.include_router(
    projects_router, 
    prefix="/api/v1", 
    tags=["Projects"]
)

app.include_router(
    project_members_router,
    prefix="/api/v1",
    tags=["Project Members"]
)

app.include_router(
    sprints_router,
    prefix="/api/v1",
    tags=["Sprints"]
)

app.include_router(
    tickets_router,
    prefix="/api/v1",
    tags=["Tickets"]
)

app.include_router(
    comments_router,
    prefix="/api/v1",
    tags=["Comments"]
)

app.include_router(
    attachments_router,
    prefix="/api/v1",
    tags=["Attachments"]
)

app.include_router(
    conversation_router,
    prefix="/api/v1",
    tags=["Conversation"]
)

app.include_router(
    message_router,
    prefix="/api/v1",
    tags=["Message"]
)

app.include_router(
    websocket_router,
    prefix="/api/v1",
    tags=["Websocket"]
)