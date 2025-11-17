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

# Fields to ignore (noise that doesn't represent real events)
IGNORED_FIELDS = [
    "last_seen",
    "timestamp",
    "uptime",
    "triggers_count",
    "errors_count",
    "last_trigger",
    "power_outage_count",
    "trigger_count",
    "update",
    "identify",
    "effect",
    "power_on_behavior",
    "interlock",
    "power_outage_memory",
]


class RecordParams(BaseModel):
    """Parameters for record tool."""
    timeout: int = Field(default=30, ge=1, le=300, description="Recording duration in seconds")
    topics: Optional[List[str]] = Field(default=None, description="Specific topics to subscribe to")
    keywords: Optional[List[str]] = Field(default=None, description="Keywords to filter topics (OR logic)")


def should_ignore_topic(topic: str) -> bool:
    """Check if topic should be ignored."""
    return any(topic.startswith(prefix) for prefix in IGNORED_TOPIC_PREFIXES)


def clean_payload(payload: Any) -> Dict[str, Any]:
    """Remove ignored fields from payload."""
    if not isinstance(payload, dict):
        return {"value": payload}

    cleaned = {}
    for key, value in payload.items():
        if key not in IGNORED_FIELDS:
            cleaned[key] = value

    return cleaned


def get_device_name(topic: str) -> str:
    """Extract device name from topic."""
    # Remove common prefixes
    topic = topic.replace("zigbee2mqtt/", "")
    topic = topic.replace("automation/", "auto:")

    # Remove /set, /action, /get suffixes
    topic = topic.replace("/set", "")
    topic = topic.replace("/action", "")
    topic = topic.replace("/get", "")

    return topic


def get_changes(old_payload: Dict[str, Any], new_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Get only changed fields between old and new payload."""
    changes = {}

    all_keys = set(old_payload.keys()) | set(new_payload.keys())
    for key in all_keys:
        old_val = old_payload.get(key)
        new_val = new_payload.get(key)
        if old_val != new_val:
            changes[key] = new_val

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
        Dict with devices and their event timelines
    """
    mqtt = MQTTClient()
    devices: Dict[str, List[Dict[str, Any]]] = {}
    device_last_payload: Dict[str, Dict[str, Any]] = {}
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

                    # Apply keyword filter
                    if not params.topics and not matches_keywords(topic, params.keywords):
                        continue

                    # Decode payload
                    try:
                        payload = message.payload.decode('utf-8')
                        try:
                            payload = json.loads(payload)
                        except json.JSONDecodeError:
                            payload = {"value": payload}
                    except (UnicodeDecodeError, AttributeError):
                        payload = {"value": str(message.payload)}

                    # Clean payload
                    cleaned = clean_payload(payload)
                    if not cleaned:
                        continue

                    # Get device name
                    device_name = get_device_name(topic)

                    # Initialize device if first time
                    if device_name not in devices:
                        devices[device_name] = []
                        device_last_payload[device_name] = {}

                    # Get only changed fields
                    if device_last_payload[device_name]:
                        changes = get_changes(device_last_payload[device_name], cleaned)
                        if not changes:
                            continue
                    else:
                        changes = cleaned

                    # Record event with timestamp and changes
                    event = {"t": round(get_timestamp(), 3)}
                    event.update(changes)

                    devices[device_name].append(event)
                    device_last_payload[device_name] = cleaned

            # Record for specified duration
            try:
                await asyncio.wait_for(collect_events(), timeout=params.timeout)
            except asyncio.TimeoutError:
                pass

        # Count total events
        total_events = sum(len(events) for events in devices.values())

        sys.stderr.write(f"Recording complete: {total_events} events from {len(devices)} devices")
        if ignored_count > 0:
            sys.stderr.write(f" ({ignored_count} ignored)\n")
        else:
            sys.stderr.write("\n")

        return {
            "devices": devices
        }

    except Exception as e:
        error_msg = f"Recording failed: {str(e)}"
        sys.stderr.write(f"Error: {error_msg}\n")
        raise RuntimeError(error_msg)
