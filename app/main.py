from fastapi import FastAPI
from app.controllers.users_controller import router as users_router
from app.controllers.auth_controller import router as auth_router  # login + register

app = FastAPI()

app.include_router(auth_router, prefix="/api/v1", tags=["Auth"])
app.include_router(
    users_router,
    prefix="/api/v1",
    tags=["Users"]
)
