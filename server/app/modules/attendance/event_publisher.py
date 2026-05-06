from app.core.security import redis_client  # async Redis
from typing import Dict
import json

async def publish_event(channel: str, event_data: Dict):
    await redis_client.publish(channel, json.dumps(event_data))