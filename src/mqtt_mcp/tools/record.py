"""MQTT event recording tool."""

import asyncio
import json
import sys
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from ..mqtt_client import MQTTClient


# Topics to ignore (retained messages and config spam)
IGNORED_TOPIC_PREFIXES = [
    "zigbee2mqtt/bridge/",
    "homeassistant/",
]


class RecordParams(BaseModel):
    """Parameters for record tool."""
    timeout: int = Field(default=30, ge=1, le=300, description="Recording duration in seconds")
    topics: Optional[List[str]] = Field(default=None, description="Specific topics to subscribe to")
    keywords: Optional[List[str]] = Field(default=None, description="Keywords to filter topics (OR logic)")


def should_ignore_topic(topic: str) -> bool:
    """Check if topic should be ignored."""
    return any(topic.startswith(prefix) for prefix in IGNORED_TOPIC_PREFIXES)


def get_payload_diff(old_payload: Any, new_payload: Any) -> Dict[str, Any]:
    """Get difference between old and new payload."""
    changes = {}

    if isinstance(old_payload, dict) and isinstance(new_payload, dict):
        all_keys = set(old_payload.keys()) | set(new_payload.keys())
        for key in all_keys:
            old_val = old_payload.get(key)
            new_val = new_payload.get(key)
            if old_val != new_val:
                changes[key] = {"old": old_val, "new": new_val}
    else:
        if old_payload != new_payload:
            changes = {"old": old_payload, "new": new_payload}

    return changes


def matches_keywords(topic: str, keywords: Optional[List[str]]) -> bool:
    """Check if topic matches any keyword (OR logic)."""
    if not keywords:
        return True
    return any(keyword.lower() in topic.lower() for keyword in keywords)


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
    topic_last_payload: Dict[str, Any] = {}
    ignored_count = 0
    start_time = datetime.now()

    def get_timestamp() -> float:
        """Get seconds from start."""
        return (datetime.now() - start_time).total_seconds()

    try:
        async with await mqtt.create_client(timeout=params.timeout) as client:
            # Subscribe based on parameters
            if params.topics:
                for topic in params.topics:
                    await client.subscribe(topic)
                sys.stderr.write(f"Recording from {len(params.topics)} specific topics\n")
            else:
                await client.subscribe("#")
                if params.keywords:
                    sys.stderr.write(f"Recording all topics filtered by keywords: {', '.join(params.keywords)}\n")
                else:
                    sys.stderr.write("Recording all MQTT topics\n")

            # Record events
            async def collect_events():
                nonlocal ignored_count
                async for message in client.messages:
                    topic = str(message.topic)

                    # Filter out ignored topics
                    if should_ignore_topic(topic):
                        ignored_count += 1
                        continue

                    # Apply keyword filter if using wildcard subscription
                    if not params.topics and not matches_keywords(topic, params.keywords):
                        continue

                    # Decode payload
                    try:
                        payload = message.payload.decode('utf-8')
                        try:
                            payload = json.loads(payload)
                        except json.JSONDecodeError:
                            pass
                    except (UnicodeDecodeError, AttributeError):
                        payload = str(message.payload)

                    # Check if this is a new topic or an update
                    is_new = topic not in unique_topics

                    # Get changes
                    if is_new:
                        changes = payload
                        change_type = "new"
                    else:
                        old_payload = topic_last_payload.get(topic)
                        changes = get_payload_diff(old_payload, payload)
                        change_type = "updated"

                        # Skip if no changes
                        if not changes:
                            continue

                    # Record event with only changes
                    event = {
                        "timestamp": round(get_timestamp(), 3),
                        "topic": topic,
                        "changes": changes,
                        "change_type": change_type
                    }
                    events.append(event)
                    unique_topics.add(topic)
                    topic_last_payload[topic] = payload

                    # Progress feedback
                    if len(events) % 100 == 0:
                        sys.stderr.write(f"Recorded {len(events)} events...\n")

            # Record for specified duration
            try:
                await asyncio.wait_for(collect_events(), timeout=params.timeout)
            except asyncio.TimeoutError:
                pass

        # Calculate actual duration
        duration = round(get_timestamp(), 3)

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

        sys.stderr.write(f"Recording complete: {len(events)} events from {len(unique_topics)} topics")
        if ignored_count > 0:
            sys.stderr.write(f" ({ignored_count} ignored)\n")
        else:
            sys.stderr.write("\n")

        return {
            "duration": duration,
            "filter": filter_info,
            "events": events,
            "unique_topics": len(unique_topics),
            "total_events": len(events),
            "ignored_events": ignored_count
        }

    except Exception as e:
        error_msg = f"Recording failed: {str(e)}"
        sys.stderr.write(f"Error: {error_msg}\n")
        raise RuntimeError(error_msg)
