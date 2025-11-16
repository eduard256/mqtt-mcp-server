#!/usr/bin/env python3
"""
Test script for MQTT topics discovery functionality.
Discovers and filters MQTT topics with caching.
"""

import asyncio
import json
import argparse
from typing import List, Optional, Dict, Any
from aiomqtt import Client, Message


# Global cache for discovered topics
TOPICS_CACHE: Dict[str, str] = {}


class MQTTTopicsScanner:
    """Scans and discovers MQTT topics with filtering and pagination."""

    def __init__(
        self,
        broker: str,
        port: int,
        username: str,
        password: str,
        scan_timeout: int,
        keywords: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0
    ):
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.scan_timeout = scan_timeout
        self.keywords = keywords
        self.limit = limit
        self.offset = offset

        self.discovered_topics: Dict[str, str] = {}

    def _matches_keywords(self, topic: str) -> bool:
        """Check if topic matches any of the keywords (OR logic)."""
        if not self.keywords:
            return True
        return any(keyword.lower() in topic.lower() for keyword in self.keywords)

    def _record_topic(self, message: Message) -> None:
        """Record a discovered topic with its latest payload."""
        topic = str(message.topic)

        # Decode payload
        try:
            payload = message.payload.decode('utf-8')
        except (UnicodeDecodeError, AttributeError):
            payload = str(message.payload)

        # Store in discovered topics and global cache
        self.discovered_topics[topic] = payload
        TOPICS_CACHE[topic] = payload

    def _apply_filters_and_pagination(self) -> Dict[str, Any]:
        """Apply keyword filtering and pagination to discovered topics."""
        # Get all topics
        all_topics = sorted(self.discovered_topics.keys())

        # Filter by keywords
        if self.keywords:
            filtered_topics = [t for t in all_topics if self._matches_keywords(t)]
        else:
            filtered_topics = all_topics

        total = len(filtered_topics)

        # Apply pagination
        start_idx = self.offset
        end_idx = min(start_idx + self.limit, total)
        paginated_topics = filtered_topics[start_idx:end_idx]

        # Calculate has_more
        has_more = end_idx < total

        return {
            "topics": paginated_topics,
            "total": total,
            "showing": f"{start_idx}-{end_idx}",
            "has_more": has_more,
            "cache_size": len(TOPICS_CACHE)
        }

    async def scan(self) -> Dict[str, Any]:
        """Scan for MQTT topics."""
        print(f"Scanning for topics (timeout: {self.scan_timeout}s)...")
        if self.keywords:
            print(f"Keywords filter: {', '.join(self.keywords)}")
        print(f"Pagination: offset={self.offset}, limit={self.limit}")
        print("-" * 50)

        async with Client(
            hostname=self.broker,
            port=self.port,
            username=self.username,
            password=self.password
        ) as client:
            # Subscribe to all topics
            await client.subscribe("#")
            print("Subscribed to all topics (#)")
            print("Discovering topics...")

            # Collect topics until timeout
            async def collect_topics():
                async for message in client.messages:
                    self._record_topic(message)
                    # Print progress every 100 topics
                    if len(self.discovered_topics) % 100 == 0 and len(self.discovered_topics) > 0:
                        print(f"Discovered {len(self.discovered_topics)} unique topics so far...")

            try:
                await asyncio.wait_for(collect_topics(), timeout=self.scan_timeout)
            except asyncio.TimeoutError:
                pass

            print("-" * 50)
            print(f"Scan completed. Discovered {len(self.discovered_topics)} unique topics")
            print(f"Global cache contains {len(TOPICS_CACHE)} topics")

            return self._apply_filters_and_pagination()


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Discover and search MQTT topics"
    )
    parser.add_argument(
        "--scan-timeout",
        type=int,
        default=10,
        help="Topic discovery timeout in seconds (default: 10)"
    )
    parser.add_argument(
        "--keywords",
        type=str,
        nargs="+",
        help="Keywords to filter topics (OR logic, space-separated)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of results to return (default: 50)"
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Pagination offset (default: 0)"
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
        "--show-cache",
        action="store_true",
        help="Show current cache contents before scanning"
    )

    args = parser.parse_args()

    # Show cache if requested
    if args.show_cache and TOPICS_CACHE:
        print("=" * 50)
        print(f"CURRENT CACHE: {len(TOPICS_CACHE)} topics")
        print("=" * 50)
        for topic in sorted(TOPICS_CACHE.keys())[:10]:
            print(f"  - {topic}")
        if len(TOPICS_CACHE) > 10:
            print(f"  ... and {len(TOPICS_CACHE) - 10} more")
        print()

    # Create scanner
    scanner = MQTTTopicsScanner(
        broker=args.broker,
        port=args.port,
        username=args.username,
        password=args.password,
        scan_timeout=args.scan_timeout,
        keywords=args.keywords,
        limit=args.limit,
        offset=args.offset
    )

    # Start scanning
    try:
        results = await scanner.scan()

        # Output results as formatted JSON
        print("\n" + "=" * 50)
        print("RESULTS:")
        print("=" * 50)
        print(json.dumps(results, indent=2, ensure_ascii=False))

        # Show some example topics if any found
        if results["topics"]:
            print("\n" + "=" * 50)
            print(f"SAMPLE TOPICS (showing first 5 of {len(results['topics'])}):")
            print("=" * 50)
            for topic in results["topics"][:5]:
                payload = TOPICS_CACHE.get(topic, "")
                # Truncate long payloads
                if len(payload) > 100:
                    payload = payload[:100] + "..."
                print(f"\nTopic: {topic}")
                print(f"Payload: {payload}")

    except KeyboardInterrupt:
        print("\n\nScan interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
