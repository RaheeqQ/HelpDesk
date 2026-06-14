"""
Background worker that consumes events from Redis and logs them to the database.
Run this as a separate process: python -m app.workers.activity_worker
"""

import json
import redis
import time
from sqlmodel import Session, create_engine
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=False)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

from app.models.activity_log import ActivityLog

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


def process_event(event_type: str, event_data: dict):
    session = Session(engine)
    
    try:
        if event_type == "ticket.status_changed":
            activity = ActivityLog(
                user_id=event_data.get("user_id"),
                project_id=event_data.get("project_id"),
                action=f"changed status {event_data.get('old_status')} → {event_data.get('new_status')}",
                entity_type="ticket",
                entity_id=event_data.get("ticket_id"),
                old_value=event_data.get("old_status"),
                new_value=event_data.get("new_status")
            )
            session.add(activity)
            session.commit()
            print(f"Logged: {event_data.get('old_status')} → {event_data.get('new_status')}")

        elif event_type == "ticket.priority_changed":
            activity = ActivityLog(
                user_id=event_data.get("user_id"),
                project_id=event_data.get("project_id"),
                action=f"changed priority {event_data.get('old_priority')} → {event_data.get('new_priority')}",
                entity_type="ticket",
                entity_id=event_data.get("ticket_id"),
                old_value=str(event_data.get("old_priority")),
                new_value=str(event_data.get("new_priority"))
            )
            session.add(activity)
            session.commit()
            print(f"Logged: Priority changed")

        elif event_type == "ticket.assigned":
            activity = ActivityLog(
                user_id=event_data.get("user_id"),
                project_id=event_data.get("project_id"),
                action="assigned ticket",
                entity_type="ticket",
                entity_id=event_data.get("ticket_id"),
                new_value=event_data.get("assignee_id")
            )
            session.add(activity)
            session.commit()
            print(f"Logged: Ticket assigned")

    except Exception as e:
        print(f"Error processing event: {e}")
    finally:
        session.close()


def start_worker():
    """
    Start the background worker that listens to Redis Streams.
    """
    print("Activity Worker started...")
    print(f"Connected to Redis: {REDIS_HOST}:{REDIS_PORT}")
    print("Listening to Redis stream 'events'...")
    
    last_id = "0"  # Start from the beginning
    
    while True:
        try:
            # Read from Redis stream with 5 second timeout
            events = redis_client.xread(
                {"events": last_id},
                block=5000,
                count=10
            )
            
            if events:
                for stream_name, message_list in events:
                    for message_id, message_data in message_list:
                        last_id = message_id
                        
                        event_type = message_data.get("type")
                        event_data = json.loads(message_data.get("data", "{}"))
                        
                        print(f"\n Received event: {event_type}")
                        process_event(event_type, event_data)
            
        except Exception as e:
            print(f"✗ Worker error: {e}")
            time.sleep(1)  # Wait before retrying


if __name__ == "__main__":
    start_worker()
