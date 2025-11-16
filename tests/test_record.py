#!/usr/bin/env python3
"""
Test script for MQTT record functionality.
Records MQTT events with optional filtering by topics or keywords.
"""

import asyncio
import json
import argparse
from datetime import datetime
from typing import List, Optional, Dict, Any
from aiomqtt import Client, Message


class MQTTRecorder:
    """Records MQTT events with filtering capabilities."""

    def __init__(
        self,
        broker: str,
        port: int,
        username: str,
        password: str,
        timeout: int,
        topics: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None
    ):
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.timeout = timeout
        self.topics = topics
        self.keywords = keywords

        self.events: List[Dict[str, Any]] = []
        self.start_time: Optional[datetime] = None
        self.unique_topics: set = set()

    def _matches_keywords(self, topic: str) -> bool:
        """Check if topic matches any of the keywords (OR logic)."""
        if not self.keywords:
            return True
        return any(keyword.lower() in topic.lower() for keyword in self.keywords)

    def _get_timestamp(self) -> float:
        """Get timestamp in seconds from start of recording."""
        if not self.start_time:
            return 0.0
        return (datetime.now() - self.start_time).total_seconds()

    def _record_event(self, message: Message) -> None:
        """Record a single MQTT event."""
        topic = str(message.topic)

        # Filter by keywords if using wildcard subscription
        if self.keywords and not self._matches_keywords(topic):
            return

        # Decode payload
        try:
            payload = message.payload.decode('utf-8')
        except (UnicodeDecodeError, AttributeError):
            payload = str(message.payload)

        # Record event
        event = {
            "timestamp": round(self._get_timestamp(), 3),
            "topic": topic,
            "payload": payload
        }
        self.events.append(event)
        self.unique_topics.add(topic)

    def _get_filter_info(self) -> Optional[Dict[str, Any]]:
        """Get filter information for output."""
        if self.topics:
            return {
                "type": "topics",
                "values": self.topics
            }
        elif self.keywords:
            return {
                "type": "keywords",
                "values": self.keywords
            }
        return None

    def _get_results(self) -> Dict[str, Any]:
        """Generate results JSON."""
        return {
            "duration": round(self._get_timestamp(), 3),
            "filter": self._get_filter_info(),
            "events": self.events,
            "unique_topics": sorted(list(self.unique_topics)),
            "total_events": len(self.events)
        }

    async def record(self) -> Dict[str, Any]:
        """Start recording MQTT events."""
        self.start_time = datetime.now()

        async with Client(
            hostname=self.broker,
            port=self.port,
            username=self.username,
            password=self.password
        ) as client:
            # Determine subscription strategy
            if self.topics:
                # Subscribe to specific topics
                for topic in self.topics:
                    await client.subscribe(topic)
                print(f"Subscribed to topics: {', '.join(self.topics)}")
            else:
                # Subscribe to everything
                await client.subscribe("#")
                if self.keywords:
                    print(f"Subscribed to all topics, filtering by keywords: {', '.join(self.keywords)}")
                else:
                    print("Subscribed to all topics")

            print(f"Recording for {self.timeout} seconds...")
            print("-" * 50)

            # Record events until timeout
            async def record_messages():
                async for message in client.messages:
                    self._record_event(message)
                    # Print real-time feedback
                    if len(self.events) % 10 == 0 and len(self.events) > 0:
                        print(f"Recorded {len(self.events)} events so far...")

            try:
                await asyncio.wait_for(record_messages(), timeout=self.timeout)
            except asyncio.TimeoutError:
                pass

            print("-" * 50)
            print(f"Recording completed. Total events: {len(self.events)}")

            return self._get_results()


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Record MQTT events with optional filtering"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Recording duration in seconds (default: 30)"
    )
    parser.add_argument(
        "--topics",
        type=str,
        nargs="+",
        help="Specific topics to subscribe to (space-separated)"
    )
    parser.add_argument(
        "--keywords",
        type=str,
        nargs="+",
        help="Keywords to filter topics (OR logic, space-separated)"
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

    # Create recorder
    recorder = MQTTRecorder(
        broker=args.broker,
        port=args.port,
        username=args.username,
        password=args.password,
        timeout=args.timeout,
        topics=args.topics,
        keywords=args.keywords
    )

    # Start recording
    try:
        results = await recorder.record()

        # Output results as formatted JSON
        print("\n" + "=" * 50)
        print("RESULTS:")
        print("=" * 50)
        print(json.dumps(results, indent=2, ensure_ascii=False))

    except KeyboardInterrupt:
        print("\n\nRecording interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
