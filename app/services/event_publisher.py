import json
import redis
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

# Connect to Redis using .env configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        db=0,
        decode_responses=True
    )
    redis_client.ping()
    print(f"Redis connected: {REDIS_HOST}:{REDIS_PORT}")
except Exception as e:
    print(f"Redis connection failed: {e}")
    redis_client = None


def publish_event(event_type: str, payload: dict) -> bool:
    if not redis_client:
        print("Redis client not available")
        return False
    
    try:
        event_data = {
            "type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": json.dumps(payload)
        }
        
        redis_client.xadd("events", event_data)
        print(f"Event published: {event_type}")
        return True
    except Exception as e:
        print(f"Failed to publish event: {e}")
        return False
