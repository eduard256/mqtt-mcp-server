"""MQTT value reading tool."""

import asyncio
import json
import sys
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from ..mqtt_client import MQTTClient
from ..cache import save_cache, set_cached_value


class ValueParams(BaseModel):
    """Parameters for value tool."""
    topics: List[str] = Field(min_items=1, description="Topic paths to read")
    timeout: int = Field(default=5, ge=1, le=60, description="Wait time per topic in seconds")


async def value(params: ValueParams) -> Dict[str, Any]:
    """
    Read current FRESH values from specific MQTT topics.

    NOTE: Always reads live data for accuracy. Cache is updated but not used for results.

    Args:
        params: Value reading parameters

    Returns:
        Dict with successful reads and errors
    """
    mqtt = MQTTClient()
    success = []
    errors = []

    sys.stderr.write(f"Reading {len(params.topics)} topic(s) from MQTT (fresh data)...\n")

    try:
        # Open ONE connection for ALL topics
        async with await mqtt.create_client(timeout=params.timeout) as client:
            sys.stderr.write(f"Connected to broker, subscribing to {len(params.topics)} topic(s)...\n")

            # Subscribe to ALL requested topics
            for topic in params.topics:
                await client.subscribe(topic)

            # Track which topics we've received
            received_topics = set()
            topic_values = {}

            # Collect messages with overall timeout
            async def collect_values():
                async for message in client.messages:
                    topic = str(message.topic)

                    # Only process if it's one of our requested topics
                    if topic in params.topics and topic not in received_topics:
                        # Decode payload
                        try:
                            payload = message.payload.decode('utf-8')
                        except (UnicodeDecodeError, AttributeError):
                            payload = str(message.payload)

                        # Store value
                        topic_values[topic] = payload
                        received_topics.add(topic)

                        sys.stderr.write(f"[{len(received_topics)}/{len(params.topics)}] Received '{topic}'\n")

                        # Update cache for future use
                        set_cached_value(topic, payload)

                        # Got all topics? Exit early
                        if len(received_topics) == len(params.topics):
                            sys.stderr.write("All topics received, exiting early\n")
                            break

            # Wait for messages with timeout
            try:
                await asyncio.wait_for(collect_values(), timeout=params.timeout)
            except asyncio.TimeoutError:
                sys.stderr.write(f"Timeout after {params.timeout}s, got {len(received_topics)}/{len(params.topics)} topics\n")

        # Process received topics
        for topic in params.topics:
            if topic in topic_values:
                value = topic_values[topic]

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
                # Topic didn't respond within timeout
                suggestion = get_suggestion(topic)
                errors.append({
                    "topic": topic,
                    "error": f"No message received within {params.timeout}s timeout",
                    "suggestion": suggestion
                })

    except Exception as e:
        # Connection-level error
        error_msg = f"Connection error: {str(e)}"
        sys.stderr.write(f"Connection failed: {error_msg}\n")

        # All topics that weren't read go to errors
        for topic in params.topics:
            if topic not in [s["topic"] for s in success]:
                errors.append({
                    "topic": topic,
                    "error": error_msg,
                    "suggestion": "Check broker connection and credentials"
                })

    # Save updated cache
    save_cache()

    sys.stderr.write(f"Read complete: {len(success)} success, {len(errors)} errors\n")

    return {
        "success": success,
        "errors": errors
    }


def get_suggestion(topic: str) -> str:
    """Generate helpful suggestion for failed topic read."""
    if '/' in topic:
        parts = topic.split('/')
        base = '/'.join(parts[:2]) if len(parts) > 1 else parts[0]
        return f"Try discovering topics with keywords='{parts[0]}' or check if topic '{base}/#' exists"
    return f"Try discovering topics with keywords='{topic}'"