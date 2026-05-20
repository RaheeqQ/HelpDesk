from fastapi import APIRouter
from ..cache import redis_client

router = APIRouter()

@router.get("/redis-test")
async def redis_test():

    await redis_client.set(
        "test",
        "redis working"
    )

    value = await redis_client.get("test")

    return {
        "message": value
    }