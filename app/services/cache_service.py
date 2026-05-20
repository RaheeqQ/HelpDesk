import json

from fastapi.encoders import jsonable_encoder

from app.cache import redis_client


async def get_cache(key: str):

    data = await redis_client.get(key)

    if data:
        return json.loads(data)

    return None


async def set_cache(
    key: str,
    value,
    expire: int = 300
):

    await redis_client.set(
        key,
        json.dumps(jsonable_encoder(value)),
        ex=expire
    )


async def delete_cache(key: str):

    await redis_client.delete(key)