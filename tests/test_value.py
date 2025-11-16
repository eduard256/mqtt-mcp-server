#!/usr/bin/env python3
"""
Test script for MQTT value reading functionality.
Reads specific topic values with caching support.
"""

import asyncio
import json
import argparse
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from aiomqtt import Client, Message


# Cache file path
CACHE_FILE = Path(__file__).parent / "cache.json"


class ValueCache:
    """Manages topic value cache with timestamps."""

    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.load()

    def load(self) -> None:
        """Load cache from file."""
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                print(f"Loaded cache with {len(self.cache)} topics from {CACHE_FILE}")
            except Exception as e:
                print(f"Warning: Could not load cache: {e}")
                self.cache = {}
        else:
            print("No cache file found, starting fresh")

    def save(self) -> None:
        """Save cache to file."""
        try:
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
            print(f"Saved cache with {len(self.cache)} topics to {CACHE_FILE}")
        except Exception as e:
            print(f"Warning: Could not save cache: {e}")

    def get(self, topic: str) -> Optional[Dict[str, Any]]:
        """Get cached value for topic."""
        return self.cache.get(topic)

    def set(self, topic: str, value: str, timestamp: str = None) -> None:
        """Set cached value for topic."""
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat() + 'Z'

        self.cache[topic] = {
            "value": value,
            "timestamp": timestamp
        }

    def get_age_seconds(self, topic: str) -> float:
        """Calculate age of cached value in seconds."""
        cached = self.get(topic)
        if not cached:
            return 0.0

        try:
            cached_time = datetime.fromisoformat(cached["timestamp"].replace('Z', '+00:00'))
            now = datetime.utcnow()
            # Make both timezone-aware or both naive
            if cached_time.tzinfo is not None:
                from datetime import timezone
                now = now.replace(tzinfo=timezone.utc)
            age = (now - cached_time).total_seconds()
            return max(0.0, age)
        except Exception:
            return 0.0


class MQTTValueReader:
    """Reads values from specific MQTT topics with caching."""

    def __init__(
        self,
        broker: str,
        port: int,
        username: str,
        password: str,
        topics: List[str],
        timeout: int
    ):
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.topics = topics
        self.timeout = timeout
        self.cache = ValueCache()

    async def read_topic_live(self, topic: str) -> Optional[str]:
        """Read a topic value live from MQTT broker."""
        print(f"  Reading live: {topic}")

        try:
            async with Client(
                hostname=self.broker,
                port=self.port,
                username=self.username,
                password=self.password
            ) as client:
                await client.subscribe(topic)

                # Wait for first message with timeout
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
                    return await asyncio.wait_for(wait_for_message(), timeout=self.timeout)
                except asyncio.TimeoutError:
                    return None
        except Exception as e:
            print(f"  Error reading {topic}: {e}")
            return None

    def get_suggestion(self, topic: str) -> str:
        """Generate suggestion for failed topic read."""
        # Suggest trying discovery
        if '/' in topic:
            parts = topic.split('/')
            base = '/'.join(parts[:2]) if len(parts) > 1 else parts[0]
            return f"Try discovering topics with: --keywords {parts[0]} or check if topic '{base}/#' exists"
        return f"Try discovering topics with: --keywords {topic}"

    async def read_values(self) -> Dict[str, Any]:
        """Read values for all requested topics."""
        print(f"Reading {len(self.topics)} topic(s)...")
        print(f"Timeout per topic: {self.timeout}s")
        print("-" * 50)

        success = []
        errors = []

        for topic in self.topics:
            print(f"\n[{topic}]")

            # Check cache first
            cached = self.cache.get(topic)
            if cached:
                age = self.cache.get_age_seconds(topic)
                print(f"  Found in cache (age: {age:.1f}s)")

                success.append({
                    "topic": topic,
                    "value": cached["value"],
                    "source": "cache",
                    "age_seconds": round(age, 2)
                })
            else:
                # Read live
                value = await self.read_topic_live(topic)

                if value is not None:
                    print(f"  Got live value")

                    # Update cache
                    self.cache.set(topic, value)

                    success.append({
                        "topic": topic,
                        "value": value,
                        "source": "live",
                        "age_seconds": 0.0
                    })
                else:
                    print(f"  Timeout - no value received")
                    suggestion = self.get_suggestion(topic)

                    errors.append({
                        "topic": topic,
                        "error": f"No message received within {self.timeout}s timeout",
                        "suggestion": suggestion
                    })

        # Save updated cache
        print("\n" + "-" * 50)
        self.cache.save()

        return {
            "success": success,
            "errors": errors
        }


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Read values from specific MQTT topics"
    )
    parser.add_argument(
        "--topics",
        type=str,
        nargs="+",
        required=True,
        help="Topics to read values from (space-separated)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=5,
        help="Timeout in seconds for each topic (default: 5)"
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
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Clear cache before reading"
    )

    args = parser.parse_args()

    # Clear cache if requested
    if args.clear_cache:
        if CACHE_FILE.exists():
            CACHE_FILE.unlink()
            print("Cache cleared")
        print()

    # Create reader
    reader = MQTTValueReader(
        broker=args.broker,
        port=args.port,
        username=args.username,
        password=args.password,
        topics=args.topics,
        timeout=args.timeout
    )

    # Read values
    try:
        results = await reader.read_values()

        # Output results as formatted JSON
        print("\n" + "=" * 50)
        print("RESULTS:")
        print("=" * 50)
        print(json.dumps(results, indent=2, ensure_ascii=False))

        # Summary
        print("\n" + "=" * 50)
        print("SUMMARY:")
        print("=" * 50)
        print(f"Success: {len(results['success'])}/{len(args.topics)}")
        print(f"Errors: {len(results['errors'])}/{len(args.topics)}")

        if results['success']:
            cache_count = sum(1 for s in results['success'] if s['source'] == 'cache')
            live_count = sum(1 for s in results['success'] if s['source'] == 'live')
            print(f"  - From cache: {cache_count}")
            print(f"  - Live reads: {live_count}")

    except KeyboardInterrupt:
        print("\n\nRead interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
