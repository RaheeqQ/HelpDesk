from fastapi import FastAPI
from app.controllers.users_controller import router as users_router
from app.controllers.auth_controller import router as auth_router  # login + register
from app.controllers.project_controller import router as projects_router
from app.controllers.project_members_controller import router as project_members_router
from app.controllers.sprint_controller import router as sprints_router
from app.controllers.ticket_controller import router as tickets_router
from app.controllers.comment_controller import router as comments_router

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