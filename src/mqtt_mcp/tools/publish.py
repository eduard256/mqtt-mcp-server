"""MQTT publishing tool."""

import json
import sys
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator

from ..mqtt_client import MQTTClient


class PublishMessage(BaseModel):
    """Single message to publish."""
    topic: str = Field(min_length=1, description="Topic to publish to")
    payload: Any = Field(description="Payload to publish")
    qos: int = Field(default=1, ge=0, le=2, description="Quality of Service level")
    retain: bool = Field(default=False, description="Retain message on broker")

    @validator('topic')
    def validate_topic(cls, v):
        """Ensure topic is not empty or whitespace."""
        if not v or not v.strip():
            raise ValueError("Topic cannot be empty or whitespace")
        return v


class PublishParams(BaseModel):
    """Parameters for publish tool."""
    messages: List[PublishMessage] = Field(min_items=1, description="Messages to publish")
    timeout: int = Field(default=3, ge=1, le=30, description="Network timeout in seconds")


async def publish(params: PublishParams) -> Dict[str, Any]:
    """
    Publish messages to MQTT topics.

    Args:
        params: Publishing parameters

    Returns:
        Dict with validation_errors, success, and errors
    """
    mqtt = MQTTClient()

    sys.stderr.write(f"Publishing {len(params.messages)} message(s)\n")

    # Phase 1: Validation (already done by Pydantic)
    # Additional validation for payload serializability
    validation_errors = []
    for i, msg in enumerate(params.messages):
        try:
            # Check if payload is serializable
            if isinstance(msg.payload, str):
                pass  # String is ok
            elif isinstance(msg.payload, bytes):
                pass  # Bytes is ok
            else:
                # Try to serialize as JSON
                json.dumps(msg.payload)
        except (TypeError, ValueError) as e:
            validation_errors.append({
                "index": i,
                "message": msg.dict(),
                "errors": [f"Payload is not serializable: {e}"]
            })

    # If any validation errors, don't publish anything
    if validation_errors:
        sys.stderr.write(f"Validation failed for {len(validation_errors)} message(s)\n")
        sys.stderr.write("No messages will be published due to validation errors\n")
        return {
            "validation_errors": validation_errors,
            "success": [],
            "errors": []
        }

    sys.stderr.write("All messages passed validation\n")

    # Phase 2: Publishing
    success = []
    errors = []

    for i, msg in enumerate(params.messages):
        sys.stderr.write(f"Publishing to topic '{msg.topic}'...\n")

        try:
            # Prepare payload
            if isinstance(msg.payload, str):
                payload_bytes = msg.payload.encode('utf-8')
            elif isinstance(msg.payload, bytes):
                payload_bytes = msg.payload
            else:
                # Convert to JSON
                payload_bytes = json.dumps(msg.payload, ensure_ascii=False).encode('utf-8')

            # Connect and publish
            async with await mqtt.create_client(timeout=params.timeout) as client:
                await client.publish(
                    topic=msg.topic,
                    payload=payload_bytes,
                    qos=msg.qos,
                    retain=msg.retain
                )

            sys.stderr.write(f"Successfully published to '{msg.topic}'\n")

            success.append({
                "index": i,
                "topic": msg.topic,
                "payload": msg.payload,
                "qos": msg.qos,
                "retain": msg.retain,
                "status": "published"
            })

        except Exception as e:
            error_msg = str(e)
            sys.stderr.write(f"Failed to publish to '{msg.topic}': {error_msg}\n")

            errors.append({
                "index": i,
                "topic": msg.topic,
                "payload": msg.payload,
                "error": error_msg,
                "status": "failed"
            })

    sys.stderr.write(f"Publishing complete: {len(success)} success, {len(errors)} failed\n")

    return {
        "validation_errors": [],
        "success": success,
        "errors": errors
    }