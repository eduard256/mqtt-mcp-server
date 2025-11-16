"""MQTT value reading tool."""

import asyncio
import json
import sys
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from ..mqtt_client import MQTTClient
from ..cache import load_cache, save_cache, get_cached_value, set_cached_value


class ValueParams(BaseModel):
    """Parameters for value tool."""
    topics: List[str] = Field(min_items=1, description="Topic paths to read")
    timeout: int = Field(default=5, ge=1, le=60, description="Wait time per topic in seconds")


async def value(params: ValueParams) -> Dict[str, Any]:
    """
    Read current values from specific MQTT topics.

    Args:
        params: Value reading parameters

    Returns:
        Dict with successful reads and errors
    """
    mqtt = MQTTClient()
    success = []
    errors = []

    # Load cache
    load_cache()

    sys.stderr.write(f"Reading {len(params.topics)} topic(s)\n")

    for topic in params.topics:
        # Check cache first
        cached = get_cached_value(topic)
        if cached:
            value, age = cached
            sys.stderr.write(f"Topic '{topic}' found in cache (age: {age:.1f}s)\n")

            # Parse value if JSON
            try:
                parsed_value = json.loads(value) if isinstance(value, str) else value
            except json.JSONDecodeError:
                parsed_value = value

            success.append({
                "topic": topic,
                "value": parsed_value,
                "source": "cache",
                "age_seconds": round(age, 2)
            })
        else:
            # Read live from MQTT
            sys.stderr.write(f"Reading topic '{topic}' from MQTT...\n")

            try:
                value = await read_topic_live(mqtt, topic, params.timeout)

                if value is not None:
                    sys.stderr.write(f"Got value for topic '{topic}'\n")

                    # Update cache
                    set_cached_value(topic, value if isinstance(value, str) else json.dumps(value))

                    # Parse value if JSON
                    try:
                        parsed_value = json.loads(value) if isinstance(value, str) else value
                    except json.JSONDecodeError:
                        parsed_value = value

                    success.append({
                        "topic": topic,
                        "value": parsed_value,
                        "source": "live",
                        "age_seconds": 0.0
                    })
                else:
                    sys.stderr.write(f"Timeout reading topic '{topic}'\n")

                    # Generate suggestion
                    suggestion = get_suggestion(topic)

                    errors.append({
                        "topic": topic,
                        "error": f"No message received within {params.timeout}s timeout",
                        "suggestion": suggestion
                    })

            except Exception as e:
                sys.stderr.write(f"Error reading topic '{topic}': {e}\n")
                errors.append({
                    "topic": topic,
                    "error": str(e),
                    "suggestion": "Check if the topic exists and is being published to"
                })

    # Save updated cache
    save_cache()

    sys.stderr.write(f"Read complete: {len(success)} success, {len(errors)} errors\n")

    return {
        "success": success,
        "errors": errors
    }


async def read_topic_live(mqtt: MQTTClient, topic: str, timeout: int) -> Optional[str]:
    """
    Read a single topic value live from MQTT.

    Args:
        mqtt: MQTT client instance
        topic: Topic to read
        timeout: Timeout in seconds

    Returns:
        Value string or None if timeout
    """
    try:
        async with await mqtt.create_client(timeout=timeout) as client:
            await client.subscribe(topic)

            # Wait for first message
            async def wait_for_message():
                async for message in client.messages:
                    if str(message.topic) == topic:
                        # Decode payload
                        try:
                            payload = message.payload.decode('utf-8')
                        except (UnicodeDecodeError, AttributeError):
                            payload = str(message.payload)
                        return payload

            try:
                return await asyncio.wait_for(wait_for_message(), timeout=timeout)
            except asyncio.TimeoutError:
                return None

    except Exception as e:
        sys.stderr.write(f"Error in read_topic_live: {e}\n")
        return None


def get_suggestion(topic: str) -> str:
    """Generate helpful suggestion for failed topic read."""
    if '/' in topic:
        parts = topic.split('/')
        base = '/'.join(parts[:2]) if len(parts) > 1 else parts[0]
        return f"Try discovering topics with keywords='{parts[0]}' or check if topic '{base}/#' exists"
    return f"Try discovering topics with keywords='{topic}'"