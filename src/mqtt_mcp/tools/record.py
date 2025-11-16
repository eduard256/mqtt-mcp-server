"""MQTT event recording tool."""

import asyncio
import json
import sys
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from ..mqtt_client import MQTTClient
from ..cache import update_cache


class RecordParams(BaseModel):
    """Parameters for record tool."""
    timeout: int = Field(default=30, ge=1, le=300, description="Recording duration in seconds")
    topics: Optional[List[str]] = Field(default=None, description="Specific topics to subscribe to")
    keywords: Optional[List[str]] = Field(default=None, description="Keywords to filter topics (OR logic)")


async def record(params: RecordParams) -> Dict[str, Any]:
    """
    Record MQTT events in real-time.

    Args:
        params: Recording parameters

    Returns:
        Dict with events, statistics, and filter info
    """
    mqtt = MQTTClient()
    events: List[Dict[str, Any]] = []
    unique_topics: set = set()
    topic_cache: Dict[str, str] = {}
    start_time = datetime.now()

    def get_timestamp() -> float:
        """Get seconds from start."""
        return (datetime.now() - start_time).total_seconds()

    def matches_keywords(topic: str) -> bool:
        """Check if topic matches any keyword (OR logic)."""
        if not params.keywords:
            return True
        return any(keyword.lower() in topic.lower() for keyword in params.keywords)

    try:
        async with await mqtt.create_client(timeout=params.timeout) as client:
            # Subscribe based on parameters
            if params.topics:
                # Subscribe to specific topics
                for topic in params.topics:
                    await client.subscribe(topic)
                sys.stderr.write(f"Recording from {len(params.topics)} specific topics\n")
            else:
                # Subscribe to everything
                await client.subscribe("#")
                if params.keywords:
                    sys.stderr.write(f"Recording all topics filtered by keywords: {', '.join(params.keywords)}\n")
                else:
                    sys.stderr.write("Recording all MQTT topics\n")

            # Record events
            async def collect_events():
                async for message in client.messages:
                    topic = str(message.topic)

                    # Apply keyword filter if using wildcard subscription
                    if not params.topics and params.keywords and not matches_keywords(topic):
                        continue

                    # Decode payload
                    try:
                        payload = message.payload.decode('utf-8')
                        # Try to parse as JSON
                        try:
                            payload = json.loads(payload)
                        except json.JSONDecodeError:
                            pass  # Keep as string
                    except (UnicodeDecodeError, AttributeError):
                        payload = str(message.payload)

                    # Determine if new or updated
                    change = "updated" if topic in unique_topics else "new"

                    # Record event
                    event = {
                        "timestamp": round(get_timestamp(), 3),
                        "topic": topic,
                        "payload": payload,
                        "change": change
                    }
                    events.append(event)
                    unique_topics.add(topic)
                    topic_cache[topic] = payload if isinstance(payload, str) else json.dumps(payload)

                    # Progress feedback
                    if len(events) % 100 == 0:
                        sys.stderr.write(f"Recorded {len(events)} events...\n")

            # Record for specified duration
            try:
                await asyncio.wait_for(collect_events(), timeout=params.timeout)
            except asyncio.TimeoutError:
                pass  # Normal timeout

        # Update global cache with discovered topics
        update_cache(topic_cache)

        # Build filter info
        filter_info = None
        if params.topics:
            filter_info = {
                "type": "topics",
                "values": params.topics
            }
        elif params.keywords:
            filter_info = {
                "type": "keywords",
                "values": params.keywords
            }

        # Calculate actual duration
        duration = round(get_timestamp(), 3)

        sys.stderr.write(f"Recording complete: {len(events)} events from {len(unique_topics)} topics\n")

        return {
            "duration": duration,
            "filter": filter_info,
            "events": events,
            "unique_topics": len(unique_topics),
            "total_events": len(events)
        }

    except Exception as e:
        error_msg = f"Recording failed: {str(e)}"
        sys.stderr.write(f"Error: {error_msg}\n")
        raise RuntimeError(error_msg)