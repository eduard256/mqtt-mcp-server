"""MQTT value reading tool."""

import asyncio
import json
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from ..mqtt_client import MQTTClient
from ..cache import save_cache, set_cached_value, get_cached_value


class ValueParams(BaseModel):
    """Parameters for value tool."""
    topics: List[str] = Field(min_items=1, description="Topic paths to read")
    timeout: int = Field(default=3, ge=1, le=60, description="Wait time for fresh data in seconds")


def get_request_topic_and_payload(topic: str) -> Optional[tuple[str, dict]]:
    """
    Generate request topic and payload for getting fresh data.
    Returns (request_topic, payload) or None if no request needed.
    """
    # Zigbee2MQTT devices
    if topic.startswith("zigbee2mqtt/") and not topic.startswith("zigbee2mqtt/bridge/"):
        return (f"{topic}/get", {"state": ""})

    # Tasmota devices
    if topic.startswith("tasmota/") or topic.startswith("cmnd/"):
        device = topic.split('/')[1] if '/' in topic else topic
        return (f"cmnd/{device}/STATUS", "")

    # ESPHome devices
    if topic.startswith("esphome/"):
        return (f"{topic}/command", "update")

    # No known request pattern
    return None


async def value(params: ValueParams) -> Dict[str, Any]:
    """
    Read current values from MQTT topics.

    Strategy:
    1. Send get/request commands for known systems (zigbee2mqtt, tasmota, etc)
    2. Subscribe and wait for fresh data (2-3 seconds)
    3. Fallback to cache if no fresh data received
    4. Return age of data in all cases

    Args:
        params: Value reading parameters

    Returns:
        Dict with successful reads and suggestions
    """
    mqtt = MQTTClient()
    success = []
    needs_interaction = []

    sys.stderr.write(f"Reading {len(params.topics)} topic(s)...\n")

    try:
        async with await mqtt.create_client(timeout=params.timeout) as client:
            # Step 1: Send request commands
            sys.stderr.write("Sending get/request commands...\n")
            for topic in params.topics:
                request = get_request_topic_and_payload(topic)
                if request:
                    request_topic, payload = request
                    try:
                        await client.publish(
                            request_topic,
                            payload=json.dumps(payload) if isinstance(payload, dict) else payload,
                            qos=1
                        )
                        sys.stderr.write(f"  Sent request to: {request_topic}\n")
                    except Exception as e:
                        sys.stderr.write(f"  Failed to send request to {request_topic}: {e}\n")

            # Step 2: Subscribe to topics
            sys.stderr.write("Subscribing to topics...\n")
            for topic in params.topics:
                await client.subscribe(topic)

            # Small delay for requests to be processed
            await asyncio.sleep(0.1)

            # Step 3: Collect fresh messages
            received_topics = {}

            async def collect_messages():
                async for message in client.messages:
                    topic = str(message.topic)

                    if topic in params.topics and topic not in received_topics:
                        try:
                            payload = message.payload.decode('utf-8')
                        except (UnicodeDecodeError, AttributeError):
                            payload = str(message.payload)

                        received_topics[topic] = {
                            'payload': payload,
                            'timestamp': datetime.utcnow()
                        }

                        sys.stderr.write(f"  Received fresh data: {topic}\n")

                        # Update cache
                        set_cached_value(topic, payload)

                        # Exit early if got all
                        if len(received_topics) == len(params.topics):
                            break

            # Wait for fresh data with timeout
            try:
                await asyncio.wait_for(collect_messages(), timeout=params.timeout)
            except asyncio.TimeoutError:
                sys.stderr.write(f"Timeout after {params.timeout}s\n")

        # Step 4: Process results (fresh + cache fallback)
        now = datetime.utcnow()

        for topic in params.topics:
            # Check if we got fresh data
            if topic in received_topics:
                payload = received_topics[topic]['payload']
                timestamp = received_topics[topic]['timestamp']
                age = (now - timestamp).total_seconds()

                # Parse JSON if possible
                try:
                    parsed = json.loads(payload) if isinstance(payload, str) else payload
                except json.JSONDecodeError:
                    parsed = payload

                success.append({
                    "topic": topic,
                    "value": parsed,
                    "source": "live",
                    "age_seconds": round(age, 1),
                    "timestamp": timestamp.isoformat() + 'Z'
                })
            else:
                # Try cache fallback
                cached = get_cached_value(topic)

                if cached:
                    cached_value, age = cached

                    # Parse JSON if possible
                    try:
                        parsed = json.loads(cached_value) if isinstance(cached_value, str) else cached_value
                    except json.JSONDecodeError:
                        parsed = cached_value

                    # Warn if data is old (>60 seconds)
                    if age > 60:
                        needs_interaction.append(topic)

                    success.append({
                        "topic": topic,
                        "value": parsed,
                        "source": "cache",
                        "age_seconds": round(age, 1),
                        "warning": "Data may be outdated" if age > 60 else None
                    })
                else:
                    # No data at all
                    needs_interaction.append(topic)
                    success.append({
                        "topic": topic,
                        "value": None,
                        "source": "none",
                        "age_seconds": None,
                        "warning": "No data available"
                    })

    except Exception as e:
        error_msg = f"Connection error: {str(e)}"
        sys.stderr.write(f"Error: {error_msg}\n")

        # Try cache for all topics
        for topic in params.topics:
            cached = get_cached_value(topic)
            if cached:
                cached_value, age = cached
                try:
                    parsed = json.loads(cached_value) if isinstance(cached_value, str) else cached_value
                except json.JSONDecodeError:
                    parsed = cached_value

                success.append({
                    "topic": topic,
                    "value": parsed,
                    "source": "cache",
                    "age_seconds": round(age, 1),
                    "warning": f"Connection failed, using cached data. {error_msg}"
                })
            else:
                success.append({
                    "topic": topic,
                    "value": None,
                    "source": "none",
                    "age_seconds": None,
                    "error": error_msg
                })

    # Save cache
    save_cache()

    sys.stderr.write(f"Completed: {len(success)} topics processed\n")

    # Build response
    response = {
        "values": success
    }

    # Add suggestion if some topics need interaction
    if needs_interaction:
        response["suggestion"] = (
            "To get current data for these devices, start MQTT event recording "
            "and ask the user to interact with the device."
        )
        response["topics_needing_interaction"] = needs_interaction

    return response
