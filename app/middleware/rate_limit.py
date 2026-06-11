from fastapi import HTTPException, Request
import redis.asyncio as redis
import os

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    password=os.getenv("REDIS_PASSWORD"),
    db=0,
    decode_responses=True
)

async def rate_limit_middleware(request: Request, call_next):
    try:
        user_id = request.client.host if request.client else "unknown"
        key = f"user:{user_id}:requests"
        
        count = await redis_client.incr(key)
        if count == 1:
            await redis_client.expire(key, 60)
        
        if count > 5:
            raise HTTPException(status_code=429, detail="Too many requests")
    
    except HTTPException:
        raise
    except (redis.ConnectionError, Exception) as e:
        # if Redis is down, allow request (fail open)
        pass
    
    return await call_next(request)