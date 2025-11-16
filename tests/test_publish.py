#!/usr/bin/env python3
"""
Test script for MQTT publish functionality.
Publishes messages to MQTT topics with validation.
"""

import asyncio
import json
import argparse
from typing import List, Dict, Any, Optional
from aiomqtt import Client


class MessageValidator:
    """Validates MQTT messages before publishing."""

    @staticmethod
    def validate_message(msg: Dict[str, Any], index: int) -> Optional[Dict[str, Any]]:
        """
        Validate a single message.
        Returns error dict if invalid, None if valid.
        """
        errors = []

        # Validate topic
        if "topic" not in msg:
            errors.append("missing 'topic' field")
        elif not msg["topic"] or not isinstance(msg["topic"], str):
            errors.append("'topic' must be a non-empty string")
        elif not msg["topic"].strip():
            errors.append("'topic' cannot be empty or whitespace")

        # Validate payload
        if "payload" not in msg:
            errors.append("missing 'payload' field")
        else:
            # Check if payload is serializable
            try:
                if isinstance(msg["payload"], str):
                    # String payload is ok
                    pass
                elif isinstance(msg["payload"], (dict, list, int, float, bool, type(None))):
                    # JSON serializable types are ok
                    json.dumps(msg["payload"])
                else:
                    errors.append(f"'payload' type {type(msg['payload']).__name__} is not serializable")
            except (TypeError, ValueError) as e:
                errors.append(f"'payload' is not JSON serializable: {e}")

        # Validate QoS
        if "qos" in msg:
            qos = msg["qos"]
            if not isinstance(qos, int):
                errors.append(f"'qos' must be an integer, got {type(qos).__name__}")
            elif qos not in [0, 1, 2]:
                errors.append(f"'qos' must be 0, 1, or 2, got {qos}")

        # Validate retain
        if "retain" in msg:
            if not isinstance(msg["retain"], bool):
                errors.append(f"'retain' must be a boolean, got {type(msg['retain']).__name__}")

        if errors:
            return {
                "index": index,
                "message": msg,
                "errors": errors
            }

        return None

    @staticmethod
    def validate_all(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate all messages.
        Returns list of validation errors.
        """
        validation_errors = []

        for i, msg in enumerate(messages):
            error = MessageValidator.validate_message(msg, i)
            if error:
                validation_errors.append(error)

        return validation_errors


class MQTTPublisher:
    """Publishes messages to MQTT broker."""

    def __init__(
        self,
        broker: str,
        port: int,
        username: str,
        password: str,
        messages: List[Dict[str, Any]],
        timeout: int
    ):
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.messages = messages
        self.timeout = timeout

    def _prepare_payload(self, payload: Any) -> bytes:
        """Convert payload to bytes."""
        if isinstance(payload, str):
            return payload.encode('utf-8')
        elif isinstance(payload, bytes):
            return payload
        else:
            # Convert to JSON
            return json.dumps(payload, ensure_ascii=False).encode('utf-8')

    async def publish_message(self, msg: Dict[str, Any], index: int) -> Dict[str, Any]:
        """
        Publish a single message.
        Returns result dict with success status.
        """
        topic = msg["topic"]
        payload = msg["payload"]
        qos = msg.get("qos", 0)
        retain = msg.get("retain", False)

        try:
            # Prepare payload
            payload_bytes = self._prepare_payload(payload)

            # Connect and publish
            async with Client(
                hostname=self.broker,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=self.timeout
            ) as client:
                await client.publish(
                    topic=topic,
                    payload=payload_bytes,
                    qos=qos,
                    retain=retain
                )

            return {
                "index": index,
                "topic": topic,
                "payload": payload,
                "qos": qos,
                "retain": retain,
                "status": "published"
            }

        except Exception as e:
            return {
                "index": index,
                "topic": topic,
                "payload": payload,
                "error": str(e),
                "status": "failed"
            }

    async def publish_all(self) -> Dict[str, Any]:
        """
        Validate and publish all messages.
        Returns results dict.
        """
        print(f"Publishing {len(self.messages)} message(s)...")
        print(f"Broker: {self.broker}:{self.port}")
        print("-" * 50)

        # Phase 1: Validation
        print("\n[VALIDATION PHASE]")
        validation_errors = MessageValidator.validate_all(self.messages)

        if validation_errors:
            print(f"❌ Validation failed for {len(validation_errors)} message(s)")
            print("⚠️  No messages will be published due to validation errors")

            for err in validation_errors:
                print(f"\nMessage #{err['index']}:")
                for e in err['errors']:
                    print(f"  - {e}")

            return {
                "validation_errors": validation_errors,
                "success": [],
                "errors": []
            }

        print(f"✅ All {len(self.messages)} message(s) passed validation")

        # Phase 2: Publishing
        print("\n[PUBLISHING PHASE]")
        success = []
        errors = []

        for i, msg in enumerate(self.messages):
            print(f"\nMessage #{i}: {msg.get('topic', 'unknown')}")

            result = await self.publish_message(msg, i)

            if result["status"] == "published":
                print(f"  ✅ Published successfully")
                success.append(result)
            else:
                print(f"  ❌ Failed: {result.get('error', 'unknown error')}")
                errors.append(result)

        print("\n" + "-" * 50)
        print(f"Summary: {len(success)} success, {len(errors)} failed")

        return {
            "validation_errors": [],
            "success": success,
            "errors": errors
        }


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Publish messages to MQTT topics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Publish single message
  python test_publish.py --messages '[{"topic":"test/topic","payload":"hello"}]'

  # Publish JSON payload
  python test_publish.py --messages '[{"topic":"device/cmd","payload":{"state":"ON","brightness":100}}]'

  # Publish with QoS and retain
  python test_publish.py --messages '[{"topic":"status","payload":"online","qos":1,"retain":true}]'

  # Publish multiple messages
  python test_publish.py --messages '[
    {"topic":"light/set","payload":{"state":"ON"}},
    {"topic":"sensor/temp","payload":"23.5"}
  ]'
        """
    )
    parser.add_argument(
        "--messages",
        type=str,
        required=True,
        help="JSON array of messages to publish"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=3,
        help="Network timeout in seconds (default: 3)"
    )
    parser.add_argument(
        "--broker",
        type=str,
        default="10.0.20.104",
        help="MQTT broker host (default: 10.0.20.104)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=1883,
        help="MQTT broker port (default: 1883)"
    )
    parser.add_argument(
        "--username",
        type=str,
        default="mqtt",
        help="MQTT username (default: mqtt)"
    )
    parser.add_argument(
        "--password",
        type=str,
        default="mqtt",
        help="MQTT password (default: mqtt)"
    )

    args = parser.parse_args()

    # Parse messages JSON
    try:
        messages = json.loads(args.messages)
        if not isinstance(messages, list):
            print("Error: --messages must be a JSON array")
            return
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in --messages: {e}")
        return

    # Create publisher
    publisher = MQTTPublisher(
        broker=args.broker,
        port=args.port,
        username=args.username,
        password=args.password,
        messages=messages,
        timeout=args.timeout
    )

    # Publish messages
    try:
        results = await publisher.publish_all()

        # Output results as formatted JSON
        print("\n" + "=" * 50)
        print("RESULTS:")
        print("=" * 50)
        print(json.dumps(results, indent=2, ensure_ascii=False))

        # Exit code based on results
        if results["validation_errors"] or results["errors"]:
            exit(1)

    except KeyboardInterrupt:
        print("\n\nPublish interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
